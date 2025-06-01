# Prettier API Service

基于 [Prettier](https://prettier.io/) 的代码格式化 API 服务，支持多种编程语言的代码格式化。

## 🚀 快速开始

### 安装依赖

```bash
cd Prettier
npm install
```

### 启动服务

```bash
npm start
```

服务将在 `http://localhost:3001` 启动。

## 📚 API 文档

### 基础信息

- **基础 URL**: `http://localhost:3001` (本地) / `https://res.allbeapi.top` (生产)
- **Content-Type**: `application/json`
- **所有端点都支持 CORS**

### 主要端点

#### 1. 代码格式化

**POST** `/prettier/format`

格式化指定的代码。

**请求体**:
```json
{
  "code": "const x={a:1,b:2};",
  "parser": "babel",
  "options": {
    "singleQuote": true,
    "semi": false,
    "printWidth": 80
  }
}
```

**响应**:
```json
{
  "success": true,
  "formatted": "const x = { a: 1, b: 2 }\n",
  "parser": "babel",
  "options": { ... }
}
```

#### 2. 格式检查

**POST** `/prettier/check`

检查代码是否已按 Prettier 规范格式化。

**请求体**:
```json
{
  "code": "const x = { a: 1, b: 2 };",
  "parser": "babel"
}
```

**响应**:
```json
{
  "success": true,
  "isFormatted": true,
  "parser": "babel",
  "message": "Code is already formatted"
}
```

#### 3. 批量格式化

**POST** `/prettier/batch`

批量格式化多个文件。

**请求体**:
```json
{
  "files": [
    {
      "name": "script.js",
      "code": "const x={a:1};",
      "parser": "babel"
    },
    {
      "name": "style.css",
      "code": "body{margin:0;}",
      "parser": "css"
    }
  ],
  "options": {
    "singleQuote": true
  }
}
```

#### 4. 获取支持的解析器

**GET** `/prettier/parsers`

获取所有支持的文件类型和对应的解析器。

**响应**:
```json
{
  "success": true,
  "parsers": {
    "javascript": "babel",
    "js": "babel",
    "typescript": "typescript",
    "html": "html",
    "css": "css",
    "json": "json",
    ...
  }
}
```

#### 5. 获取配置选项

**GET** `/prettier/options`

获取可用的配置选项和默认值。

#### 6. 健康检查

**GET** `/prettier/health`

检查服务状态。

#### 7. API 信息

**GET** `/prettier/info`

获取 API 详细信息和使用示例。

## 🎨 支持的语言

| 语言/格式 | 解析器 | 文件扩展名 |
|-----------|--------|------------|
| JavaScript | babel | js, jsx |
| TypeScript | typescript | ts, tsx |
| JSON | json | json |
| HTML | html | html |
| CSS | css | css |
| SCSS | scss | scss |
| Less | less | less |
| Markdown | markdown | md, markdown |
| YAML | yaml | yaml, yml |
| XML | xml | xml |
| PHP | php | php |
| Java | java | java |
| SQL | sql | sql |

## ⚙️ 配置选项

| 选项 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| printWidth | number | 80 | 每行最大字符数 |
| tabWidth | number | 2 | 制表符宽度 |
| useTabs | boolean | false | 使用制表符而不是空格 |
| semi | boolean | true | 在语句末尾添加分号 |
| singleQuote | boolean | false | 使用单引号而不是双引号 |
| quoteProps | string | "as-needed" | 对象属性引号策略 |
| trailingComma | string | "es5" | 尾随逗号策略 |
| bracketSpacing | boolean | true | 对象字面量括号间距 |
| bracketSameLine | boolean | false | 多行元素的 > 是否放在最后一行 |
| arrowParens | string | "always" | 箭头函数参数括号 |
| endOfLine | string | "lf" | 行尾符类型 |

## 💡 使用示例

### JavaScript/Node.js

```javascript
const response = await fetch('http://localhost:3001/prettier/format', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    code: 'const x={a:1,b:2};',
    parser: 'babel',
    options: { singleQuote: true, semi: false }
  })
});

const data = await response.json();
console.log(data.formatted);
```

### Python

```python
import requests

response = requests.post('http://localhost:3001/prettier/format', json={
    'code': 'const x={a:1,b:2};',
    'parser': 'babel',
    'options': {'singleQuote': True, 'semi': False}
})

data = response.json()
print(data['formatted'])
```

### cURL

```bash
curl -X POST http://localhost:3001/prettier/format \
  -H "Content-Type: application/json" \
  -d '{
    "code": "const x={a:1,b:2};",
    "parser": "babel",
    "options": {"singleQuote": true, "semi": false}
  }'
```

## 🧪 测试

运行测试脚本：

```bash
# 确保服务正在运行
npm start

# 在另一个终端运行测试
cd ../test
python test_prettier_api.py
```

## 🔧 开发

### 开发模式

```bash
npm run dev
```

使用 nodemon 自动重启服务。

### 添加新的解析器

编辑 `index.js` 中的 `SUPPORTED_PARSERS` 对象：

```javascript
const SUPPORTED_PARSERS = {
  // 添加新的文件类型和解析器
  'vue': 'vue',
  'graphql': 'graphql'
};
```

然后安装相应的 Prettier 插件：

```bash
npm install prettier-plugin-vue
```

## 📦 Docker 支持

### 构建镜像

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 3001
CMD ["npm", "start"]
```

### 运行容器

```bash
docker build -t prettier-api .
docker run -p 3001:3001 prettier-api
```

## ⚡ 性能优化

- 支持最大 10MB 的代码输入
- 自动错误处理和详细错误信息
- 支持批量处理以提高效率
- 内存优化的解析器选择

## 🐛 错误处理

API 返回详细的错误信息：

```json
{
  "error": "Code contains syntax errors",
  "details": "Unexpected token (1:10)",
  "code": "SYNTAX_ERROR"
}
```

常见错误代码：
- `INVALID_INPUT`: 输入参数无效
- `PARSER_REQUIRED`: 未指定解析器
- `UNSUPPORTED_PARSER`: 不支持的解析器
- `SYNTAX_ERROR`: 代码语法错误
- `FORMATTING_ERROR`: 格式化失败
- `INTERNAL_ERROR`: 内部服务器错误

## 📄 许可证

MIT License
