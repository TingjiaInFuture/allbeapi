#!/usr/bin/env python3
"""
Library-specific serialization handlers - Fully Configuration-driven version
These handlers are completely driven by JSON configuration for maximum extensibility.
No code changes needed to add new type handlers - just modify handlers_config.json
"""

from typing import Any, Dict, Optional, Callable
from allbemcp.serialization.engine import SerializationResult
import json
from pathlib import Path


class ConfigDrivenHandlers:
    """
    Fully configuration-driven serialization handlers.
    
    All handler logic is determined by handlers_config.json.
    To add support for a new type:
    1. Add a new entry in handlers_config.json under "handlers"
    2. No code changes required
    """
    
    def __init__(self, config: Dict[str, Any], handlers_config: Optional[Dict[str, Any]] = None):
        """
        config: library_specific configuration (runtime overrides)
        handlers_config: handlers configuration from JSON file
        """
        self.config = config
        self.handlers_config = handlers_config or self._load_handlers_config()
        self._resolved_configs = {}  # Cache for resolved handler configs
    
    def _load_handlers_config(self) -> Dict[str, Any]:
        """Load handlers configuration from JSON file"""
        config_path = Path(__file__).parent / "handlers_config.json"
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"handlers": {}}
    
    def get_registered_types(self) -> list:
        """Get all registered type names from configuration"""
        return list(self.handlers_config.get("handlers", {}).keys())
    
    def _get_handler_config(self, type_name: str) -> Optional[Dict[str, Any]]:
        """Get handler configuration for a type, resolving extends if needed"""
        if type_name in self._resolved_configs:
            return self._resolved_configs[type_name]
        
        handlers = self.handlers_config.get("handlers", {})
        handler_config = handlers.get(type_name)
        
        if handler_config is None:
            return None
        
        # Handle inheritance via 'extends'
        if "extends" in handler_config:
            parent_type = handler_config["extends"]
            parent_config = self._get_handler_config(parent_type)
            if parent_config:
                # Deep merge parent and child config
                resolved = self._deep_merge(parent_config, handler_config)
                if "extends" in resolved:
                    del resolved["extends"]
            else:
                resolved = handler_config.copy()
                if "extends" in resolved:
                    del resolved["extends"]
        else:
            resolved = handler_config
        
        self._resolved_configs[type_name] = resolved
        return resolved
    
    def _deep_merge(self, base: Dict, override: Dict) -> Dict:
        """Deep merge two dictionaries"""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result
    
    def _get_lib_config(self, handler_config: Dict[str, Any]) -> Dict[str, Any]:
        """Get library-specific config with defaults"""
        namespace = handler_config.get("config_namespace", "")
        defaults = handler_config.get("config_defaults", {})
        
        # Get runtime config and merge with defaults
        runtime_config = self.config.get(namespace, {})
        return {**defaults, **runtime_config}
    
    def _get_attribute(self, obj: Any, attr_path: str, default: Any = None) -> Any:
        """Get attribute from object by path (supports dot notation and index)"""
        try:
            parts = attr_path.split('.')
            value = obj
            for part in parts:
                # Handle index notation like "shape[0]"
                if '[' in part:
                    attr, idx = part.split('[')
                    idx = int(idx.rstrip(']'))
                    if attr:
                        value = getattr(value, attr, None)
                    if value is not None:
                        value = value[idx]
                elif hasattr(value, part):
                    value = getattr(value, part)
                else:
                    return default
            return value
        except Exception:
            return default
    
    def _apply_transform(self, value: Any, transform: str) -> Any:
        """Apply a transform to a value"""
        if transform == "str":
            return str(value) if value is not None else ""
        elif transform == "dict":
            return dict(value) if value is not None else {}
        elif transform == "list":
            return list(value) if value is not None else []
        elif transform == "tuple":
            return tuple(value) if value is not None else ()
        elif transform == "base64_encode":
            import base64
            if isinstance(value, bytes):
                return base64.b64encode(value).decode('ascii')
            return value
        elif transform == "int":
            return int(value) if value is not None else 0
        elif transform == "float":
            return float(value) if value is not None else 0.0
        return value
    
    def _extract_base_fields(self, obj: Any, handler_config: Dict[str, Any], 
                             lib_config: Dict[str, Any], context: Dict) -> Dict[str, Any]:
        """Extract base fields from object based on configuration"""
        data = {}
        base_fields = handler_config.get("base_fields", {})
        
        for field_name, field_spec in base_fields.items():
            field_type = field_spec.get("type")
            
            if field_type == "literal":
                data[field_name] = field_spec.get("value")
            
            elif field_type == "attribute":
                attr = field_spec.get("attr")
                default = field_spec.get("default")
                value = self._get_attribute(obj, attr, default)
                
                # Apply transform if specified
                if "transform" in field_spec:
                    value = self._apply_transform(value, field_spec["transform"])
                
                data[field_name] = value
            
            elif field_type == "computed":
                expression = field_spec.get("expression")
                data[field_name] = self._compute_expression(
                    expression, obj, handler_config, lib_config, context
                )
            
            elif field_type == "config":
                key = field_spec.get("key")
                data[field_name] = lib_config.get(key)
        
        return data
    
    def _compute_expression(self, expression: str, obj: Any, handler_config: Dict[str, Any],
                            lib_config: Dict[str, Any], context: Dict) -> Any:
        """
        Compute a named expression.
        
        Expressions are defined in configuration and mapped to computation logic here.
        This allows adding new expressions without changing the core handler logic.
        """
        # Type expressions
        if expression == "type_full_name":
            return f'{type(obj).__module__}.{type(obj).__name__}'
        
        # Size expressions
        elif expression == "json_size":
            return context.get("_json_size", 0)
        
        # Resource expressions
        elif expression == "resource_uri":
            resource_id = context.get("_resource_id", "")
            base_url = lib_config.get("resource_base_url", "mcp://resources")
            return f'{base_url}/{resource_id}'
        
        elif expression == "resource_id":
            return context.get("_resource_id", "")
        
        # Image expressions
        elif expression == "image_content_type":
            image_format = lib_config.get("image_format", "PNG")
            return f'image/{image_format.lower()}'
        
        elif expression == "image_original_size":
            return (getattr(obj, 'width', 0), getattr(obj, 'height', 0))
        
        # DataFrame expressions
        elif expression == "dataframe_columns":
            return obj.columns.tolist()
        
        elif expression == "dataframe_dtypes":
            dtypes_dict = {}
            for col, dtype in obj.dtypes.items():
                key = str(col) if isinstance(col, tuple) else col
                dtypes_dict[key] = str(dtype)
            return dtypes_dict
        
        elif expression == "dataframe_shape":
            return list(obj.shape)
        
        elif expression == "dataframe_records":
            float_precision = lib_config.get("float_precision")
            export_df = context.get("_export_df", obj)
            if float_precision is not None:
                return export_df.round(float_precision).to_dict(orient='records')
            return export_df.to_dict(orient='records')
        
        # Numpy expressions
        elif expression == "numpy_tolist":
            import numpy as np
            float_precision = lib_config.get("float_precision", 4)
            if np.issubdtype(obj.dtype, np.floating):
                return np.round(obj, float_precision).tolist()
            return obj.tolist()
        
        # Generic expressions - can be extended via configuration
        elif expression.startswith("attr:"):
            # Expression format: "attr:attribute_path"
            attr_path = expression[5:]
            return self._get_attribute(obj, attr_path)
        
        elif expression.startswith("format:"):
            # Expression format: "format:template_string"
            # Template can use {attr_name} placeholders
            template = expression[7:]
            # Simple template substitution
            result = template
            import re
            for match in re.finditer(r'\{(\w+(?:\.\w+)*)\}', template):
                attr_path = match.group(1)
                value = self._get_attribute(obj, attr_path, "")
                result = result.replace(match.group(0), str(value))
            return result
        
        return None
    
    def _check_size_limits(self, obj: Any, handler_config: Dict[str, Any], 
                           lib_config: Dict[str, Any]) -> bool:
        """Check if object exceeds size limits. Returns True if within limits."""
        size_check = handler_config.get("size_check", {})
        if not size_check.get("enabled", False):
            return True
        
        # Check dimensions (for DataFrame)
        dimensions = size_check.get("dimensions", {})
        for dim_name, dim_spec in dimensions.items():
            getter = dim_spec.get("getter", "")
            max_config = dim_spec.get("max_config", "")
            max_value = lib_config.get(max_config, float('inf'))
            
            actual_value = self._get_attribute(obj, getter, 0)
            if actual_value > max_value:
                return False
        
        # Check element count (for numpy array)
        element_count = size_check.get("element_count", {})
        if element_count:
            getter = element_count.get("getter", "size")
            max_config = element_count.get("max_config", "")
            max_value = lib_config.get(max_config, float('inf'))
            actual_value = self._get_attribute(obj, getter, 0)
            
            if actual_value > max_value:
                return False
        
        return True
    
    def _handle_content_extraction(self, obj: Any, data: Dict[str, Any],
                                   handler_config: Dict[str, Any], 
                                   lib_config: Dict[str, Any]) -> None:
        """Handle content extraction for HTTP responses and similar objects"""
        content_config = handler_config.get("content_extraction", {})
        if not content_config:
            return
        
        priority = content_config.get("priority", [])
        strategies = content_config.get("strategies", {})
        max_text_length = lib_config.get("response_max_text_length", 10000)
        
        for strategy_name in priority:
            if "content" in data:
                break
                
            strategy = strategies.get(strategy_name, {})
            
            if strategy_name == "json":
                # Try JSON extraction
                method = strategy.get("method", "json")
                if hasattr(obj, method) and callable(getattr(obj, method)):
                    try:
                        json_data = getattr(obj, method)()
                        on_success = strategy.get("on_success", {})
                        for key, value in on_success.items():
                            if value == "@result":
                                data[key] = json_data
                            else:
                                data[key] = value
                    except Exception:
                        pass
            
            elif strategy_name == "text":
                # Try text extraction
                attr = strategy.get("attribute", "text")
                if hasattr(obj, attr):
                    text = getattr(obj, attr)
                    if text:
                        on_success = strategy.get("on_success", {})
                        if len(text) > max_text_length:
                            data["content"] = text[:max_text_length]
                            on_truncate = strategy.get("on_truncate", {})
                            for key, value in on_truncate.items():
                                if value == "@original_length":
                                    data[key] = len(text)
                                else:
                                    data[key] = value
                            data["content_type"] = on_success.get("content_type", "text")
                        else:
                            for key, value in on_success.items():
                                if value == "@result":
                                    data[key] = text
                                else:
                                    data[key] = value
            
            elif strategy_name == "binary":
                # Try binary extraction
                attr = strategy.get("attribute", "content")
                if hasattr(obj, attr):
                    content_bytes = getattr(obj, attr)
                    if content_bytes:
                        encoding = getattr(obj, strategy.get("decode_with", "encoding"), None)
                        encoding = encoding or strategy.get("fallback_encoding", "utf-8")
                        
                        try:
                            text = content_bytes.decode(encoding)
                            on_success = strategy.get("on_decode_success", {})
                            if len(text) > max_text_length:
                                data["content"] = text[:max_text_length]
                                data["text_truncated"] = True
                                data["text_full_length"] = len(text)
                            else:
                                data["content"] = text
                            data["content_type"] = on_success.get("content_type", "text")
                        except UnicodeDecodeError:
                            import base64
                            on_failure = strategy.get("on_decode_failure", {})
                            data["content"] = base64.b64encode(
                                content_bytes[:max_text_length]
                            ).decode('ascii')
                            data["content_type"] = on_failure.get("content_type", "binary")
                            data["content_encoding"] = on_failure.get("content_encoding", "base64")
                            if len(content_bytes) > max_text_length:
                                data["text_truncated"] = True
    
    def _handle_conditional_fields(self, obj: Any, data: Dict[str, Any],
                                   handler_config: Dict[str, Any],
                                   lib_config: Dict[str, Any]) -> None:
        """Handle conditional fields"""
        conditional_fields = handler_config.get("conditional_fields", [])
        
        for field_spec in conditional_fields:
            condition = field_spec.get("condition", {})
            
            # Check condition
            should_include = False
            
            if "config_key" in condition:
                config_key = condition.get("config_key")
                expected_value = condition.get("value")
                should_include = lib_config.get(config_key) == expected_value
            elif "has_attr" in condition:
                attr_name = condition.get("has_attr")
                should_include = hasattr(obj, attr_name)
            
            if should_include:
                field_name = field_spec.get("field")
                field_type = field_spec.get("type", "attribute")
                
                if field_type == "attribute":
                    attr = field_spec.get("attr")
                    if hasattr(obj, attr):
                        value = getattr(obj, attr)
                        if "transform" in field_spec:
                            value = self._apply_transform(value, field_spec["transform"])
                        data[field_name] = value
                elif field_type == "literal":
                    data[field_name] = field_spec.get("value")
    
    def _handle_preprocessing(self, obj: Any, handler_config: Dict[str, Any],
                              lib_config: Dict[str, Any], context: Dict) -> None:
        """Handle preprocessing steps"""
        preprocessing = handler_config.get("preprocessing", {})
        if not preprocessing:
            return
        
        prep_type = preprocessing.get("type")
        
        if prep_type == "dataframe_columns":
            # Handle DataFrame MultiIndex columns
            columns_list = obj.columns.tolist()
            if len(columns_list) > 0 and isinstance(columns_list[0], tuple):
                export_df = obj.copy()
                export_df.columns = [str(col) for col in export_df.columns]
                context["_export_df"] = export_df
            else:
                context["_export_df"] = obj
    
    def _build_metadata(self, obj: Any, data: Dict[str, Any], handler_config: Dict[str, Any],
                        lib_config: Dict[str, Any], context: Dict) -> Dict[str, Any]:
        """Build metadata for the result"""
        metadata_config = handler_config.get("metadata", {})
        metadata = {}
        
        for key, spec in metadata_config.items():
            if isinstance(spec, str):
                # Simple literal value
                metadata[key] = spec
            elif isinstance(spec, dict):
                spec_type = spec.get("type")
                if spec_type == "computed":
                    expression = spec.get("expression")
                    if expression == "json_size":
                        metadata[key] = len(json.dumps(data).encode('utf-8'))
                    else:
                        metadata[key] = self._compute_expression(
                            expression, obj, handler_config, lib_config, context
                        )
                elif spec_type == "config":
                    config_key = spec.get("key")
                    value = lib_config.get(config_key)
                    # Convert list to tuple for certain fields
                    if isinstance(value, list):
                        value = tuple(value)
                    metadata[key] = value
                elif spec_type == "literal":
                    metadata[key] = spec.get("value")
        
        return metadata
    
    def handle(self, obj: Any, context: Dict, type_name: Optional[str] = None) -> Optional[SerializationResult]:
        """
        Universal handler function that processes objects based on JSON configuration.
        
        This is the core generic handler that reads configuration and applies
        the appropriate serialization logic for any registered type.
        
        Args:
            obj: The object to serialize
            context: Additional context for serialization
            type_name: Optional explicit type name. If not provided, will be inferred from obj.
            
        Returns:
            SerializationResult if handled, None if type not registered or error occurred.
        """
        # Determine type name
        if type_name is None:
            type_name = f'{type(obj).__module__}.{type(obj).__name__}'
        
        handler_config = self._get_handler_config(type_name)
        if handler_config is None:
            return None
        
        lib_config = self._get_lib_config(handler_config)
        result_type = handler_config.get("result_type", "direct")
        
        try:
            # Check size limits
            if not self._check_size_limits(obj, handler_config, lib_config):
                return None
            
            # Initialize context for computed values
            local_context = dict(context)
            
            # Handle preprocessing
            self._handle_preprocessing(obj, handler_config, lib_config, local_context)
            
            # Generate resource ID if needed
            resource_gen = handler_config.get("resource_generation", {})
            if resource_gen:
                import uuid
                prefix = resource_gen.get("id_prefix", "res_")
                length = resource_gen.get("id_length", 12)
                resource_id = f"{prefix}{uuid.uuid4().hex[:length]}"
                local_context["_resource_id"] = resource_id
            
            # Extract base fields
            data = self._extract_base_fields(obj, handler_config, lib_config, local_context)
            
            # Handle content extraction (for HTTP responses)
            self._handle_content_extraction(obj, data, handler_config, lib_config)
            
            # Handle conditional fields
            self._handle_conditional_fields(obj, data, handler_config, lib_config)
            
            # Build metadata
            metadata = self._build_metadata(obj, data, handler_config, lib_config, local_context)
            
            return SerializationResult(
                type=result_type,
                data=data,
                metadata=metadata
            )
        
        except Exception as e:
            # Fallback to default handling
            return None
    
    def create_type_handler(self, type_name: str) -> Callable[[Any, Dict], Optional[SerializationResult]]:
        """
        Create a handler function for a specific type.
        
        This allows creating handler functions dynamically based on configuration.
        """
        def handler(obj: Any, context: Dict) -> Optional[SerializationResult]:
            return self.handle(obj, context, type_name)
        
        handler.__doc__ = f"Handle {type_name} objects"
        handler.__name__ = f"handle_{type_name.replace('.', '_')}"
        
        return handler


# Legacy compatibility - LibraryHandlers class wraps ConfigDrivenHandlers
class LibraryHandlers(ConfigDrivenHandlers):
    """Collection of library-specific handlers (Legacy compatibility wrapper)"""
    pass


def create_handler_registry(config: Dict[str, Any]) -> Dict[str, Callable]:
    """
    Create handler registry from configuration.
    
    This function automatically creates handlers for all types defined in
    handlers_config.json. No code changes needed to add new types.
    
    Returns: {full_type_name: handler_function}
    """
    handlers = ConfigDrivenHandlers(config.get('library_specific', {}))
    
    registry = {}
    
    # Automatically register all types from configuration
    for type_name in handlers.get_registered_types():
        registry[type_name] = handlers.create_type_handler(type_name)
    
    return registry
