#!/usr/bin/env python3
"""
Universal Intelligent Serialization Engine
Supports:
1. Automatic detection of object type and size
2. Small objects serialized directly, large objects return object_id
3. File-like objects return Resource URI
4. Configurable serialization strategy
"""

import json
import sys
import io
import uuid
import importlib
import threading
import time
from typing import Any, Dict, Optional, Tuple, List
from dataclasses import dataclass, asdict
from pathlib import Path
import inspect
from collections import OrderedDict


@dataclass
class SerializationResult:
    """Serialization result"""
    type: str  # 'direct', 'object_ref', 'resource'
    data: Any
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ObjectMetadata:
    """Metadata for stored objects"""
    object_id: str
    object_type: str
    size_estimate: int  # Estimated size (bytes)
    available_methods: List[Dict[str, Any]]
    preview: Optional[str] = None  # Serialization preview (first 100 chars)
    created_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            from datetime import datetime
            self.created_at = datetime.now().isoformat()


class SerializationConfig:
    """Serialization configuration"""
    
    def __init__(self, config_dict: Optional[Dict] = None):
        """
        Configuration parameters:
        - max_direct_size: Max bytes for direct serialization (default 10KB)
        - max_preview_length: Max length for preview text (default 200)
        - max_iterator_items: Max items to consume from iterator (default 1000)
        - enable_resources: Whether to enable Resource URI (default True)
        - resource_base_url: Base URL for Resource service
        - type_handlers: Custom type handlers
        """
        config = config_dict or {}
        
        self.max_direct_size = config.get('max_direct_size', 10 * 1024)  # 10KB
        self.max_preview_length = config.get('max_preview_length', 200)
        self.max_iterator_items = config.get('max_iterator_items', 1000)  # Max 1000 items
        self.enable_resources = config.get('enable_resources', True)
        self.resource_base_url = config.get('resource_base_url', 'mcp://resources')
        self.max_stored_objects = config.get('max_stored_objects', 10000)
        
        # Custom type handlers: type_pattern -> handler_function_name
        self.type_handlers = config.get('type_handlers', {})
        
        # File type detection patterns
        self.file_like_patterns = config.get('file_like_patterns', [
            'BufferedReader', 'BufferedWriter', 'TextIOWrapper',
            'BytesIO', 'StringIO', 'FileIO'
        ])
        
        # Data container patterns (need size check)
        self.data_container_patterns = config.get('data_container_patterns', [
            'DataFrame', 'Series', 'ndarray', 'Tensor',
            'Dataset', 'DataArray'
        ])
    
    @classmethod
    def from_file(cls, config_path: str):
        """Load configuration from JSON file"""
        with open(config_path, 'r', encoding='utf-8') as f:
            config_dict = json.load(f)
        return cls(config_dict)


