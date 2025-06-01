# 开源库API化平台ALLBEAPI 🌊

为优秀开源库提供免费 API 服务，让开发者无需安装和部署即可直接调用。

## 🌐 API 接入地址

**基础 URL**: `https://res.allbeapi.top`

所有 API 服务都通过此域名提供，支持 HTTPS 安全访问。


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

### 🎨 Prettier API
强大的代码格式化工具，支持多种编程语言

**主要端点**:
- `POST https://res.allbeapi.top/prettier/format` - 代码格式化
- `POST https://res.allbeapi.top/prettier/check` - 格式检查
- `POST https://res.allbeapi.top/prettier/batch` - 批量格式化
- `GET https://res.allbeapi.top/prettier/parsers` - 支持的解析器
- `GET https://res.allbeapi.top/prettier/options` - 配置选项

```javascript
fetch('https://res.allbeapi.top/prettier/format', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        code: 'const x={a:1,b:2};',
        parser: 'babel',
        options: { singleQuote: true, semi: false }
    })
})
.then(response => response.json())
.then(data => console.log(data.formatted));
```


## ⚠️ 重要说明

本项目旨在为快速原型开发提供轻量的代码体验，以及基于网络的简易集成。

**对于生产环境，不建议使用 API 代替库的引入**，因为这可能会带来：
- 网络延迟问题
- 稳定性风险
- 安全性考虑

对于生产应用，请考虑直接安装和使用相应的开源库。



## 🤝 贡献指南

欢迎提交新的API服务或改进现有功能！

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 发起 Pull Request

## 📄 许可证

本项目采用开源许可证，详见 [LICENSE](LICENSE) 文件。

---

🌊 **让优秀的开源工具像海水一样自由流动** 🌊
