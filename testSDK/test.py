from allbeapi import AllBeApi

# 初始化客户端
api = AllBeApi()

# 图像分类
result = api.tensorflow_js.classify_image(
    'D:\\1\\fun\\allbeapi\\R-C.jpg',
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