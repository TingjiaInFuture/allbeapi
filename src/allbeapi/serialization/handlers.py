#!/usr/bin/env python3
"""
库特定的序列化处理器
这些处理器可以通过配置文件动态加载，而非硬编码到核心代码中
"""

from typing import Any, Dict
from allbeapi.serialization.engine import SerializationResult
import json


class LibraryHandlers:
    """库特定处理器集合"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        config: library_specific配置
        """
        self.config = config
    
    def _handle_http_response(self, obj: Any, context: Dict) -> SerializationResult:
        """处理HTTP响应对象（requests, httpx等通用）"""
        lib_config = self.config.get('requests', {})
        max_text_length = lib_config.get('response_max_text_length', 10000)  # 增加默认长度
        include_headers = lib_config.get('include_headers', True)
        include_cookies = lib_config.get('include_cookies', False)
        
        try:
            # 通用HTTP响应接口
            data = {
                '_type': f'{type(obj).__module__}.{type(obj).__name__}',
                'status_code': getattr(obj, 'status_code', None),
                'url': str(getattr(obj, 'url', '')),
                'ok': getattr(obj, 'ok', None),
                'reason': getattr(obj, 'reason', None),
                'encoding': getattr(obj, 'encoding', None)
            }
            
            # 🔥 关键修复：正确提取响应内容
            # 1. 优先尝试 JSON 内容
            try:
                if hasattr(obj, 'json') and callable(obj.json):
                    json_data = obj.json()
                    data['content'] = json_data
                    data['content_type'] = 'json'
            except Exception:
                # JSON 解析失败，继续尝试文本
                pass
            
            # 2. 如果没有 JSON，提取文本内容
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
            
            # 3. 如果都没有，尝试二进制内容
            if 'content' not in data and hasattr(obj, 'content'):
                content_bytes = obj.content
                # 尝试解码为文本
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
                    # 无法解码，返回 base64
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
            
            # 计算大小
            size = len(json.dumps(data).encode('utf-8'))
            
            return SerializationResult(
                type='direct',
                data=data,
                metadata={'size_bytes': size, 'handler': 'http_response'}
            )
        except Exception as e:
            # 降级到默认处理
            return None
    
    def _handle_image(self, obj: Any, context: Dict) -> SerializationResult:
        """处理PIL Image对象 -> Resource"""
        lib_config = self.config.get('PIL', {})
        thumbnail_size = tuple(lib_config.get('thumbnail_size', [200, 200]))
        image_format = lib_config.get('image_format', 'PNG')
        
        try:
            import io
            import uuid
            
            # 创建缩略图
            thumb = obj.copy()
            thumb.thumbnail(thumbnail_size)
            
            # 转换为字节
            buffer = io.BytesIO()
            thumb.save(buffer, format=image_format)
            thumbnail_bytes = buffer.getvalue()
            
            # 生成resource_id
            resource_id = f"img_{uuid.uuid4().hex[:12]}"
            
            # 返回Resource引用和缩略图
            return SerializationResult(
                type='resource',
                data={
                    'uri': f'mcp://resources/{resource_id}',
                    'content_type': f'image/{image_format.lower()}',
                    'width': obj.width,
                    'height': obj.height,
                    'mode': obj.mode,
                    'format': obj.format,
                    'thumbnail_base64': None  # 可选：包含base64缩略图
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
        """处理pandas DataFrame（增强版）"""
        lib_config = self.config.get('pandas', {})
        max_rows = lib_config.get('max_rows_direct', 100)
        max_cols = lib_config.get('max_cols_direct', 20)
        float_precision = lib_config.get('float_precision', 2)
        
        try:
            num_rows, num_cols = obj.shape
            
            # 如果超过限制，返回对象引用
            if num_rows > max_rows or num_cols > max_cols:
                preview = (
                    f"DataFrame(shape={obj.shape}, "
                    f"columns={obj.columns.tolist()[:5]}..., "
                    f"dtypes={dict(obj.dtypes.head())})"
                )
                return None  # 让默认处理器存储对象
            
            # Handle MultiIndex columns
            export_df = obj
            columns_list = obj.columns.tolist()
            if len(columns_list) > 0 and isinstance(columns_list[0], tuple):
                export_df = obj.copy()
                export_df.columns = [str(col) for col in export_df.columns]

            # 直接序列化
            # 格式化浮点数
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
        """处理numpy数组（增强版）"""
        lib_config = self.config.get('numpy', {})
        max_elements = lib_config.get('max_elements_direct', 1000)
        float_precision = lib_config.get('float_precision', 4)
        
        try:
            import numpy as np
            
            # 检查元素数量
            num_elements = obj.size
            
            if num_elements > max_elements:
                preview = f"ndarray(shape={obj.shape}, dtype={obj.dtype}, size={num_elements})"
                return None  # 存储对象
            
            # 格式化数组
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
    创建处理器注册表
    
    返回: {full_type_name: handler_method}
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
