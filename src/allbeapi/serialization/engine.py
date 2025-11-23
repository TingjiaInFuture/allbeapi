#!/usr/bin/env python3
"""
通用智能序列化引擎
支持：
1. 自动检测对象类型和大小
2. 小对象直接序列化，大对象返回object_id
3. 文件类对象返回Resource URI
4. 可配置的序列化策略
"""

import json
import sys
import io
import uuid
from typing import Any, Dict, Optional, Tuple, List
from dataclasses import dataclass, asdict
from pathlib import Path
import inspect


@dataclass
class SerializationResult:
    """序列化结果"""
    type: str  # 'direct', 'object_ref', 'resource'
    data: Any
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ObjectMetadata:
    """存储对象的元数据"""
    object_id: str
    object_type: str
    size_estimate: int  # 估算大小(字节)
    available_methods: List[Dict[str, Any]]
    preview: Optional[str] = None  # 序列化预览(前100字符)
    created_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            from datetime import datetime
            self.created_at = datetime.now().isoformat()


class SerializationConfig:
    """序列化配置"""
    
    def __init__(self, config_dict: Optional[Dict] = None):
        """
        配置参数：
        - max_direct_size: 直接序列化的最大字节数(默认10KB)
        - max_preview_length: 预览文本最大长度(默认200)
        - max_iterator_items: 迭代器最大消费项数(默认1000)
        - enable_resources: 是否启用Resource URI(默认True)
        - resource_base_url: Resource服务的基础URL
        - type_handlers: 自定义类型处理器
        """
        config = config_dict or {}
        
        self.max_direct_size = config.get('max_direct_size', 10 * 1024)  # 10KB
        self.max_preview_length = config.get('max_preview_length', 200)
        self.max_iterator_items = config.get('max_iterator_items', 1000)  # 最多消费1000项
        self.enable_resources = config.get('enable_resources', True)
        self.resource_base_url = config.get('resource_base_url', 'mcp://resources')
        
        # 自定义类型处理器: type_pattern -> handler_function_name
        self.type_handlers = config.get('type_handlers', {})
        
        # 文件类型检测模式
        self.file_like_patterns = config.get('file_like_patterns', [
            'BufferedReader', 'BufferedWriter', 'TextIOWrapper',
            'BytesIO', 'StringIO', 'FileIO'
        ])
        
        # 数据容器类型(需要检查大小)
        self.data_container_patterns = config.get('data_container_patterns', [
            'DataFrame', 'Series', 'ndarray', 'Tensor',
            'Dataset', 'DataArray'
        ])
    
    @classmethod
    def from_file(cls, config_path: str):
        """从JSON文件加载配置"""
        with open(config_path, 'r', encoding='utf-8') as f:
            config_dict = json.load(f)
        return cls(config_dict)


