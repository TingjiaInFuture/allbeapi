#!/usr/bin/env python3
"""
Library-specific serialization handlers
These handlers can be dynamically loaded via configuration instead of hardcoded into the core code
"""

from typing import Any, Dict
from allbeapi.serialization.engine import SerializationResult
import json


class LibraryHandlers:
    """Collection of library-specific handlers"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        config: library_specific configuration
        """
        self.config = config
    
    def _handle_http_response(self, obj: Any, context: Dict) -> SerializationResult:
        """Handle HTTP response objects (requests, httpx, etc.)"""
        lib_config = self.config.get('requests', {})
        max_text_length = lib_config.get('response_max_text_length', 10000)  # Increase default length
        include_headers = lib_config.get('include_headers', True)
        include_cookies = lib_config.get('include_cookies', False)
        
        try:
            # Generic HTTP response interface
            data = {
                '_type': f'{type(obj).__module__}.{type(obj).__name__}',
                'status_code': getattr(obj, 'status_code', None),
                'url': str(getattr(obj, 'url', '')),
                'ok': getattr(obj, 'ok', None),
                'reason': getattr(obj, 'reason', None),
                'encoding': getattr(obj, 'encoding', None)
            }
            
            # 🔥 Critical Fix: Correctly extract response content
            # 1. Try JSON content first
            try:
                if hasattr(obj, 'json') and callable(obj.json):
                    json_data = obj.json()
                    data['content'] = json_data
                    data['content_type'] = 'json'
            except Exception:
                # JSON parsing failed, continue to try text
                pass
            
            # 2. If no JSON, extract text content
            if 'content' not in data and hasattr(obj, 'text'):
                text = obj.text
                if len(text) > max_text_length:
                    data['content'] = text[:max_text_length]
                    data['text_truncated'] = True
                    data['text_full_length'] = len(text)
                    data['content_type'] = 'text'
                else:
                    data['content'] = text
                    data['content_type'] = 'text'
            
            # 3. If neither, try binary content
            if 'content' not in data and hasattr(obj, 'content'):
                content_bytes = obj.content
                # Try to decode as text
                try:
                    text = content_bytes.decode(obj.encoding or 'utf-8')
                    if len(text) > max_text_length:
                        data['content'] = text[:max_text_length]
                        data['text_truncated'] = True
                        data['text_full_length'] = len(text)
                    else:
                        data['content'] = text
                    data['content_type'] = 'text'
                except UnicodeDecodeError:
                    # Cannot decode, return base64
                    import base64
                    data['content'] = base64.b64encode(content_bytes[:max_text_length]).decode('ascii')
                    data['content_type'] = 'binary'
                    data['content_encoding'] = 'base64'
                    if len(content_bytes) > max_text_length:
                        data['text_truncated'] = True
            
            # Headers
            if include_headers and hasattr(obj, 'headers'):
                data['headers'] = dict(obj.headers)
            
            # Cookies
            if include_cookies and hasattr(obj, 'cookies'):
                data['cookies'] = dict(obj.cookies)
            
            # Calculate size
            size = len(json.dumps(data).encode('utf-8'))
            
            return SerializationResult(
                type='direct',
                data=data,
                metadata={'size_bytes': size, 'handler': 'http_response'}
            )
        except Exception as e:
            # Fallback to default handling
            return None
    
    def _handle_image(self, obj: Any, context: Dict) -> SerializationResult:
        """Handle PIL Image object -> Resource"""
        lib_config = self.config.get('PIL', {})
        thumbnail_size = tuple(lib_config.get('thumbnail_size', [200, 200]))
        image_format = lib_config.get('image_format', 'PNG')
        
        try:
            import io
            import uuid
            
            # Create thumbnail
            thumb = obj.copy()
            thumb.thumbnail(thumbnail_size)
            
            # Convert to bytes
            buffer = io.BytesIO()
            thumb.save(buffer, format=image_format)
            thumbnail_bytes = buffer.getvalue()
            
            # Generate resource_id
            resource_id = f"img_{uuid.uuid4().hex[:12]}"
            
            # Return Resource reference and thumbnail
            return SerializationResult(
                type='resource',
                data={
                    'uri': f'mcp://resources/{resource_id}',
                    'content_type': f'image/{image_format.lower()}',
                    'width': obj.width,
                    'height': obj.height,
                    'mode': obj.mode,
                    'format': obj.format,
                    'thumbnail_base64': None  # Optional: include base64 thumbnail
                },
                metadata={
                    'resource_id': resource_id,
                    'original_size': (obj.width, obj.height),
                    'thumbnail_size': thumbnail_size,
                    'handler': 'pil_image'
                }
            )
        except Exception as e:
            return None
    
    def _handle_pandas_dataframe(self, obj: Any, context: Dict) -> SerializationResult:
        """Handle pandas DataFrame (Enhanced)"""
        lib_config = self.config.get('pandas', {})
        max_rows = lib_config.get('max_rows_direct', 100)
        max_cols = lib_config.get('max_cols_direct', 20)
        float_precision = lib_config.get('float_precision', 2)
        
        try:
            num_rows, num_cols = obj.shape
            
            # If exceeds limit, return object reference
            if num_rows > max_rows or num_cols > max_cols:
                preview = (
                    f"DataFrame(shape={obj.shape}, "
                    f"columns={obj.columns.tolist()[:5]}..., "
                    f"dtypes={dict(obj.dtypes.head())})"
                )
                return None  # Let default handler store object
            
            # Handle MultiIndex columns
            export_df = obj
            columns_list = obj.columns.tolist()
            if len(columns_list) > 0 and isinstance(columns_list[0], tuple):
                export_df = obj.copy()
                export_df.columns = [str(col) for col in export_df.columns]

            # Serialize directly
            # Format floats
            if float_precision is not None:
                formatted_data = export_df.round(float_precision).to_dict(orient='records')
            else:
                formatted_data = export_df.to_dict(orient='records')
            
            # Handle dtypes keys if they are tuples
            dtypes_dict = {}
            for col, dtype in obj.dtypes.items():
                key = str(col) if isinstance(col, tuple) else col
                dtypes_dict[key] = str(dtype)

            data = {
                '_type': 'pandas.DataFrame',
                'columns': columns_list,
                'dtypes': dtypes_dict,
                'shape': [num_rows, num_cols],
                'data': formatted_data,
                'index_name': obj.index.name
            }
            
            return SerializationResult(
                type='direct',
                data=data,
                metadata={'handler': 'pandas_dataframe'}
            )
        except Exception as e:
            return None
    
    def _handle_numpy_array(self, obj: Any, context: Dict) -> SerializationResult:
        """Handle numpy array (Enhanced)"""
        lib_config = self.config.get('numpy', {})
        max_elements = lib_config.get('max_elements_direct', 1000)
        float_precision = lib_config.get('float_precision', 4)
        
        try:
            import numpy as np
            
            # Check element count
            num_elements = obj.size
            
            if num_elements > max_elements:
                preview = f"ndarray(shape={obj.shape}, dtype={obj.dtype}, size={num_elements})"
                return None  # Store object
            
            # Format array
            if np.issubdtype(obj.dtype, np.floating):
                formatted_array = np.round(obj, float_precision).tolist()
            else:
                formatted_array = obj.tolist()
            
            data = {
                '_type': 'numpy.ndarray',
                'shape': obj.shape,
                'dtype': str(obj.dtype),
                'data': formatted_array,
                'size': num_elements
            }
            
            return SerializationResult(
                type='direct',
                data=data,
                metadata={'handler': 'numpy_array'}
            )
        except Exception as e:
            return None


def create_handler_registry(config: Dict[str, Any]) -> Dict[str, callable]:
    """
    Create handler registry
    
    Returns: {full_type_name: handler_method}
    """
    handlers = LibraryHandlers(config.get('library_specific', {}))
    
    registry = {
        'requests.models.Response': handlers._handle_http_response,
        'httpx.Response': handlers._handle_http_response,
        'PIL.Image.Image': handlers._handle_image,
        'pandas.core.frame.DataFrame': handlers._handle_pandas_dataframe,
        'numpy.ndarray': handlers._handle_numpy_array,
    }
    
    return registry
