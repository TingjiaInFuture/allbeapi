# AllBeAPI - AI-Enhanced Universal SDK

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![AI-Enhanced](https://img.shields.io/badge/AI-Enhanced-brightgreen.svg)](https://github.com/TingjiaInFuture/allbeapi)
[![Market Research](https://img.shields.io/badge/Market-Validated-blue.svg)](docs/ai-roadmap.html)

AllBeAPI is evolving from a versatile backend-as-a-service platform into a next-generation AI-enhanced API ecosystem. Starting with 13+ traditional library integrations, we're expanding to include cutting-edge AI capabilities for image processing, natural language understanding, document intelligence, smart code analysis, and intelligent web scraping.

## 🚀 Evolution Roadmap

### Current State (13+ Traditional APIs)
*   **Text Processing**: Markdown conversion, HTML parsing, code formatting
*   **Data Validation**: JSON schema validation, CSV parsing, text comparison  
*   **Media Generation**: QR codes, diagrams, PDFs, image manipulation
*   **Developer Tools**: Code linting, syntax highlighting, HTML sanitization

### AI-Enhanced Future (20+ Advanced APIs)
*   **🤖 AI Image Processing** (Q3 2025): Object recognition, face detection, smart enhancement, background removal
*   **🧠 Natural Language Processing** (Q4 2025): Sentiment analysis, text similarity, entity recognition, summarization
*   **📄 Document Intelligence** (Q4 2025): Smart format conversion, HTML-to-image, multi-document merging
*   **🔍 Smart Code Analysis** (Q1 2026): AI-powered vulnerability detection, intelligent refactoring suggestions
*   **🕷️ Intelligent Web Scraping** (Q1 2026): Adaptive extraction, anti-scraping evasion, real-time monitoring

## ✨ Features

### Current Platform Capabilities
*   **Comprehensive API Suite**: Access 13+ traditional development tools through a unified platform
*   **Easy Integration**: Official SDKs for JavaScript and Python for quick setup
*   **RESTful Access**: Direct HTTP access to all services for flexibility
*   **Open Source**: Community-driven and open for contributions
*   **Scalable Microservices**: Each functionality is a distinct service

### AI-Enhanced Features (Coming Soon)
*   **Computer Vision**: Advanced image analysis with object and face detection
*   **Natural Language Understanding**: Intelligent text processing and analysis
*   **Document Intelligence**: Smart format conversion and processing
*   **Code Intelligence**: AI-powered development assistance and security analysis
*   **Intelligent Automation**: Adaptive web scraping and data extraction

## 📊 Market-Validated Growth Strategy

Based on comprehensive market research, AllBeAPI is strategically positioned to capture significant opportunities:

*   **AI Image Processing Market**: 21% CAGR growth, projected $94.2B market by 2034
*   **Enterprise Document Automation**: High demand for intelligent format conversion
*   **AI Development Tools**: Growing need for AI-enhanced code analysis and security
*   **Training Data Collection**: 65%+ of organizations need intelligent scraping for AI models

##  архитектура

AllBeAPI operates on a microservice architecture. Client applications can interact with these services either through the dedicated SDKs (JavaScript/Python) which abstract the API calls, or by making direct HTTP requests to the respective service endpoints.

```
Client Applications
│
├─── SDKs (JavaScript, Python) ─────┐
│                                    │
└─── Direct HTTP/REST API Calls ───┐ │
                                   │ │
                                   ▼ ▼
                            AllBeAPI Gateway
                         (https://res.allbeapi.top)
                                   │
          ┌────────────────────────┼────────────────────────┐
          │                        │                        │
          ▼                        ▼                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────┐
│  Marked Service │    │   Pillow Service│    │  Prettier Service│    │   ... (Other│
│ (Markdown Proc.)│    │ (Image Proc.)   │    │ (Code Format)   │    │   Services) │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────┘
```

## 🛠️ Available Services

AllBeAPI provides the following services:

*   **Marked**: Converts Markdown text to HTML.
*   **BeautifulSoup**: Parses and extracts data from HTML/XML.
*   **Prettier**: Formats code for various languages (JavaScript, TypeScript, HTML, CSS, JSON, PHP, XML, Java, SQL).
*   **Pygments**: Provides syntax highlighting for a wide range of languages.
*   **PythonQRCode**: Generates QR codes from text or data.
*   **SanitizeHtml**: Cleans and sanitizes HTML input to prevent XSS attacks.
*   **Ajv**: Validates JSON data against JSON schemas.
*   **ESLint**: Lints JavaScript and TypeScript code to find and fix problems.
*   **Diff**: Compares text and highlights differences.
*   **CsvParser**: Parses CSV data.
*   **MermaidCli**: Generates diagrams and flowcharts from text using Mermaid syntax.
*   **PDFKit**: Creates and manipulates PDF documents.
*   **Pillow**: Performs various image processing tasks (resize, filters, format conversion, etc.).

## 🚀 Getting Started

You can interact with AllBeAPI services using our SDKs or by making direct HTTP requests. The base URL for all API services is `https://res.allbeapi.top`.

### SDKs

#### JavaScript SDK

**Installation:**

Download the SDK file:
```bash
curl -O https://raw.githubusercontent.com/TingjiaInFuture/allbeapi/main/SDK/JavaScript/allbeapi.js
# Or use wget
wget https://raw.githubusercontent.com/TingjiaInFuture/allbeapi/main/SDK/JavaScript/allbeapi.js
```

Or include it via CDN:
```html
<script src="https://cdn.jsdelivr.net/gh/TingjiaInFuture/allbeapi@3/SDK/JavaScript/allbeapi.js"></script>
```

**Usage:**
```javascript
// If using Node.js:
// const AllBeApi = require('./allbeapi.js'); // Assuming the SDK file is in the same directory

// In the browser (after including the script tag):
const api = new AllBeApi();

async function exampleUsage() {
    try {
        // Convert Markdown to HTML
        const markdownText = "# Hello AllBeAPI\nThis is **awesome**!";
        const htmlResult = await api.marked.render(markdownText);
        console.log('HTML Output:', htmlResult);

        // Generate a QR code
        const qrBlob = await api.pythonQrcode.generateQrcode("https://allbeapi.top");
        // You can then use this blob to display the QR code, e.g., by creating an object URL
        const qrImageUrl = URL.createObjectURL(qrBlob);
        console.log('QR Code Image URL:', qrImageUrl);
        // Example: <img src="qrImageUrl" alt="QR Code">

    } catch (error) {
        console.error("API Error:", error);
    }
}

exampleUsage();
```

#### Python SDK

**Installation:**

Download the SDK file:
```bash
curl -O https://raw.githubusercontent.com/TingjiaInFuture/allbeapi/main/SDK/Python/allbeapi.py
# Or use wget
wget https://raw.githubusercontent.com/TingjiaInFuture/allbeapi/main/SDK/Python/allbeapi.py
```

**Usage:**
```python
# Ensure allbeapi.py is in your Python path or the same directory
from allbeapi import AllBeApi

api = AllBeApi()

def example_usage():
    try:
        # Convert Markdown to HTML
        markdown_text = "# Hello AllBeAPI\nThis is **awesome**!"
        html_result = api.marked.render(markdown_text)
        print(f"HTML Output: {html_result}")

        # Generate a QR code
        # The Python SDK's generate_qrcode returns bytes of the image
        qr_image_bytes = api.python_qrcode.generate_qrcode(data="https://allbeapi.top", image_format="png")
        
        # You can save these bytes to a file
        with open("qrcode.png", "wb") as f:
            f.write(qr_image_bytes)
        print("QR Code saved to qrcode.png")

    except Exception as e:
        print(f"API Error: {e}")

if __name__ == '__main__':
    example_usage()
```

### Direct API Calls

You can also make direct HTTP requests to the API endpoints. For example, to convert Markdown using `curl`:

```bash
curl -X POST https://res.allbeapi.top/marked/render \
     -H "Content-Type: application/json" \
     -d '{ "markdown": "# Hello via cURL" }'
```

## 📚 Documentation

*   **General Documentation**: [docs/index.html](docs/index.html)
*   **API Reference**: [docs/api.html](docs/api.html) (Details all endpoints, parameters, and response formats)
*   **SDK Guide**: [docs/sdk.html](docs/sdk.html)
*   **Getting Started Guide**: [docs/getting-started.html](docs/getting-started.html)

## 🤝 Contributing

Contributions are welcome! Whether it's bug reports, feature requests, or code contributions, please feel free to:

1.  Fork the repository.
2.  Create your feature branch (`git checkout -b feature/AmazingFeature`).
3.  Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4.  Push to the branch (`git push origin feature/AmazingFeature`).
5.  Open a Pull Request.

We value community contributions and look forward to your input!

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Contact

For issues, feature requests, or questions, please open an issue on the GitHub repository.