class SmartSerializer:
    """智能序列化器"""
    
    def __init__(self, config: Optional[SerializationConfig] = None):
        self.config = config or SerializationConfig()
        self.object_store: Dict[str, Any] = {}
        self.metadata_store: Dict[str, ObjectMetadata] = {}
        self.resource_store: Dict[str, Any] = {}  # resource_id -> data
        
        # 自动加载库特定处理器
        self._load_library_handlers()
    
    def _load_library_handlers(self):
        """动态加载库特定处理器"""
        try:
            from allbeapi.serialization.handlers import create_handler_registry
            
            # 创建处理器注册表
            handler_registry = create_handler_registry({'library_specific': {}})
            
            # 注册处理器到配置中
            for full_type_name, handler_func in handler_registry.items():
                # 为每个类型创建一个包装方法
                method_name = f"_custom_handler_{full_type_name.replace('.', '_')}"
                
                # 动态绑定处理器方法
                setattr(self, method_name, lambda obj, ctx, h=handler_func: h(obj, ctx))
                
                # 在配置中注册类型 -> 方法名映射
                self.config.type_handlers[full_type_name] = method_name
        except ImportError:
            # 处理器模块不可用，跳过
            pass
    
    def serialize(self, obj: Any, context: Optional[Dict] = None) -> SerializationResult:
        """
        智能序列化对象
        
        决策树：
        1. None/基本类型 -> 直接返回
        2. 可直接JSON序列化 -> 尝试序列化，检查大小
        3. 生成器/迭代器 -> 消费并序列化内容
        4. 文件类对象 -> Resource URI
        5. 大型数据容器 -> 检查大小，决定直接序列化还是对象引用
        6. 其他复杂对象 -> 对象引用
        """
        context = context or {}
        
        # 1. None 和基本类型
        if obj is None or isinstance(obj, (bool, int, float, str)):
            return SerializationResult(type='direct', data=obj)
        
        # 2. 检查自定义类型处理器
        type_name = type(obj).__name__
        full_type_name = f"{type(obj).__module__}.{type_name}"
        
        if full_type_name in self.config.type_handlers:
            handler_name = self.config.type_handlers[full_type_name]
            if hasattr(self, handler_name):
                result = getattr(self, handler_name)(obj, context)
                # 处理器返回None表示无法处理，继续其他处理流程
                if result is not None:
                    return result
        
        # 3. 生成器和迭代器 -> 消费并序列化内容
        if self._is_iterator_or_generator(obj):
            return self._handle_iterator(obj, context)
        
        # 4. 文件类对象 -> Resource
        if self._is_file_like(obj):
            return self._handle_file_like(obj, context)
        
        # 5. 列表和元组 - 递归序列化
        if isinstance(obj, (list, tuple)):
            return self._handle_sequence(obj, context)
        
        # 6. 字典
        if isinstance(obj, dict):
            return self._handle_dict(obj, context)
        
        # 7. 大型数据容器 - 检查大小
        if self._is_data_container(obj):
            return self._handle_data_container(obj, context)
        
        # 7. 尝试直接JSON序列化
        try:
            serialized = json.dumps(obj)
            size = len(serialized.encode('utf-8'))
            
            if size <= self.config.max_direct_size:
                # 小对象，直接返回
                return SerializationResult(
                    type='direct',
                    data=json.loads(serialized),  # 反序列化回Python对象
                    metadata={'size_bytes': size}
                )
            else:
                # 大对象，存储并返回引用
                return self._store_object(obj, preview=serialized[:self.config.max_preview_length])
        except (TypeError, ValueError):
            # 无法JSON序列化，存储对象
            return self._store_object(obj)
    
    def _is_file_like(self, obj: Any) -> bool:
        """判断是否是文件类对象"""
        type_name = type(obj).__name__
        
        # 检查类型名称
        if any(pattern in type_name for pattern in self.config.file_like_patterns):
            return True
        
        # 检查是否有read/write方法
        return hasattr(obj, 'read') and (hasattr(obj, 'write') or hasattr(obj, 'seek'))
    
    def _is_data_container(self, obj: Any) -> bool:
        """判断是否是数据容器"""
        type_name = type(obj).__name__
        return any(pattern in type_name for pattern in self.config.data_container_patterns)
    
    def _is_iterator_or_generator(self, obj: Any) -> bool:
        """判断是否是迭代器或生成器"""
        import types
        import collections.abc
        
        # 检查是否是生成器
        if isinstance(obj, types.GeneratorType):
            return True
        
        # 检查是否是迭代器（但排除字符串、字节、列表、元组、字典等已处理的类型）
        if isinstance(obj, (str, bytes, bytearray, list, tuple, dict, set, frozenset)):
            return False
        
        # 检查是否有 __iter__ 和 __next__ 方法（迭代器协议）
        return (hasattr(obj, '__iter__') and hasattr(obj, '__next__') and 
                callable(getattr(obj, '__iter__', None)) and 
                callable(getattr(obj, '__next__', None)))
    
    def _handle_iterator(self, obj: Any, context: Dict) -> SerializationResult:
        """处理迭代器和生成器 - 消费它们并序列化内容"""
        max_items = context.get('max_iterator_items', self.config.max_direct_size // 100)  # 默认最多100项
        
        try:
            # 消费迭代器，收集所有元素
            items = []
            total_size = 0
            is_truncated = False
            is_bytes_content = False
            
            for i, item in enumerate(obj):
                # 检查是否超过最大项数
                if i >= max_items:
                    is_truncated = True
                    break
                
                # 检查是否是字节内容（如 iter_content 返回的）
                if isinstance(item, bytes):
                    is_bytes_content = True
                    items.append(item)
                    total_size += len(item)
                else:
                    items.append(item)
                    # 估算大小
                    try:
                        total_size += len(json.dumps(item).encode('utf-8'))
                    except:
                        total_size += 100  # 粗略估计
                
                # 检查总大小是否超限
                if total_size > self.config.max_direct_size:
                    is_truncated = True
                    break
            
            # 如果是字节内容（如 HTTP 响应体），合并为单个字节对象
            if is_bytes_content:
                combined_bytes = b''.join(items)
                
                # 尝试解码为文本
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
                    # 无法解码，返回 base64 编码
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
            
            # 如果不是字节内容，递归序列化每个项
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
            # 消费迭代器失败，存储原始对象
            return self._store_object(
                obj, 
                preview=f"<Iterator/Generator: {type(obj).__name__}>",
                error=f"Failed to consume iterator: {str(e)}"
            )
    
    def _handle_file_like(self, obj: Any, context: Dict) -> SerializationResult:
        """处理文件类对象 -> Resource URI"""
        if not self.config.enable_resources:
            # 如果禁用Resource，则存储对象
            return self._store_object(obj)
        
        # 生成resource_id
        resource_id = f"file_{uuid.uuid4().hex[:12]}"
        
        # 尝试读取内容
        content = None
        content_type = 'application/octet-stream'
        
        try:
            if hasattr(obj, 'read'):
                # 保存当前位置
                current_pos = obj.tell() if hasattr(obj, 'tell') else None
                
                content = obj.read()
                
                # 恢复位置
                if current_pos is not None and hasattr(obj, 'seek'):
                    obj.seek(current_pos)
                
                # 判断内容类型
                if isinstance(content, str):
                    content_type = 'text/plain'
                elif isinstance(content, bytes):
                    # 尝试判断文件类型
                    if content.startswith(b'\x89PNG'):
                        content_type = 'image/png'
                    elif content.startswith(b'\xff\xd8\xff'):
                        content_type = 'image/jpeg'
                    elif content.startswith(b'%PDF'):
                        content_type = 'application/pdf'
        except Exception as e:
            # 读取失败，存储对象本身
            return self._store_object(obj, error=str(e))
        
        # 存储到resource store
        self.resource_store[resource_id] = {
            'content': content,
            'content_type': content_type,
            'original_object': obj
        }
        
        # 返回Resource URI
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
        """处理列表和元组"""
        # 递归序列化每个元素
        serialized_items = []
        total_size = 0
        has_complex = False
        
        for item in obj:
            result = self.serialize(item, context)
            serialized_items.append(result.data)
            
            if result.type != 'direct':
                has_complex = True
            
            # 估算大小
            try:
                item_size = len(json.dumps(result.data).encode('utf-8'))
                total_size += item_size
            except:
                has_complex = True
        
        # 如果总大小过大或包含复杂对象，考虑存储
        if total_size > self.config.max_direct_size or (has_complex and len(obj) > 100):
            return self._store_object(obj, preview=str(obj)[:self.config.max_preview_length])
        
        return SerializationResult(
            type='direct',
            data=serialized_items,
            metadata={'size_bytes': total_size}
        )
    
    def _handle_dict(self, obj: Dict, context: Dict) -> SerializationResult:
        """处理字典"""
        serialized_dict = {}
        total_size = 0
        has_complex = False
        
        for key, value in obj.items():
            # 键必须是字符串
            str_key = str(key)
            
            result = self.serialize(value, context)
            serialized_dict[str_key] = result.data
            
            if result.type != 'direct':
                has_complex = True
            
            try:
                item_size = len(json.dumps({str_key: result.data}).encode('utf-8'))
                total_size += item_size
            except:
                has_complex = True
        
        # 检查总大小
        if total_size > self.config.max_direct_size or (has_complex and len(obj) > 50):
            return self._store_object(obj, preview=str(obj)[:self.config.max_preview_length])
        
        return SerializationResult(
            type='direct',
            data=serialized_dict,
            metadata={'size_bytes': total_size}
        )
    
    def _handle_data_container(self, obj: Any, context: Dict) -> SerializationResult:
        """处理数据容器(DataFrame, ndarray等)"""
        type_name = type(obj).__name__
        
        # 尝试转换为简单格式
        try:
            # pandas DataFrame/Series
            if type_name == 'DataFrame':
                # 检查大小
                num_rows, num_cols = obj.shape
                estimated_size = num_rows * num_cols * 8  # 粗略估计
                
                if estimated_size <= self.config.max_direct_size:
                    # Handle MultiIndex columns which cause JSON serialization errors
                    # because to_dict(orient='records') produces dicts with tuple keys
                    export_df = obj
                    columns_list = obj.columns.tolist()
                    
                    # Check if columns are MultiIndex (list of tuples)
                    if len(columns_list) > 0 and isinstance(columns_list[0], tuple):
                        # Create a copy to avoid modifying the original
                        export_df = obj.copy()
                        # Flatten columns to strings: "('A', 'B')" -> "('A', 'B')"
                        export_df.columns = [str(col) for col in export_df.columns]


                    # 小数据，直接序列化
                    return SerializationResult(
                        type='direct',
                        data={
                            '_type': 'pandas.DataFrame',
                            'columns': columns_list,
                            'data': export_df.to_dict(orient='records'),
                            'shape': [num_rows, num_cols]
                        },
                        metadata={'size_estimate': estimated_size}
                    )
                else:
                    # 大数据，存储对象
                    preview = f"DataFrame(shape={obj.shape}, columns={obj.columns.tolist()[:5]}...)"
                    return self._store_object(obj, preview=preview)
            
            elif type_name == 'Series':
                if len(obj) <= 1000:  # 小Series直接序列化
                    return SerializationResult(
                        type='direct',
                        data={
                            '_type': 'pandas.Series',
                            'values': obj.tolist(),
                            'index': [str(idx) for idx in obj.index],
                            'name': obj.name
                        }
                    )
                else:
                    return self._store_object(obj, preview=f"Series(length={len(obj)}, name={obj.name})")
            
            # numpy ndarray
            elif type_name == 'ndarray':
                size = obj.nbytes
                if size <= self.config.max_direct_size:
                    return SerializationResult(
                        type='direct',
                        data={
                            '_type': 'numpy.ndarray',
                            'shape': obj.shape,
                            'dtype': str(obj.dtype),
                            'data': obj.tolist()
                        },
                        metadata={'size_bytes': size}
                    )
                else:
                    return self._store_object(obj, preview=f"ndarray(shape={obj.shape}, dtype={obj.dtype})")
            
            # 其他数据容器，尝试通用处理
            else:
                return self._store_object(obj)
                
        except Exception as e:
            # 转换失败，存储对象
            return self._store_object(obj, error=str(e))
    
    def _store_object(self, obj: Any, preview: Optional[str] = None, error: Optional[str] = None) -> SerializationResult:
        """存储对象并返回引用"""
        object_id = f"obj_{uuid.uuid4().hex[:12]}"
        
        # 获取类型信息
        obj_type = type(obj)
        type_name = f"{obj_type.__module__}.{obj_type.__name__}"
        
        # 估算大小
        size_estimate = 0
        try:
            size_estimate = sys.getsizeof(obj)
        except:
            pass
        
        # 提取可用方法
        available_methods = self._extract_methods(obj)
        
        # 生成预览
        if preview is None:
            try:
                preview = str(obj)[:self.config.max_preview_length]
            except:
                preview = f"<{type_name} object>"
        
        # 创建元数据
        metadata = ObjectMetadata(
            object_id=object_id,
            object_type=type_name,
            size_estimate=size_estimate,
            available_methods=available_methods,
            preview=preview
        )
        
        # 存储
        self.object_store[object_id] = obj
        self.metadata_store[object_id] = metadata
        
        # 返回结果
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
    
    def _extract_methods(self, obj: Any) -> List[Dict[str, Any]]:
        """提取对象的可用方法"""
        available_methods = []
        
        for name in dir(obj):
            if name.startswith('_'):
                continue
            
            try:
                attr = getattr(obj, name)
                if callable(attr):
                    # 提取参数信息
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
                        # 无法获取签名，只添加方法名
                        available_methods.append({
                            'name': name,
                            'params': []
                        })
            except:
                continue
        
        return available_methods
    
    def get_object(self, object_id: str) -> Optional[Any]:
        """获取存储的对象"""
        return self.object_store.get(object_id)
    
    def get_metadata(self, object_id: str) -> Optional[ObjectMetadata]:
        """获取对象元数据"""
        return self.metadata_store.get(object_id)
    
    def get_resource(self, resource_id: str) -> Optional[Dict]:
        """获取Resource数据"""
        return self.resource_store.get(resource_id)
    
    def cleanup_objects(self, max_age_seconds: int = 3600):
        """清理旧对象"""
        from datetime import datetime, timedelta
        
        now = datetime.now()
        to_remove = []
        
        for object_id, metadata in self.metadata_store.items():
            created_at = datetime.fromisoformat(metadata.created_at)
            age = (now - created_at).total_seconds()
            
            if age > max_age_seconds:
                to_remove.append(object_id)
        
        for object_id in to_remove:
            del self.object_store[object_id]
            del self.metadata_store[object_id]
        
        return len(to_remove)


# 全局序列化器实例(可在MCP server中使用)
_global_serializer: Optional[SmartSerializer] = None


def get_serializer(config: Optional[SerializationConfig] = None) -> SmartSerializer:
    """获取全局序列化器实例"""
    global _global_serializer
    
    if _global_serializer is None:
        _global_serializer = SmartSerializer(config)
    
    return _global_serializer


def reset_serializer():
    """重置全局序列化器"""
    global _global_serializer
    _global_serializer = None
