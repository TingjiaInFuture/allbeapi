"""
AllBeAPI Python SDK

Python客户端库，用于与AllBeAPI平台交互。
支持机器学习推理、图像/视频处理和3D渲染服务。

作者: AllBeAPI Team
版本: 2.0.0
许可证: MIT
"""

import requests
import json
from typing import Dict, List, Optional, Union, Any
from pathlib import Path
import io


class AllBeApiError(Exception):
    """AllBeAPI异常类"""
    pass


class AllBeApi:
    """
    AllBeAPI主客户端类
    
    提供对所有AllBeAPI服务的统一访问接口。
    """
    
    def __init__(self, base_url: str = "https://res.allbeapi.top", timeout: int = 30):
        """
        初始化AllBeAPI客户端
        
        Args:
            base_url: API基础URL
            timeout: 请求超时时间（秒）
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        
        # 初始化各个服务API
        self.eslint = ESLintAPI(self)
        self.mermaid_cli = MermaidCliAPI(self)
        self.pdfkit = PDFKitAPI(self)
        self.tensorflow_js = TensorFlowJsAPI(self)
        self.opencv_ffmpeg = OpenCVFfmpegAPI(self)
        self.three_js = ThreeJsAPI(self)
    
    def _request(self, method: str, path: str, params: Optional[Dict] = None, 
                json_data: Optional[Dict] = None, files: Optional[Dict] = None,
                data: Optional[Dict] = None) -> Union[requests.Response, Dict, bytes]:
        """
        内部请求方法
        
        Args:
            method: HTTP方法
            path: API路径
            params: URL参数
            json_data: JSON数据
            files: 文件数据
            data: 表单数据
            
        Returns:
            响应数据
            
        Raises:
            AllBeApiError: API请求失败
        """
        url = f"{self.base_url}{path}"
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                files=files,
                data=data,
                timeout=self.timeout
            )
            
            if not response.ok:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', f'HTTP {response.status_code}')
                except:
                    error_msg = f'HTTP {response.status_code}: {response.text}'
                raise AllBeApiError(f"API请求失败: {error_msg}")
            
            content_type = response.headers.get('content-type', '')
            
            # 根据内容类型返回相应格式
            if 'application/json' in content_type:
                return response.json()
            elif content_type.startswith('image/') or content_type == 'application/pdf':
                return response.content
            else:
                return response.text
                
        except requests.RequestException as e:
            raise AllBeApiError(f"网络请求错误: {str(e)}")
    
    def health_check(self) -> Dict[str, Any]:
        """
        检查API服务健康状态
        
        Returns:
            健康状态信息
        """
        return self._request('GET', '/health')


class ESLintAPI:
    """ESLint代码检查API"""
    
    def __init__(self, client: AllBeApi):
        self.client = client
    
    def lint(self, code: str, rules: Optional[Dict] = None, 
             options: Optional[Dict] = None) -> Dict[str, Any]:
        """
        对JavaScript/TypeScript代码进行静态分析
        
        Args:
            code: 要检查的代码
            rules: ESLint规则配置
            options: 额外的ESLint选项
            
        Returns:
            代码检查结果
        """
        data = {'code': code}
        if rules:
            data['rules'] = rules
        if options:
            data.update(options)
            
        return self.client._request('POST', '/eslint/lint', json_data=data)


class MermaidCliAPI:
    """Mermaid图表生成API"""
    
    def __init__(self, client: AllBeApi):
        self.client = client
    
    def generate_diagram(self, mermaid_definition: str, 
                        options: Optional[Dict] = None) -> bytes:
        """
        从文本定义生成图表
        
        Args:
            mermaid_definition: Mermaid图表定义
            options: 生成选项（如主题、输出格式）
            
        Returns:
            图表图像数据
        """
        data = {'mermaid': mermaid_definition}
        if options:
            data.update(options)
            
        return self.client._request('POST', '/mermaid-cli/generate-diagram', 
                                   json_data=data)


class PDFKitAPI:
    """PDF生成API"""
    
    def __init__(self, client: AllBeApi):
        self.client = client
    
    def generate(self, content: str, options: Optional[Dict] = None) -> bytes:
        """
        生成PDF文档
        
        Args:
            content: HTML内容或文本
            options: PDF生成选项
            
        Returns:
            PDF文档数据
        """
        data = {'content': content}
        if options:
            data.update(options)
            
        return self.client._request('POST', '/pdfkit/generate', json_data=data)


class TensorFlowJsAPI:
    """TensorFlow.js机器学习推理API"""
    
    def __init__(self, client: AllBeApi):
        self.client = client
    
    def classify_image(self, image_file: Union[str, Path, io.IOBase], 
                      options: Optional[Dict] = None) -> Dict[str, Any]:
        """
        图像分类
        
        Args:
            image_file: 图像文件路径或文件对象
            options: 分类选项
            
        Returns:
            分类结果
        """
        files = self._prepare_file('image', image_file)
        data = options or {}
        
        return self.client._request('POST', '/tensorflow-js/classify-image', 
                                   files=files, data=data)
    
    def predict_text(self, text: str, options: Optional[Dict] = None) -> Dict[str, Any]:
        """
        文本预测分析
        
        Args:
            text: 输入文本
            options: 预测选项
            
        Returns:
            文本分析结果
        """
        data = {'text': text}
        if options:
            data.update(options)
            
        return self.client._request('POST', '/tensorflow-js/predict-text', 
                                   json_data=data)
    
    def custom_inference(self, data: Union[str, Path, io.IOBase, Dict], 
                        options: Optional[Dict] = None) -> Dict[str, Any]:
        """
        自定义模型推理
        
        Args:
            data: 输入数据（文件或字典）
            options: 模型配置选项
            
        Returns:
            推理结果
        """
        if isinstance(data, (str, Path, io.IOBase)):
            files = self._prepare_file('data', data)
            return self.client._request('POST', '/tensorflow-js/custom-inference',
                                       files=files, data=options or {})
        else:
            request_data = {'data': json.dumps(data)}
            if options:
                request_data.update(options)
            return self.client._request('POST', '/tensorflow-js/custom-inference',
                                       data=request_data)
    
    def detect_objects(self, image_file: Union[str, Path, io.IOBase], 
                      options: Optional[Dict] = None) -> Dict[str, Any]:
        """
        对象检测
        
        Args:
            image_file: 图像文件
            options: 检测选项
            
        Returns:
            检测结果
        """
        files = self._prepare_file('image', image_file)
        data = options or {}
        
        return self.client._request('POST', '/tensorflow-js/detect-objects',
                                   files=files, data=data)
    
    def batch_inference(self, files: List[Union[str, Path, io.IOBase]], 
                       options: Optional[Dict] = None) -> Dict[str, Any]:
        """
        批量推理
        
        Args:
            files: 文件列表
            options: 推理选项
            
        Returns:
            批量推理结果
        """
        file_uploads = []
        for i, file in enumerate(files):
            if isinstance(file, (str, Path)):
                with open(file, 'rb') as f:
                    file_uploads.append(('files', (f.name, f.read())))
            else:
                file_uploads.append(('files', file))
        
        return self.client._request('POST', '/tensorflow-js/batch-inference',
                                   files=file_uploads, data=options or {})
    
    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """
        获取模型信息
        
        Args:
            model_name: 模型名称
            
        Returns:
            模型信息
        """
        return self.client._request('GET', f'/tensorflow-js/model-info/{model_name}')
    
    def get_memory_status(self) -> Dict[str, Any]:
        """
        获取内存状态
        
        Returns:
            内存使用信息
        """
        return self.client._request('GET', '/tensorflow-js/memory-status')
    
    def _prepare_file(self, field_name: str, file: Union[str, Path, io.IOBase]) -> Dict:
        """准备文件上传"""
        if isinstance(file, (str, Path)):
            with open(file, 'rb') as f:
                return {field_name: (Path(file).name, f.read())}
        else:
            return {field_name: file}


class OpenCVFfmpegAPI:
    """OpenCV和FFmpeg图像/视频处理API"""
    
    def __init__(self, client: AllBeApi):
        self.client = client
    
    def process_image(self, image_file: Union[str, Path, io.IOBase], 
                     operations: List[Dict]) -> bytes:
        """
        高级图像处理
        
        Args:
            image_file: 图像文件
            operations: 处理操作列表
            
        Returns:
            处理后的图像数据
        """
        files = self._prepare_file('image', image_file)
        data = {'operations': json.dumps(operations)}
        
        return self.client._request('POST', '/opencv-ffmpeg/process-image',
                                   files=files, data=data)
    
    def process_video(self, video_file: Union[str, Path, io.IOBase], 
                     operations: List[Dict], output_format: str = 'mp4') -> Dict[str, Any]:
        """
        高级视频处理
        
        Args:
            video_file: 视频文件
            operations: 处理操作列表
            output_format: 输出格式
            
        Returns:
            处理结果信息
        """
        files = self._prepare_file('video', video_file)
        data = {
            'operations': json.dumps(operations),
            'outputFormat': output_format
        }
        
        return self.client._request('POST', '/opencv-ffmpeg/process-video',
                                   files=files, data=data)
    
    def detect_objects(self, image_file: Union[str, Path, io.IOBase], 
                      method: str = 'contours', **kwargs) -> Dict[str, Any]:
        """
        对象检测
        
        Args:
            image_file: 图像文件
            method: 检测方法
            **kwargs: 其他参数
            
        Returns:
            检测结果
        """
        files = self._prepare_file('image', image_file)
        data = {'method': method, **kwargs}
        
        return self.client._request('POST', '/opencv-ffmpeg/detect-objects',
                                   files=files, data=data)
    
    def extract_features(self, image_file: Union[str, Path, io.IOBase], 
                        method: str = 'orb', max_features: int = 500) -> Dict[str, Any]:
        """
        特征提取
        
        Args:
            image_file: 图像文件
            method: 特征提取方法
            max_features: 最大特征点数
            
        Returns:
            特征提取结果
        """
        files = self._prepare_file('image', image_file)
        data = {'method': method, 'maxFeatures': max_features}
        
        return self.client._request('POST', '/opencv-ffmpeg/extract-features',
                                   files=files, data=data)
    
    def video_to_frames(self, video_file: Union[str, Path, io.IOBase], 
                       **kwargs) -> Dict[str, Any]:
        """
        视频帧提取
        
        Args:
            video_file: 视频文件
            **kwargs: 其他参数
            
        Returns:
            帧提取结果
        """
        files = self._prepare_file('video', video_file)
        data = kwargs
        
        return self.client._request('POST', '/opencv-ffmpeg/video-to-frames',
                                   files=files, data=data)
    
    def _prepare_file(self, field_name: str, file: Union[str, Path, io.IOBase]) -> Dict:
        """准备文件上传"""
        if isinstance(file, (str, Path)):
            with open(file, 'rb') as f:
                return {field_name: (Path(file).name, f.read())}
        else:
            return {field_name: file}


class ThreeJsAPI:
    """Three.js 3D渲染API"""
    
    def __init__(self, client: AllBeApi):
        self.client = client
    
    def render_scene(self, scene_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        渲染3D场景
        
        Args:
            scene_config: 场景配置
            
        Returns:
            渲染结果
        """
        return self.client._request('POST', '/three-js/render-scene', 
                                   json_data=scene_config)
    
    def generate_model(self, model_type: str, parameters: Optional[Dict] = None, 
                      **kwargs) -> Dict[str, Any]:
        """
        生成3D模型
        
        Args:
            model_type: 模型类型
            parameters: 模型参数
            **kwargs: 其他选项
            
        Returns:
            模型生成结果
        """
        data = {
            'modelType': model_type,
            'parameters': parameters or {},
            **kwargs
        }
        
        return self.client._request('POST', '/three-js/generate-model', 
                                   json_data=data)
    
    def animate_object(self, obj: Dict[str, Any], animations: List[Dict], 
                      **kwargs) -> Dict[str, Any]:
        """
        创建动画对象
        
        Args:
            obj: 要动画的对象
            animations: 动画定义列表
            **kwargs: 动画选项
            
        Returns:
            动画创建结果
        """
        data = {
            'object': obj,
            'animations': animations,
            **kwargs
        }
        
        return self.client._request('POST', '/three-js/animate-object', 
                                   json_data=data)
    
    def get_scene_templates(self) -> Dict[str, Any]:
        """
        获取可用的场景模板
        
        Returns:
            场景模板列表
        """
        return self.client._request('GET', '/three-js/scene-templates')
    
    def render_panoramic(self, scene: Dict[str, Any], 
                        **kwargs) -> Dict[str, Any]:
        """
        渲染全景图
        
        Args:
            scene: 场景配置
            **kwargs: 渲染选项
            
        Returns:
            全景渲染结果
        """
        data = {'scene': scene, **kwargs}
        
        return self.client._request('POST', '/three-js/render-panoramic', 
                                   json_data=data)


