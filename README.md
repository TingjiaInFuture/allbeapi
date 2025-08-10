# AllBeAPI - Minimal Utility Function Set

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Rapid Development](https://img.shields.io/badge/Rapid-Development-brightgreen.svg)](https://github.com/TingjiaInFuture/allbeapi)
[![Multi-Language](https://img.shields.io/badge/Python%20%7C%20JavaScript-supported-blue.svg)](https://github.com/TingjiaInFuture/allbeapi)

AllBeAPI is a cloud-based utility function set for rapid development. Call ready-to-use tools like Markdown-to-HTML, QR code generation, and image format conversion — all without installing extra libraries. Works in Python and JavaScript out of the box.

## ✨ Key Features

AllBeAPI helps developers complete prototypes and experiments in minimal time by providing:

* **No Heavy Dependencies**: Access powerful utilities without installing and managing multiple libraries
* **Unified API Calls**: Consistent interface across all functions - learn once, use everywhere  
* **Multi-Language Support**: Official SDKs for Python and JavaScript with identical functionality
* **Instant Integration**: Copy one file, start coding immediately
* **Rapid Prototyping**: Focus on your logic, not library setup and configuration

### Current Utility Functions (13+ Tools)
* **Text Processing**: Markdown-to-HTML conversion, syntax highlighting, code formatting
* **Data Handling**: JSON schema validation, CSV parsing, text comparison  
* **Content Generation**: QR codes, diagrams, PDFs, image processing
* **Developer Tools**: Code linting, HTML sanitization, format conversion

## 🏗️ Architecture

AllBeAPI operates on a simple microservice architecture. Client applications can interact with these services either through the dedicated SDKs (JavaScript/Python) or by making direct HTTP requests to the respective service endpoints.

```
Your Application
│
├─── SDKs (JavaScript, Python) ─────┐
│                                   │
└─── Direct HTTP/REST API Calls ───┐│
                                   ▼▼
                          AllBeAPI Gateway
                       (https://res.allbeapi.top)
                                   │
          ┌────────────────────────┼────────────────────────┐
          │                       │                        │
          ▼                       ▼                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────┐
│ Markdown Service│    │  Image Service  │    │ Code Formatting │    │   ... (13+  │
│ (HTML Rendering)│    │ (QR, Resize)    │    │ (Prettier, Lint)│    │  Services)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────┘
```

## 🛠️ Available Services

AllBeAPI provides these ready-to-use utility functions:

*   **Marked**: Converts Markdown text to HTML
*   **BeautifulSoup**: Parses and extracts data from HTML/XML
*   **Prettier**: Formats code for various languages (JavaScript, TypeScript, HTML, CSS, JSON, PHP, XML, Java, SQL)
*   **Pygments**: Provides syntax highlighting for 500+ programming languages
*   **PythonQRCode**: Generates QR codes from text or URLs
*   **SanitizeHtml**: Cleans and sanitizes HTML input to prevent XSS attacks
*   **Ajv**: Validates JSON data against JSON schemas
*   **ESLint**: Lints JavaScript and TypeScript code to find and fix problems
*   **Diff**: Compares text and highlights differences
*   **CsvParser**: Parses CSV data into structured format
*   **MermaidCli**: Generates diagrams and flowcharts from text using Mermaid syntax
*   **PDFKit**: Creates PDF documents from text and data
*   **Pillow**: Performs image processing tasks (resize, filters, format conversion)

## 🚀 Quick Start

Get started with AllBeAPI in under 60 seconds. All you need is to download one SDK file - no package managers, no dependency hell.

### JavaScript SDK

**Installation:**
```bash
# Download the SDK
curl -O https://raw.githubusercontent.com/TingjiaInFuture/allbeapi/main/SDK/JavaScript/allbeapi.js

# Or use in browser via CDN
# <script src="https://cdn.jsdelivr.net/gh/TingjiaInFuture/allbeapi@3/SDK/JavaScript/allbeapi.js"></script>
```

**Usage:**
```javascript
const api = new AllBeApi();

// Convert Markdown to HTML
const html = await api.marked.render("# Hello AllBeAPI\nThis is **awesome**!");
console.log(html);

// Generate a QR code
const qrBlob = await api.pythonQrcode.generateQrcode("https://allbeapi.top");
const qrImageUrl = URL.createObjectURL(qrBlob);
// Now use qrImageUrl in an <img> tag
```

### Python SDK

**Installation:**
```bash
# Download the SDK  
curl -O https://raw.githubusercontent.com/TingjiaInFuture/allbeapi/main/SDK/Python/allbeapi.py
```

**Usage:**
```python
from allbeapi import AllBeApi

api = AllBeApi()

# Convert Markdown to HTML
html = api.marked.render("# Hello AllBeAPI\nThis is **awesome**!")
print(html)

# Generate a QR code and save to file
qr_bytes = api.python_qrcode.generate_qrcode("https://allbeapi.top")
with open("qrcode.png", "wb") as f:
    f.write(qr_bytes)
```

## 💡 Examples

### Practical Use Cases

**Rapid Prototyping Blog Engine:**
```python
# Python: Convert user content and generate preview
api = AllBeApi()
html = api.marked.render(user_markdown)
preview_pdf = api.pdfkit.generate(html)
```

**Quick Image Processing:**
```javascript
// JavaScript: Process uploaded images without installing PIL/Pillow
const processedImg = await api.pillow.process(imageBytes, ["resize:300,300", "convert:JPEG"]);
```

**Instant Code Formatting:**
```python
# Python: Format code without installing prettier locally
formatted = api.prettier.format(messy_js_code, "babel")
```

**Data Validation Pipeline:**
```javascript
// JavaScript: Validate and parse data in one go
const isValid = await api.ajv.validate(schema, data);
const parsed = await api.csvParser.parse(csvString);
```

### Direct API Access

For maximum flexibility, make direct HTTP requests:

```bash
# Convert Markdown to HTML
curl -X POST https://res.allbeapi.top/marked/render \
     -H "Content-Type: application/json" \
     -d '{"markdown": "# Hello via cURL"}'

# Generate QR code
curl -X POST https://res.allbeapi.top/python-qrcode/generate-qrcode \
     -H "Content-Type: application/json" \
     -d '{"data": "https://example.com"}' \
     --output qrcode.png

# Format JavaScript code
curl -X POST https://res.allbeapi.top/prettier/format \
     -H "Content-Type: application/json" \
     -d '{"code": "const x=1;", "parser": "babel"}'
```

## 📚 Documentation

*   **API Reference**: [docs/api.html](docs/api.html) - Complete endpoint documentation  
*   **SDK Guide**: [docs/sdk.html](docs/sdk.html) - Detailed SDK usage examples
*   **Getting Started**: [docs/getting-started.html](docs/getting-started.html) - Step-by-step tutorials

## 🤝 Contributing

We welcome contributions to expand our utility function set! Whether it's adding new integrations, improving documentation, or fixing bugs:

1.  Fork the repository
2.  Create your feature branch (`git checkout -b feature/NewUtility`)
3.  Commit your changes (`git commit -m 'Add NewUtility integration'`)
4.  Push to the branch (`git push origin feature/NewUtility`)
5.  Open a Pull Request

Help us build the most comprehensive lightweight utility platform for developers!

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Contact

For questions, feature requests, or issues, please open an issue on GitHub.
