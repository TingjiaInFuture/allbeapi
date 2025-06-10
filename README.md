# AllBeAPI Platform

**赋能低性能设备 - 通过卸载密集计算让嵌入式和IoT设备更强大**

AllBeAPI Platform是一个专为低性能设备设计的云计算平台，通过将计算密集型任务卸载到云端，让嵌入式系统、IoT设备和边缘计算设备能够执行复杂的机器学习推理、图像/视频处理和3D渲染等任务。

## 🚀 已集成服务

### 📊 机器学习推理 (TensorFlow.js)
- **图像分类**: 使用预训练模型进行快速图像识别
- **对象检测**: 实时检测图像中的多个对象
- **文本分析**: 情感分析、实体提取、语言检测
- **自定义模型**: 支持加载和运行自定义TensorFlow.js模型
- **批量处理**: 高效处理多个文件的批量推理

### 🖼️ 高级图像/视频处理 (OpenCV + FFmpeg)
- **图像处理**: 滤波、边缘检测、形态学操作、直方图均衡化
- **计算机视觉**: 人脸检测、轮廓检测、特征提取、模板匹配
- **视频处理**: 格式转换、剪辑、调整大小、添加水印
- **帧提取**: 从视频中提取关键帧
- **实时处理**: 支持流式视频处理

### 🎨 3D渲染 (Three.js)
- **场景渲染**: 创建复杂的3D场景和环境
- **模型生成**: 程序化生成3D几何体和模型
- **动画制作**: 创建流畅的3D动画和转场效果
- **全景渲染**: 生成360度全景图和VR内容
- **材质系统**: 支持多种材质和光照效果

### 🛠️ 开发工具
- **代码分析**: ESLint静态代码检查
- **图表生成**: Mermaid流程图和架构图
- **PDF生成**: 动态PDF文档创建


## 📚 API文档

### 机器学习推理 API

#### 图像分类
```http
POST /tensorflow-js/classify-image
Content-Type: multipart/form-data

image: [图像文件]
modelName: "mobilenet" (可选)
```

#### 文本预测
```http
POST /tensorflow-js/predict-text
Content-Type: application/json

{
  "text": "要分析的文本",
  "maxLength": 100
}
```

#### 对象检测
```http
POST /tensorflow-js/detect-objects
Content-Type: multipart/form-data

image: [图像文件]
modelName: "coco-ssd" (可选)
threshold: 0.5 (可选)
```

### 图像/视频处理 API

#### 图像处理
```http
POST /opencv-ffmpeg/process-image
Content-Type: multipart/form-data

image: [图像文件]
operations: [
  {"type": "blur", "kernelSize": 15},
  {"type": "edge_detection", "threshold1": 100, "threshold2": 200}
]
```

#### 视频处理
```http
POST /opencv-ffmpeg/process-video
Content-Type: multipart/form-data

video: [视频文件]
operations: [
  {"type": "resize", "width": 720, "height": 480},
  {"type": "fps", "fps": 30}
]
outputFormat: "mp4"
```

### 3D渲染 API

#### 场景渲染
```http
POST /three-js/render-scene
Content-Type: application/json

{
  "objects": [
    {"type": "box", "size": [1, 1, 1], "position": [0, 0, 0]}
  ],
  "lights": [
    {"type": "ambient", "color": 16777215, "intensity": 0.6}
  ],
  "camera": {"position": [0, 0, 5]}
}
```

## 💻 SDK使用示例

### JavaScript SDK

```javascript
// 初始化客户端
const api = new AllBeApi();

// 图像分类
const imageFile = document.getElementById('imageInput').files[0];
const result = await api.tensorflowJs.classifyImage(imageFile, {
  modelName: 'mobilenet'
});
console.log('分类结果:', result);

// 图像处理
const operations = [
  { type: 'blur', kernelSize: 15 },
  { type: 'edge_detection', threshold1: 100, threshold2: 200 }
];
const processedImage = await api.opencvFfmpeg.processImage(imageFile, operations);

// 3D场景渲染
const sceneConfig = {
  objects: [
    { type: 'box', size: [1, 1, 1], position: [0, 0, 0] }
  ],
  lights: [
    { type: 'ambient', color: 0x404040, intensity: 0.6 }
  ]
};
const renderResult = await api.threeJs.renderScene(sceneConfig);
```

### Python SDK

```python
from allbeapi import AllBeApi

# 初始化客户端
api = AllBeApi()

# 图像分类
result = api.tensorflow_js.classify_image(
    'path/to/image.jpg',
    {'modelName': 'mobilenet'}
)
print('分类结果:', result)

# 图像处理
operations = [
    {"type": "blur", "kernelSize": 15},
    {"type": "edge_detection", "threshold1": 100, "threshold2": 200}
]
processed_image = api.opencv_ffmpeg.process_image('image.jpg', operations)

# 保存处理后的图像
with open('processed.jpg', 'wb') as f:
    f.write(processed_image)

# 3D场景渲染
scene_config = {
    'objects': [
        {'type': 'box', 'size': [1, 1, 1], 'position': [0, 0, 0]}
    ],
    'lights': [
        {'type': 'ambient', 'color': 0x404040, 'intensity': 0.6}
    ]
}
render_result = api.three_js.render_scene(scene_config)
```

## 🎯 使用场景

### IoT设备
- **智能摄像头**: 云端图像识别和分析
- **传感器数据**: 机器学习预测和异常检测
- **边缘计算**: 减轻设备计算负担

### 嵌入式系统
- **工业自动化**: 实时图像检测和质量控制
- **医疗设备**: 医学图像分析和诊断辅助
- **机器人**: 计算机视觉和路径规划

### 移动应用
- **AR/VR应用**: 3D内容生成和渲染
- **图像编辑**: 专业级图像处理功能
- **AI助手**: 智能文本分析和理解



## 📊 监控和日志

- **健康检查**: `/health` 端点监控所有服务状态
- **性能指标**: 请求时间、内存使用、错误率
- **详细日志**: 结构化日志记录，支持ELK堆栈
- **告警系统**: 自动故障检测和通知

## 🤝 贡献指南

1. Fork项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建Pull Request

## 📄 许可证

本项目采用MIT许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。


---

**让每个设备都拥有AI的力量！** 🚀