# 使用示例
if __name__ == "__main__":
    # 初始化客户端
    api = AllBeApi('https://res.allbeapi.top')
    
    # 检查服务健康状态
    try:
        health = api.health_check()
        print("API服务状态:", health)
    except AllBeApiError as e:
        print("API错误:", e)
    
    # 机器学习推理示例
    try:
        # 图像分类
        result = api.tensorflow_js.classify_image(
            'path/to/image.jpg', 
            {'modelName': 'mobilenet'}
        )
        print("图像分类结果:", result)
        
        # 文本分析
        text_result = api.tensorflow_js.predict_text(
            "这是一个测试文本。", 
            {'maxLength': 100}
        )
        print("文本分析结果:", text_result)
        
    except AllBeApiError as e:
        print("机器学习API错误:", e)
    
    # 图像处理示例
    try:
        operations = [
            {"type": "blur", "kernelSize": 15},
            {"type": "edge_detection", "threshold1": 100, "threshold2": 200}
        ]
        
        processed_image = api.opencv_ffmpeg.process_image(
            'path/to/image.jpg', 
            operations
        )
        
        # 保存处理后的图像
        with open('processed_image.jpg', 'wb') as f:
            f.write(processed_image)
        print("图像处理完成")
        
    except AllBeApiError as e:
        print("图像处理API错误:", e)
    
    # 3D渲染示例
    try:
        scene_config = {
            'objects': [
                {'type': 'box', 'size': [1, 1, 1], 'position': [0, 0, 0]},
                {'type': 'sphere', 'radius': 0.5, 'position': [2, 0, 0]}
            ],
            'lights': [
                {'type': 'ambient', 'color': 0x404040, 'intensity': 0.6},
                {'type': 'directional', 'color': 0xffffff, 'intensity': 0.8, 
                 'position': [10, 10, 5]}
            ],
            'camera': {'position': [0, 0, 5], 'target': [0, 0, 0]}
        }
        
        render_result = api.three_js.render_scene(scene_config)
        print("3D场景渲染结果:", render_result)
        
    except AllBeApiError as e:
        print("3D渲染API错误:", e)


