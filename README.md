# 开源库API化平台ALLBEAPI 🌊

![API服务数量](https://img.shields.io/badge/API%E6%9C%8D%E5%8A%A1-13%E4%B8%AA-blue?style=flat-square)
![端点总数](https://img.shields.io/badge/%E7%AB%AF%E7%82%B9%E6%80%BB%E6%95%B0-25%E4%B8%AA-green?style=flat-square)
![平台状态](https://img.shields.io/badge/%E5%B9%B3%E5%8F%B0%E7%8A%B6%E6%80%81-%E5%9C%A8%E7%BA%BF-brightgreen?style=flat-square)
![最后更新](https://img.shields.io/badge/%E6%9C%80%E5%90%8E%E6%9B%B4%E6%96%B0-2025--06--04-orange?style=flat-square)
![许可证](https://img.shields.io/badge/%E8%AE%B8%E5%8F%AF%E8%AF%81-MIT-yellow?style=flat-square)
[![演示平台](https://img.shields.io/badge/%F0%9F%9A%80-%E5%9C%A8%E7%BA%BF%E6%BC%94%E7%A4%BA-ff69b4?style=flat-square)](https://res.allbeapi.top/demo.html)

![GitHub stars](https://img.shields.io/github/stars/yourusername/allbeapi?style=flat-square)
![GitHub forks](https://img.shields.io/github/forks/yourusername/allbeapi?style=flat-square)
![GitHub issues](https://img.shields.io/github/issues/yourusername/allbeapi?style=flat-square)
![GitHub pull requests](https://img.shields.io/github/issues-pr/yourusername/allbeapi?style=flat-square)
![Response Time](https://img.shields.io/badge/%E5%93%8D%E5%BA%94%E6%97%B6%E9%97%B4-%3C500ms-success?style=flat-square)
![Uptime](https://img.shields.io/badge/%E5%9C%A8%E7%BA%BF%E7%8E%87-99.9%25-brightgreen?style=flat-square)
![Security](https://img.shields.io/badge/%E5%AE%89%E5%85%A8%E6%80%A7-HTTPS-blue?style=flat-square)
![Free](https://img.shields.io/badge/%E4%BB%B7%E6%A0%BC-%E5%AE%8C%E5%85%A8%E5%85%8D%E8%B4%B9-success?style=flat-square)

> 为优秀开源库提供免费 API 服务，让开发者无需安装和部署即可直接调用

## 🌐 API 接入地址

**基础 URL**: `https://res.allbeapi.top`

所有 API 服务都通过此域名提供，支持 HTTPS 安全访问。

## 📊 平台统计

- 🚀 **API 总数**: 13个
- 🔗 **端点总数**: 25个
- 📅 **最后更新**: 2025年6月3日
- 🏷️ **服务分类**: 4大类

## 🔧 API 服务分类

### 📝 文本处理 (Text Processing)
文本转换、格式化、高亮等功能

### 📋 数据解析 (Data Parsing)  
HTML、CSV等数据格式的解析和提取

### 🛡️ 安全验证 (Security & Validation)
代码检查、数据验证、安全过滤等功能

### 🎨 内容生成 (Content Generation)
图片、PDF、图表等内容的生成

## 🚀 核心价值

1. **🚀 快速原型开发** - 无需安装配置，即开即用，适合教学和原型开发
2. **🌐 跨平台跨语言集成** - 统一HTTP接口，支持任何编程语言调用，省去引入整个库的开销
3. **🔄 统一管理库版本** - 自动升级到最新版本，无需手动维护依赖
4. **💻 IoT设备算力卸载** - 为资源受限设备提供云端计算能力

## 📖 API 使用指南

### 快速开始

所有API调用都使用相同的基础URL：`https://res.allbeapi.top`

**基础请求格式：**
```bash
curl -X POST https://res.allbeapi.top/{endpoint} \
  -H "Content-Type: application/json" \
  -d '{"param": "value"}'
```

### 📊 API 服务总览

| API服务 | 图标 | 描述 | 端点数 | 分类 |
|---------|------|------|--------|------|
| [Marked](#📝-marked-api) | 📝 | Markdown 转 HTML | 1 | 文本处理 |
| [Beautiful Soup](#🥄-beautiful-soup-api) | 🥄 | HTML 解析与提取 | 7 | 数据解析 |
| [Prettier](#🎨-prettier-api) | 🎨 | 代码格式化工具 | 7 | 文本处理 |
| [Pygments](#🌈-pygments-api) | 🌈 | 代码语法高亮 | 1 | 文本处理 |
| [Python QR Code](#📱-python-qr-code-api) | 📱 | 二维码生成 | 1 | 内容生成 |
| [Sanitize HTML](#🛡️-sanitize-html-api) | 🛡️ | HTML 清理 (XSS防护) | 1 | 安全验证 |
| [Ajv](#✅-ajv-api) | ✅ | JSON Schema 验证 | 1 | 安全验证 |
| [ESLint](#🔍-eslint-api) | 🔍 | JS/TS 静态分析 | 1 | 安全验证 |
| [Diff](#🔄-diff-api) | 🔄 | 文本内容比较 | 1 | 文本处理 |
| [CSV Parser](#📊-csv-parser-api) | 📊 | CSV 转 JSON | 1 | 数据解析 |
| [Mermaid CLI](#📈-mermaid-cli-api) | 📈 | 文本生成图表 | 1 | 内容生成 |
| [PDFKit](#📄-pdfkit-api) | 📄 | PDF 文档生成 | 1 | 内容生成 |
| [Pillow](#🖼️-pillow-api) | 🖼️ | 图像处理 | 1 | 内容生成 |

### 🚀 API 快速参考

#### 文本处理类 API

| API | 端点 | 方法 | 主要参数 | 响应类型 | 应用场景 |
|-----|------|------|----------|----------|----------|
| **Marked** | `/marked/render` | POST | `markdown` | JSON | 文档生成、博客系统 |
| **Prettier** | `/prettier/format` | POST | `code`, `parser` | JSON | 代码美化、CI/CD |
| **Pygments** | `/pygments/highlight` | POST | `code`, `language` | JSON | 代码展示、语法高亮 |
| **Diff** | `/diff/compare` | POST | `text1`, `text2` | JSON | 版本对比、文档比较 |

#### 数据解析类 API

| API | 端点 | 方法 | 主要参数 | 响应类型 | 应用场景 |
|-----|------|------|----------|----------|----------|
| **Beautiful Soup** | `/beautifulsoup/parse` | POST | `html` | JSON | 网页数据提取 |
| **Beautiful Soup** | `/beautifulsoup/links` | POST | `html` | JSON | 链接爬取、SEO分析 |
| **Beautiful Soup** | `/beautifulsoup/images` | POST | `html` | JSON | 图片资源收集 |
| **CSV Parser** | `/csv-parser/csv-to-json` | POST | `csv_data` | JSON | 数据导入、表格处理 |

#### 安全验证类 API

| API | 端点 | 方法 | 主要参数 | 响应类型 | 应用场景 |
|-----|------|------|----------|----------|----------|
| **Sanitize HTML** | `/sanitize-html` | POST | `html` | JSON | XSS防护、内容清理 |
| **Ajv** | `/ajv/validate` | POST | `schema`, `data` | JSON | 数据验证、API校验 |
| **ESLint** | `/eslint/lint` | POST | `code`, `rules` | JSON | 代码质量检查 |

#### 内容生成类 API

| API | 端点 | 方法 | 主要参数 | 响应类型 | 应用场景 |
|-----|------|------|----------|----------|----------|
| **Python QR Code** | `/python-qrcode/generate-qrcode` | POST | `data`, `box_size` | Image | 二维码生成、分享链接 |
| **Mermaid CLI** | `/mermaid-cli/generate-diagram` | POST | `mermaid` | Image | 流程图、架构图 |
| **PDFKit** | `/pdfkit/generate` | POST | `content`, `title` | PDF | 报告生成、文档导出 |
| **Pillow** | `/pillow/process` | POST | `image_url`, `operation` | Image | 图像处理、缩放裁剪 |

### 📝 Marked API
**Markdown 转 HTML**

| 端点 | 方法 | 描述 | 示例 |
|------|------|------|------|
| `/marked/render` | POST | 将 Markdown 文本转换为 HTML | [示例](#marked-示例) |

#### Marked 示例
```bash
curl -X POST https://res.allbeapi.top/marked/render \
  -H "Content-Type: application/json" \
  -d '{"markdown": "# Hello World\n\nThis is **bold** text."}'
```

### 🥄 Beautiful Soup API
**HTML 解析与提取**

| 端点 | 方法 | 描述 | 示例 |
|------|------|------|------|
| `/beautifulsoup/parse` | POST | 解析HTML内容 | [示例](#beautifulsoup-示例) |
| `/beautifulsoup/extract` | POST | 提取特定元素 | [示例](#beautifulsoup-示例) |
| `/beautifulsoup/links` | POST | 提取所有链接 | [示例](#beautifulsoup-示例) |
| `/beautifulsoup/images` | POST | 提取所有图片 | [示例](#beautifulsoup-示例) |
| `/beautifulsoup/clean` | POST | 清理HTML内容 | [示例](#beautifulsoup-示例) |
| `/beautifulsoup/fetch` | POST | 获取网页并解析 | [示例](#beautifulsoup-示例) |
| `/beautifulsoup/health` | GET | 健康检查 | [示例](#beautifulsoup-示例) |

#### Beautiful Soup 示例
```bash
# 解析HTML
curl -X POST https://res.allbeapi.top/beautifulsoup/parse \
  -H "Content-Type: application/json" \
  -d '{"html": "<div class=\"content\"><p>Hello World</p></div>"}'

# 提取链接
curl -X POST https://res.allbeapi.top/beautifulsoup/links \
  -H "Content-Type: application/json" \
  -d '{"html": "<a href=\"https://example.com\">Link</a>"}'
```

### 🎨 Prettier API
**代码格式化工具**

| 端点 | 方法 | 描述 | 示例 |
|------|------|------|------|
| `/prettier/format` | POST | 格式化代码 | [示例](#prettier-示例) |
| `/prettier/check` | POST | 检查代码格式 | [示例](#prettier-示例) |
| `/prettier/batch` | POST | 批量格式化 | [示例](#prettier-示例) |
| `/prettier/parsers` | GET | 获取支持的解析器 | [示例](#prettier-示例) |
| `/prettier/options` | GET | 获取配置选项 | [示例](#prettier-示例) |
| `/prettier/health` | GET | 健康检查 | [示例](#prettier-示例) |
| `/prettier/info` | GET | API信息 | [示例](#prettier-示例) |

#### Prettier 示例
```bash
# 格式化JavaScript代码
curl -X POST https://res.allbeapi.top/prettier/format \
  -H "Content-Type: application/json" \
  -d '{"code": "const x=1;function test(){return x;}", "parser": "babel"}'
```

### 🌈 Pygments API
**代码语法高亮**

| 端点 | 方法 | 描述 | 示例 |
|------|------|------|------|
| `/pygments/highlight` | POST | 对代码进行语法高亮 | [示例](#pygments-示例) |

#### Pygments 示例
```bash
curl -X POST https://res.allbeapi.top/pygments/highlight \
  -H "Content-Type: application/json" \
  -d '{"code": "print(\"Hello World\")", "language": "python"}'
```

### 📱 Python QR Code API
**二维码生成**

| 端点 | 方法 | 描述 | 示例 |
|------|------|------|------|
| `/python-qrcode/generate-qrcode` | POST | 生成二维码图像 | [示例](#qrcode-示例) |

#### QR Code 示例
```bash
curl -X POST https://res.allbeapi.top/python-qrcode/generate-qrcode \
  -H "Content-Type: application/json" \
  -d '{"data": "https://example.com", "size": 10}'
```

### 🛡️ Sanitize HTML API
**HTML 清理 (XSS防护)**

| 端点 | 方法 | 描述 | 示例 |
|------|------|------|------|
| `/sanitize-html` | POST | 清理HTML内容，防止XSS攻击 | [示例](#sanitize-示例) |

#### Sanitize HTML 示例
```bash
curl -X POST https://res.allbeapi.top/sanitize-html \
  -H "Content-Type: application/json" \
  -d '{"html": "<script>alert(\"xss\")</script><p>Safe content</p>"}'
```

### ✅ Ajv API
**JSON Schema 验证**

| 端点 | 方法 | 描述 | 示例 |
|------|------|------|------|
| `/ajv/validate` | POST | 验证JSON数据是否符合Schema | [示例](#ajv-示例) |

#### Ajv 示例
```bash
curl -X POST https://res.allbeapi.top/ajv/validate \
  -H "Content-Type: application/json" \
  -d '{"schema": {"type": "object", "properties": {"name": {"type": "string"}}}, "data": {"name": "John"}}'
```

### 🔍 ESLint API
**JS/TS 静态分析**

| 端点 | 方法 | 描述 | 示例 |
|------|------|------|------|
| `/eslint/lint` | POST | 对JavaScript/TypeScript代码进行静态分析 | [示例](#eslint-示例) |

#### ESLint 示例
```bash
curl -X POST https://res.allbeapi.top/eslint/lint \
  -H "Content-Type: application/json" \
  -d '{"code": "var x = 1;", "rules": {"no-var": "error"}}'
```

### 🔄 Diff API
**文本内容比较**

| 端点 | 方法 | 描述 | 示例 |
|------|------|------|------|
| `/diff/compare` | POST | 比较两个文本的差异 | [示例](#diff-示例) |

#### Diff 示例
```bash
curl -X POST https://res.allbeapi.top/diff/compare \
  -H "Content-Type: application/json" \
  -d '{"text1": "Hello World", "text2": "Hello Beautiful World"}'
```

### 📊 CSV Parser API
**CSV 转 JSON**

| 端点 | 方法 | 描述 | 示例 |
|------|------|------|------|
| `/csv-parser/csv-to-json` | POST | 将CSV转换为JSON | [示例](#csv-示例) |

#### CSV Parser 示例
```bash
curl -X POST https://res.allbeapi.top/csv-parser/csv-to-json \
  -H "Content-Type: application/json" \
  -d '{"csv_data": "name,age\nJohn,25\nJane,30"}'
```

### 📈 Mermaid CLI API
**文本生成图表**

| 端点 | 方法 | 描述 | 示例 |
|------|------|------|------|
| `/mermaid-cli/generate-diagram` | POST | 从文本定义生成图表 | [示例](#mermaid-示例) |

#### Mermaid 示例
```bash
curl -X POST https://res.allbeapi.top/mermaid-cli/generate-diagram \
  -H "Content-Type: application/json" \
  -d '{"mermaid": "graph TD\n    A[Start] --> B[Process]\n    B --> C[End]"}'
```

### 📄 PDFKit API
**PDF 文档生成**

| 端点 | 方法 | 描述 | 示例 |
|------|------|------|------|
| `/pdfkit/generate` | POST | 生成PDF文档 | [示例](#pdf-示例) |

#### PDFKit 示例
```bash
curl -X POST https://res.allbeapi.top/pdfkit/generate \
  -H "Content-Type: application/json" \
  -d '{"content": "Hello World", "title": "My Document"}'
```

### 🖼️ Pillow API
**图像处理**

| 端点 | 方法 | 描述 | 示例 |
|------|------|------|------|
| `/pillow/process` | POST | 处理和编辑图像 | [示例](#pillow-示例) |

#### Pillow 示例
```bash
curl -X POST https://res.allbeapi.top/pillow/process \
  -H "Content-Type: application/json" \
  -d '{"image_url": "https://example.com/image.jpg", "operation": "resize", "width": 200, "height": 200}'
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