class SmartSerializer:
    """Intelligent Serializer"""
    
    def __init__(self, config: Optional[SerializationConfig] = None):
        self.config = config or SerializationConfig()
        self._object_store: "OrderedDict[str, Any]" = OrderedDict()
        self.object_store = self._object_store
        self.metadata_store: Dict[str, ObjectMetadata] = {}
        self.resource_store: Dict[str, Any] = {}  # resource_id -> data
        self._ref_timestamps: Dict[str, float] = {}
        self._type_dispatch: Dict[type, Any] = {}
        self._dispatch_cache: Dict[type, Tuple[Optional[Any], bool]] = {}
        self._cleanup_interval = 300
        self._max_object_age = 3600
        self._cleanup_thread: Optional[threading.Thread] = None
        self._stop_cleanup = threading.Event()
        self._cleanup_started = False
        self._max_objects = max(1, int(self.config.max_stored_objects))
        self._lock = threading.Lock()
        self._id_lock = threading.Lock()
        self._id_counter = 0
        
        # Automatically load library-specific handlers
        self._load_library_handlers()
        self._build_type_dispatch()
        self._schedule_cleanup()
    
    def _load_library_handlers(self):
        """Dynamically load library-specific handlers"""
        try:
            from allbemcp.serialization.handlers import create_handler_registry
            
            # Create handler registry
            handler_registry = create_handler_registry({'library_specific': {}})
            
            # Register handlers into configuration
            for full_type_name, handler_func in handler_registry.items():
                # Create a wrapper method for each type
                method_name = f"_custom_handler_{full_type_name.replace('.', '_')}"
                
                # Dynamically bind handler method
                setattr(self, method_name, lambda obj, ctx, h=handler_func: h(obj, ctx))
                
                # Register type -> method name mapping in configuration
                self.config.type_handlers[full_type_name] = method_name
        except ImportError:
            # Handler module not available, skip
            pass

    def _build_type_dispatch(self):
        """Build type-dispatch table from configured type handlers."""
        self._type_dispatch = {}
        self._dispatch_cache.clear()
        for full_type_name, handler_name in (self.config.type_handlers or {}).items():
            if not hasattr(self, handler_name):
                continue
            try:
                module_name, class_name = full_type_name.rsplit('.', 1)
                module_obj = importlib.import_module(module_name)
                target_type = getattr(module_obj, class_name)
            except Exception:
                continue
            self._type_dispatch[target_type] = getattr(self, handler_name)

    def _resolve_dispatched_handler(self, obj_type: type):
        cached = self._dispatch_cache.get(obj_type)
        if cached is not None:
            return cached

        handler = self._type_dispatch.get(obj_type)
        if handler is not None:
            result = (handler, True)
            self._dispatch_cache[obj_type] = result
            return result

        for base in obj_type.__mro__[1:]:
            handler = self._type_dispatch.get(base)
            if handler is not None:
                result = (handler, True)
                self._dispatch_cache[obj_type] = result
                return result

        result = (None, False)
        self._dispatch_cache[obj_type] = result
        return result

    def _schedule_cleanup(self):
        if self._cleanup_interval <= 0 or self._cleanup_started:
            return

        self._cleanup_started = True

        def _worker():
            while not self._stop_cleanup.wait(self._cleanup_interval):
                try:
                    self.cleanup_objects(self._max_object_age)
                except Exception:
                    continue

        self._cleanup_thread = threading.Thread(
            target=_worker,
            daemon=True,
            name="allbemcp-serializer-cleanup",
        )
        self._cleanup_thread.start()

    def _auto_cleanup(self):
        self.cleanup_objects(self._max_object_age)

    def close(self):
        self._stop_cleanup.set()
        worker = self._cleanup_thread
        if worker is not None and worker.is_alive():
            worker.join(timeout=1.0)
        self._cleanup_thread = None
        self._cleanup_started = False

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass
    
    def serialize(self, obj: Any, context: Optional[Dict] = None) -> SerializationResult:
        """
        Intelligently serialize object
        
        Decision tree:
        1. None/Basic types -> Return directly
        2. Directly JSON serializable -> Try serialize, check size
        3. Generator/Iterator -> Consume and serialize content
        4. File-like object -> Resource URI
        5. Large data container -> Check size, decide direct serialization or object reference
        6. Other complex objects -> Object reference
        """
        context = context or {}
        
        # 1. None and basic types
        if obj is None or isinstance(obj, (bool, int, float, str)):
            return SerializationResult(type='direct', data=obj)
        
        # 2. Check custom type handlers via dispatch table
        handler, matched_custom_handler = self._resolve_dispatched_handler(type(obj))
        if matched_custom_handler and handler is not None:
            result = handler(obj, context)
            # Handler returns None means cannot handle, continue other processing flow
            if result is not None:
                return result
        
        # If a dedicated handler exists but chooses not to serialize directly
        # (typically due to configured size limits), fallback to object reference.
        if matched_custom_handler:
            return self._store_object(obj, preview=str(obj)[:self.config.max_preview_length])
        
        # 3. Generator and Iterator -> Consume and serialize content
        if self._is_iterator_or_generator(obj):
            return self._handle_iterator(obj, context)
        
        # 4. File-like object -> Resource
        if self._is_file_like(obj):
            return self._handle_file_like(obj, context)
        
        # 5. List and Tuple - Recursive serialization
        if isinstance(obj, (list, tuple)):
            return self._handle_sequence(obj, context)
        
        # 6. Dictionary
        if isinstance(obj, dict):
            return self._handle_dict(obj, context)
        
        # 7. Large data container - Check size
        if self._is_data_container(obj):
            return self._handle_data_container(obj, context)
        
        # 7. Try direct JSON serialization
        try:
            serialized = json.dumps(obj)
            size = len(serialized.encode('utf-8'))
            
            if size <= self.config.max_direct_size:
                # Small object, return directly
                return SerializationResult(
                    type='direct',
                    data=json.loads(serialized),  # Deserialize back to Python object
                    metadata={'size_bytes': size}
                )
            else:
                # Large object, store and return reference
                return self._store_object(obj, preview=serialized[:self.config.max_preview_length])
        except (TypeError, ValueError):
            # Cannot JSON serialize, store object
            return self._store_object(obj)
    
    def _is_file_like(self, obj: Any) -> bool:
        """Check if object is file-like"""
        type_name = type(obj).__name__
        
        # Check type name
        if any(pattern in type_name for pattern in self.config.file_like_patterns):
            return True
        
        # Check if has read/write methods
        return hasattr(obj, 'read') and (hasattr(obj, 'write') or hasattr(obj, 'seek'))
    
    def _is_data_container(self, obj: Any) -> bool:
        """Check if object is a data container"""
        type_name = type(obj).__name__
        return any(pattern in type_name for pattern in self.config.data_container_patterns)
    
    def _is_iterator_or_generator(self, obj: Any) -> bool:
        """Check if object is an iterator or generator"""
        import types
        import collections.abc
        
        # Check if generator
        if isinstance(obj, types.GeneratorType):
            return True
        
        # Check if iterator (but exclude string, bytes, list, tuple, dict, set, frozenset etc.)
        if isinstance(obj, (str, bytes, bytearray, list, tuple, dict, set, frozenset)):
            return False
        
        # Check if has __iter__ and __next__ methods (iterator protocol)
        return (hasattr(obj, '__iter__') and hasattr(obj, '__next__') and 
                callable(getattr(obj, '__iter__', None)) and 
                callable(getattr(obj, '__next__', None)))
    
    def _handle_iterator(self, obj: Any, context: Dict) -> SerializationResult:
        """Handle iterator and generator - consume them and serialize content"""
        max_items = context.get('max_iterator_items', self.config.max_direct_size // 100)  # Default max 100 items
        
        try:
            # Consume iterator, collect all items
            items = []
            total_size = 0
            is_truncated = False
            is_bytes_content = False
            
            for i, item in enumerate(obj):
                # Check if max items exceeded
                if i >= max_items:
                    is_truncated = True
                    break
                
                # Check if bytes content (e.g. iter_content returns)
                if isinstance(item, bytes):
                    is_bytes_content = True
                    items.append(item)
                    total_size += len(item)
                else:
                    items.append(item)
                    # Estimate size
                    try:
                        total_size += len(json.dumps(item).encode('utf-8'))
                    except:
                        total_size += 100  # Rough estimate
                
                # Check if total size exceeded
                if total_size > self.config.max_direct_size:
                    is_truncated = True
                    break
            
            # If bytes content (e.g. HTTP response body), combine into single bytes object
            if is_bytes_content:
                combined_bytes = b''.join(items)
                
                # Try decode as text
                try:
                    text_content = combined_bytes.decode('utf-8')
                    return SerializationResult(
                        type='direct',
                        data={
                            '_type': 'consumed_iterator',
                            'content_type': 'text',
                            'content': text_content,
                            'size_bytes': len(combined_bytes),
                            'is_truncated': is_truncated
                        },
                        metadata={
                            'original_type': f"{type(obj).__module__}.{type(obj).__name__}",
                            'note': 'Iterator consumed and content decoded as text'
                        }
                    )
                except UnicodeDecodeError:
                    # Cannot decode, return base64 encoded
                    import base64
                    encoded_content = base64.b64encode(combined_bytes).decode('ascii')
                    return SerializationResult(
                        type='direct',
                        data={
                            '_type': 'consumed_iterator',
                            'content_type': 'binary',
                            'content_base64': encoded_content,
                            'size_bytes': len(combined_bytes),
                            'is_truncated': is_truncated
                        },
                        metadata={
                            'original_type': f"{type(obj).__module__}.{type(obj).__name__}",
                            'note': 'Iterator consumed and content base64-encoded'
                        }
                    )
            
            # If not bytes content, recursively serialize each item
            serialized_items = []
            for item in items:
                result = self.serialize(item, context)
                serialized_items.append(result.data)
            
            return SerializationResult(
                type='direct',
                data={
                    '_type': 'consumed_iterator',
                    'content_type': 'list',
                    'items': serialized_items,
                    'item_count': len(serialized_items),
                    'is_truncated': is_truncated,
                    'size_bytes': total_size
                },
                metadata={
                    'original_type': f"{type(obj).__module__}.{type(obj).__name__}",
                    'note': f'Iterator consumed with {len(serialized_items)} items'
                }
            )
            
        except Exception as e:
            # Failed to consume iterator, store original object
            return self._store_object(
                obj, 
                preview=f"<Iterator/Generator: {type(obj).__name__}>",
                error=f"Failed to consume iterator: {str(e)}"
            )
    
    def _handle_file_like(self, obj: Any, context: Dict) -> SerializationResult:
        """Handle file-like object -> Resource URI"""
        if not self.config.enable_resources:
            # If resources disabled, store object
            return self._store_object(obj)
        
        # Generate resource_id
        resource_id = f"file_{uuid.uuid4().hex[:12]}"
        
        # Try read content
        content = None
        content_type = 'application/octet-stream'
        
        try:
            if hasattr(obj, 'read'):
                # Save current position
                current_pos = obj.tell() if hasattr(obj, 'tell') else None
                
                content = obj.read()
                
                # Restore position
                if current_pos is not None and hasattr(obj, 'seek'):
                    obj.seek(current_pos)
                
                # Determine content type
                if isinstance(content, str):
                    content_type = 'text/plain'
                elif isinstance(content, bytes):
                    # Try determine file type
                    if content.startswith(b'\x89PNG'):
                        content_type = 'image/png'
                    elif content.startswith(b'\xff\xd8\xff'):
                        content_type = 'image/jpeg'
                    elif content.startswith(b'%PDF'):
                        content_type = 'application/pdf'
        except Exception as e:
            # Read failed, store object itself
            return self._store_object(obj, error=str(e))
        
        # Store to resource store
        self.resource_store[resource_id] = {
            'content': content,
            'content_type': content_type,
            'original_object': obj
        }
        
        # Return Resource URI
        uri = f"{self.config.resource_base_url}/{resource_id}"
        
        return SerializationResult(
            type='resource',
            data={
                'uri': uri,
                'content_type': content_type,
                'size': len(content) if content else 0
            },
            metadata={
                'resource_id': resource_id,
                'note': 'File-like object stored as resource'
            }
        )
    
    def _handle_sequence(self, obj: Any, context: Dict) -> SerializationResult:
        """Handle list and tuple"""
        # Recursively serialize each item
        serialized_items = []
        has_complex = False
        
        for item in obj:
            result = self.serialize(item, context)
            serialized_items.append(result.data)
            
            if result.type != 'direct':
                has_complex = True

        try:
            total_json = json.dumps(serialized_items)
            total_size = len(total_json.encode('utf-8'))
        except Exception:
            return self._store_object(obj, preview=str(obj)[:self.config.max_preview_length])
        
        # If total size is too large or contains complex objects, consider storing
        if total_size > self.config.max_direct_size or (has_complex and len(obj) > 100):
            return self._store_object(obj, preview=str(obj)[:self.config.max_preview_length])
        
        return SerializationResult(
            type='direct',
            data=serialized_items,
            metadata={'size_bytes': total_size}
        )
    
    def _handle_dict(self, obj: Dict, context: Dict) -> SerializationResult:
        """Handle dictionary"""
        serialized_dict = {}
        has_complex = False
        
        for key, value in obj.items():
            # Key must be string
            str_key = str(key)
            
            result = self.serialize(value, context)
            serialized_dict[str_key] = result.data
            
            if result.type != 'direct':
                has_complex = True

        try:
            total_json = json.dumps(serialized_dict)
            total_size = len(total_json.encode('utf-8'))
        except Exception:
            return self._store_object(obj, preview=str(obj)[:self.config.max_preview_length])
        
        # Check total size
        if total_size > self.config.max_direct_size or (has_complex and len(obj) > 50):
            return self._store_object(obj, preview=str(obj)[:self.config.max_preview_length])
        
        return SerializationResult(
            type='direct',
            data=serialized_dict,
            metadata={'size_bytes': total_size}
        )
    
    def _handle_data_container(self, obj: Any, context: Dict) -> SerializationResult:
        """Handle data container (DataFrame, ndarray, etc.)"""
        type_name = type(obj).__name__
        
        # Keep this as a generic fallback for container-like objects not covered by
        # configuration-driven handlers.
        try:
            if hasattr(obj, 'to_dict') and callable(getattr(obj, 'to_dict')):
                try:
                    as_dict = obj.to_dict(orient='records')
                except TypeError:
                    as_dict = obj.to_dict()

                payload = {
                    '_type': f"{type(obj).__module__}.{type_name}",
                    'data': as_dict,
                }
                serialized = json.dumps(payload)
                size = len(serialized.encode('utf-8'))
                if size <= self.config.max_direct_size:
                    return SerializationResult(type='direct', data=payload, metadata={'size_bytes': size})

            return self._store_object(obj, preview=f"{type_name}({str(obj)[:80]})")
                
        except Exception as e:
            # Conversion failed, store object
            return self._store_object(obj, error=str(e))
    
    def _store_object(self, obj: Any, preview: Optional[str] = None, error: Optional[str] = None) -> SerializationResult:
        """Store object and return reference"""
        object_id = self._generate_object_id()
        
        # Get type info
        obj_type = type(obj)
        type_name = f"{obj_type.__module__}.{obj_type.__name__}"
        
        # Estimate size
        size_estimate = 0
        try:
            size_estimate = sys.getsizeof(obj)
        except:
            pass
        
        # Extract available methods
        available_methods = self._extract_methods(obj)
        
        # Generate preview
        if preview is None:
            try:
                preview = str(obj)[:self.config.max_preview_length]
            except:
                preview = f"<{type_name} object>"
        
        # Create metadata
        metadata = ObjectMetadata(
            object_id=object_id,
            object_type=type_name,
            size_estimate=size_estimate,
            available_methods=available_methods,
            preview=preview
        )
        
        # Store
        with self._lock:
            if len(self._object_store) >= self._max_objects:
                oldest_id, _ = self._object_store.popitem(last=False)
                self.metadata_store.pop(oldest_id, None)
                self._ref_timestamps.pop(oldest_id, None)

            self._object_store[object_id] = obj
            self.metadata_store[object_id] = metadata
            self._ref_timestamps[object_id] = time.time()
        
        # Return result
        result_data = {
            'object_id': object_id,
            'object_type': type_name,
            'available_methods': available_methods,
            'preview': preview,
            'note': 'Object stored. Use call-object-method to invoke methods.'
        }
        
        if error:
            result_data['serialization_error'] = error
        
        return SerializationResult(
            type='object_ref',
            data=result_data,
            metadata=asdict(metadata)
        )

    def _generate_object_id(self) -> str:
        with self._id_lock:
            self._id_counter += 1
            return f"obj_{self._id_counter:016x}"
    
    def _extract_methods(self, obj: Any) -> List[Dict[str, Any]]:
        """Extract available methods of object"""
        available_methods = []
        
        for name in dir(obj):
            if name.startswith('_'):
                continue
            
            try:
                attr = getattr(obj, name)
                if callable(attr):
                    # Extract parameter info
                    try:
                        sig = inspect.signature(attr)
                        params = [
                            {
                                'name': pname,
                                'required': param.default == inspect.Parameter.empty,
                                'default': str(param.default) if param.default != inspect.Parameter.empty else None
                            }
                            for pname, param in sig.parameters.items()
                            if pname not in ('self', 'cls')
                        ]
                        available_methods.append({
                            'name': name,
                            'params': params
                        })
                    except (ValueError, TypeError):
                        # Cannot get signature, only add method name
                        available_methods.append({
                            'name': name,
                            'params': []
                        })
            except:
                continue
        
        return available_methods
    
    def get_object(self, object_id: str) -> Optional[Any]:
        """Get stored object"""
        with self._lock:
            obj = self._object_store.get(object_id)
            if obj is not None:
                self._object_store.move_to_end(object_id)
                self._ref_timestamps[object_id] = time.time()
            return obj
    
    def get_metadata(self, object_id: str) -> Optional[ObjectMetadata]:
        """Get object metadata"""
        return self.metadata_store.get(object_id)
    
    def get_resource(self, resource_id: str) -> Optional[Dict]:
        """Get Resource data"""
        return self.resource_store.get(resource_id)
    
    def cleanup_objects(self, max_age_seconds: int = 3600):
        """Cleanup old objects"""
        now = time.time()
        to_remove = []

        with self._lock:
            for object_id, ts in list(self._ref_timestamps.items()):
                if now - ts > max_age_seconds:
                    to_remove.append(object_id)
        
            for object_id in to_remove:
                self._object_store.pop(object_id, None)
                self.metadata_store.pop(object_id, None)
                self._ref_timestamps.pop(object_id, None)
        
        return len(to_remove)


# Global serializer instance (can be used in MCP server)
_global_serializer: Optional[SmartSerializer] = None


def get_serializer(config: Optional[SerializationConfig] = None) -> SmartSerializer:
    """Get global serializer instance"""
    global _global_serializer
    
    if _global_serializer is None:
        _global_serializer = SmartSerializer(config)
    
    return _global_serializer


def reset_serializer():
    """Reset global serializer"""
    global _global_serializer
    _global_serializer = None

