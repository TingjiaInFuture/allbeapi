# 开源库API化平台 - 网站地图

## 🌐 网站结构

### 主站点
- **主页**: [https://res.allbeapi.top/](https://res.allbeapi.top/)
  - 平台介绍和所有API服务展示
  - 海洋主题的交互式界面

---

## 🔧 API 服务分类

### 📝 文本处理类

#### Marked API - Markdown转HTML
- **基础端点**: `/marked`
- **主要功能**: 
  - `POST /marked/render` - 将Markdown文本转换为HTML

#### Prettier API - 代码格式化
- **基础端点**: `/prettier`
- **主要功能**:
  - `POST /prettier/format` - 格式化代码
  - `POST /prettier/check` - 检查代码格式
  - `POST /prettier/batch` - 批量格式化
  - `GET /prettier/parsers` - 获取支持的解析器
  - `GET /prettier/options` - 获取配置选项
  - `GET /prettier/health` - 健康检查
  - `GET /prettier/info` - API信息

#### Pygments API - 代码高亮
- **基础端点**: `/pygments`
- **主要功能**:
  - `POST /pygments/highlight` - 对代码进行语法高亮

#### Diff API - 文本比较
- **基础端点**: `/diff`
- **主要功能**:
  - `POST /diff/compare` - 比较两个文本的差异

---

### 🔍 数据解析类

#### Beautiful Soup API - HTML解析
- **基础端点**: `/beautifulsoup`
- **主要功能**:
  - `POST /beautifulsoup/parse` - 解析HTML内容
  - `POST /beautifulsoup/extract` - 提取特定元素
  - `POST /beautifulsoup/links` - 提取所有链接
  - `POST /beautifulsoup/images` - 提取所有图片
  - `POST /beautifulsoup/clean` - 清理HTML内容
  - `POST /beautifulsoup/fetch` - 获取网页并解析
  - `GET /beautifulsoup/health` - 健康检查

#### CSV Parser API - CSV解析
- **基础端点**: `/csv-parser`
- **主要功能**:
  - `POST /csv-parser/parse` - 将CSV转换为JSON

---

### 🛡️ 安全验证类

#### Sanitize HTML API - HTML清理
- **基础端点**: `/sanitize-html`
- **主要功能**:
  - `POST /sanitize-html` - 清理HTML内容，防止XSS攻击

#### Ajv API - JSON Schema验证
- **基础端点**: `/ajv`
- **主要功能**:
  - `POST /ajv/validate` - 验证JSON数据是否符合Schema

#### ESLint API - 代码质量检查
- **基础端点**: `/eslint`
- **主要功能**:
  - `POST /eslint/lint` - 对JavaScript/TypeScript代码进行静态分析

---

### 🎨 内容生成类

#### Python QR Code API - 二维码生成
- **基础端点**: `/python-qrcode`
- **主要功能**:
  - `POST /python-qrcode/generate-qrcode` - 生成二维码图像

#### Mermaid CLI API - 图表生成
- **基础端点**: `/mermaid-cli`
- **主要功能**:
  - `POST /mermaid-cli/generate-diagram` - 从文本定义生成图表

#### PDFKit API - PDF生成
- **基础端点**: `/pdfkit`
- **主要功能**:
  - `POST /pdfkit/generate` - 生成PDF文档

#### Pillow API - 图像处理
- **基础端点**: `/pillow`
- **主要功能**:
  - `POST /pillow/process` - 处理和编辑图像

---

## 📊 API 使用统计

### 按功能分类统计
- **文本处理**: 4个API服务
- **数据解析**: 2个API服务  
- **安全验证**: 3个API服务
- **内容生成**: 4个API服务

### 总计
- **API服务总数**: 13个
- **API端点总数**: 25+个
- **支持的编程语言**: JavaScript, Python, TypeScript, HTML, CSS, Markdown, JSON等

---

## 🔗 快速导航

### 常用服务
1. [Markdown转换](https://res.allbeapi.top/marked/render) - 快速将Markdown转为HTML
2. [代码格式化](https://res.allbeapi.top/prettier/format) - 美化你的代码
3. [HTML解析](https://res.allbeapi.top/beautifulsoup/parse) - 提取网页数据
4. [二维码生成](https://res.allbeapi.top/python-qrcode/generate-qrcode) - 快速生成二维码
5. [代码高亮](https://res.allbeapi.top/pygments/highlight) - 让代码更美观

### 开发工具
1. [代码质量检查](https://res.allbeapi.top/eslint/lint) - ESLint静态分析
2. [JSON验证](https://res.allbeapi.top/ajv/validate) - Schema验证
3. [HTML清理](https://res.allbeapi.top/sanitize-html) - 安全过滤
4. [文本比较](https://res.allbeapi.top/diff/compare) - 查看差异

### 内容创建
1. [图表生成](https://res.allbeapi.top/mermaid-cli/generate-diagram) - 流程图、时序图等
2. [PDF生成](https://res.allbeapi.top/pdfkit/generate) - 创建PDF文档
3. [图像处理](https://res.allbeapi.top/pillow/process) - 编辑和处理图片
4. [CSV解析](https://res.allbeapi.top/csv-parser/parse) - 数据格式转换

---

## ⚠️ 重要提醒

本平台为开发者提供快速原型开发和测试所需的API服务。**对于生产环境，建议直接安装和使用相应的开源库**，以获得更好的性能和稳定性。

---

## 📞 联系方式

- **项目地址**: GitHub Repository
- **问题反馈**: Issues
- **功能建议**: Pull Requests

---

*最后更新时间: 2025年6月3日*
