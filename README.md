# 开源库API化平台 🌊

一个将优秀开源库转换为 API 服务的平台，让开发者无需安装和部署即可直接调用。

## 🌐 API 接入地址

**基础 URL**: `https://res.allbeapi.top`

所有 API 服务都通过此域名提供，支持 HTTPS 安全访问。

## ✨ 主要特性

- 🌊 **海洋主题界面** - 美观的深海蓝色渐变背景，API服务如木块般在海洋中漂浮
- 📱 **响应式设计** - 支持各种屏幕尺寸和设备
- 🎨 **丰富的动画效果** - 包括漂浮动画、水波纹效果、气泡动画等
- 🚀 **快速加载** - 优化的加载动画和渐进式内容展示
- 📖 **详细文档** - 每个API都有完整的使用说明和代码示例

## 🔧 目前支持的API服务

### 📝 Marked API
将 Markdown 文本转换为 HTML

**端点**: `POST https://res.allbeapi.top/marked/render`

```javascript
fetch('https://res.allbeapi.top/marked/render', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        markdown: "# 标题\n\n这是 **粗体** 文本。"
    })
})
.then(response => response.text())
.then(html => console.log(html));
```

### 🥄 Beautiful Soup API
强大的 HTML/XML 解析和数据提取工具

**主要端点**:
- `POST https://res.allbeapi.top/beautifulsoup/parse` - HTML解析
- `POST https://res.allbeapi.top/beautifulsoup/extract` - 元素提取
- `POST https://res.allbeapi.top/beautifulsoup/links` - 链接提取
- `POST https://res.allbeapi.top/beautifulsoup/images` - 图片提取
- `POST https://res.allbeapi.top/beautifulsoup/clean` - HTML清理

```python
import requests

response = requests.post('https://res.allbeapi.top/beautifulsoup/parse', json={
    "html": "<html><head><title>测试</title></head><body><p>内容</p></body></html>"
})
data = response.json()
print(f"标题: {data['title']}")
```


## ⚠️ 重要说明

本项目旨在为快速原型开发提供轻量的代码体验，以及基于网络的简易集成。

**对于生产环境，不建议使用 API 代替库的引入**，因为这可能会带来：
- 网络延迟问题
- 稳定性风险
- 安全性考虑

对于生产应用，请考虑直接安装和使用相应的开源库。

## 🛠️ 技术架构

### 前端
- **HTML5** - 语义化标签和现代Web标准
- **CSS3** - Flexbox布局、CSS Grid、动画和渐变
- **原生JavaScript** - ES6+语法，模块化设计

### 文件结构
```
├── index.html          # 主页面
├── styles.css          # 样式文件
├── script.js           # 交互脚本
├── marked/             # Marked API 服务
│   ├── index.js
│   └── package.json
├── beautifulsoup/      # Beautiful Soup API 服务
│   ├── app.py
│   └── requirements.txt
└── test/               # 测试文件
    ├── test_marked_api.py
    └── test_beautifulsoup_api.py
```

## 🚀 本地开发

1. 克隆项目
```bash
git clone <repository-url>
cd allbeapi
```

2. 打开主页
直接在浏览器中打开 `index.html` 文件即可查看效果。

3. 测试API服务
```bash
# 测试 Marked API
python test/test_marked_api.py

# 测试 Beautiful Soup API
python test/test_beautifulsoup_api.py
```

## 🤝 贡献指南

欢迎提交新的API服务或改进现有功能！

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 发起 Pull Request

## 📄 许可证

本项目采用开源许可证，详见 [LICENSE](LICENSE) 文件。

---

🌊 **让优秀的开源工具像海洋一样自由流动** 🌊
