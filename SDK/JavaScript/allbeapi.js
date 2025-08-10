/**
 * AllBeAPI JavaScript SDK - Minimal Utility Function Set
 * Base URL: https://res.allbeapi.top
 *
 * Rapid development toolkit for prototyping and experimentation.
 * Access ready-to-use functions without installing heavy dependencies.
 */

class AllBeApi {
    /**
     * Initializes a new instance of the AllBeApi client.
     * @param {string} [baseUrl='https://res.allbeapi.top'] - The base URL for the API.
     */
    constructor(baseUrl = 'https://res.allbeapi.top') {
        this.baseUrl = baseUrl;

        this.marked = new MarkedAPI(this);
        this.beautifulsoup = new BeautifulSoupAPI(this);
        this.prettier = new PrettierAPI(this);
        this.pygments = new PygmentsAPI(this);
        this.pythonQrcode = new PythonQRCodeAPI(this); // python-qrcode -> pythonQrcode
        this.sanitizeHtml = new SanitizeHtmlAPI(this); // sanitize-html -> sanitizeHtml
        this.ajv = new AjvAPI(this);
        this.eslint = new ESLintAPI(this);
        this.diff = new DiffAPI(this);
        this.csvParser = new CsvParserAPI(this); // csv-parser -> csvParser
        this.mermaidCli = new MermaidCliAPI(this); // mermaid-cli -> mermaidCli
        this.pdfkit = new PDFKitAPI(this); // pdfkit -> pdfkit (using PDFKitAPI for consistency)
        this.pillow = new PillowAPI(this);
    }

    /**
     * Internal method to make requests to the API.
     * @param {string} method - The HTTP method (e.g., 'GET', 'POST').
     * @param {string} path - The API endpoint path.
     * @param {object} [queryParams=null] - Query parameters for GET requests.
     * @param {object} [body=null] - The request body for POST/PUT requests.
     * @returns {Promise<any>} - The response from the API.
     * @private
     */
    async _request(method, path, queryParams = null, body = null) {
        let url = `${this.baseUrl}${path}`;
        const options = {
            method: method,
            headers: {}
        };

        if (queryParams) {
            const params = new URLSearchParams();
            for (const key in queryParams) {
                if (queryParams.hasOwnProperty(key) && queryParams[key] !== undefined) {
                    params.append(key, queryParams[key]);
                }
            }
            if (params.toString()) {
                 url = `${url}?${params}`;
            }
        }

        if (body) {
            if (body instanceof FormData) {
                options.body = body; // For file uploads or form data
            } else {
                options.headers['Content-Type'] = 'application/json';
                options.body = JSON.stringify(body);
            }
        }

        const response = await fetch(url, options);

        if (!response.ok) {
            const errorData = await response.text();
            throw new Error(`API request to ${method} ${url} failed with status ${response.status}: ${errorData}`);
        }

        const contentType = response.headers.get('content-type');

        // Handle non-JSON responses based on known endpoints
        if (path.includes('/python-qrcode/generate-qrcode') ||
            path.includes('/mermaid-cli/generate-diagram') ||
            path.includes('/pillow/process-image')) {
            return response.blob(); // Expected to be image/*
        } else if (path.includes('/pdfkit/generate-pdf')) {
            return response.blob(); // Expected to be application/pdf
        } else if (contentType && contentType.includes('application/json')) {
            return response.json();
        }
        
        return response.text(); // Fallback for other types or if content-type is missing
    }
}

class MarkedAPI {
    constructor(client) { this.client = client; }
    /**
     * 将 Markdown 文本转换为 HTML (Converts Markdown text to HTML)
     * @param {string} markdown - The Markdown content.
     * @returns {Promise<object>}
     */
    async render(markdown) {
        return this.client._request('POST', '/marked/render', null, { markdown });
    }
}

class BeautifulSoupAPI {
    constructor(client) { this.client = client; }
    /**
     * 解析HTML内容 (Parses HTML content)
     * @param {string} html - The HTML content to parse.
     * @param {string} [parser='html.parser'] - The parser to use.
     * @returns {Promise<object>}
     */
    async parse(html, parser = 'html.parser') {
        return this.client._request('POST', '/beautifulsoup/parse', null, { html, parser });
    }
    /**
     * 提取特定元素 (Extracts specific elements from HTML)
     * @param {string} html - The HTML content.
     * @param {string} selector - CSS selector to extract elements.
     * @param {string} [attribute=null] - Specific attribute to extract from elements.
     * @param {string} [parser='html.parser'] - The parser to use.
     * @returns {Promise<object>}
     */
    async extract(html, selector, attribute = null, parser = 'html.parser') {
        const payload = { html, selector, parser };
        if (attribute) {
            payload.attribute = attribute;
        }
        return this.client._request('POST', '/beautifulsoup/extract', null, payload);
    }
    /**
     * 提取所有链接 (Extracts all links from HTML)
     * @param {string} html - The HTML content.
     * @param {string} [base_url=null] - Base URL to resolve relative links.
     * @param {string} [parser='html.parser'] - The parser to use.
     * @returns {Promise<object>}
     */
    async links(html, base_url = null, parser = 'html.parser') {
        const payload = { html, parser };
        if (base_url) {
            payload.base_url = base_url;
        }
        return this.client._request('POST', '/beautifulsoup/links', null, payload);
    }
    /**
     * 提取所有图片 (Extracts all images from HTML)
     * @param {string} html - The HTML content.
     * @param {string} [base_url=null] - Base URL to resolve relative image paths.
     * @param {string} [parser='html.parser'] - The parser to use.
     * @returns {Promise<object>}
     */
    async images(html, base_url = null, parser = 'html.parser') {
        const payload = { html, parser };
        if (base_url) {
            payload.base_url = base_url;
        }
        return this.client._request('POST', '/beautifulsoup/images', null, payload);
    }
    /**
     * 清理HTML内容 (Cleans HTML content)
     * @param {string} html - The HTML content to clean.
     * @param {string[]} [remove_tags=[]] - List of tags to remove.
     * @param {string[]} [keep_only=[]] - List of tags to keep, removing others.
     * @param {boolean} [remove_comments=false] - Whether to remove comments.
     * @param {string} [parser='html.parser'] - The parser to use.
     * @returns {Promise<object>}
     */
    async clean(html, remove_tags = [], keep_only = [], remove_comments = false, parser = 'html.parser') {
        return this.client._request('POST', '/beautifulsoup/clean', null, { html, remove_tags, keep_only, remove_comments, parser });
    }
    /**
     * 获取网页并解析 (Fetches a webpage and parses its content)
     * @param {string} url - The URL of the webpage to fetch and parse.
     * @param {string} [parser='html.parser'] - The parser to use.
     * @returns {Promise<object>}
     */
    async fetch(url, parser = 'html.parser') {
        return this.client._request('POST', '/beautifulsoup/fetch', null, { url, parser });
    }
    /**
     * 健康检查 (Health check for BeautifulSoup API)
     * @returns {Promise<object>}
     */
    async health() {
        return this.client._request('GET', '/beautifulsoup/health');
    }
}

class PrettierAPI {
    constructor(client) { this.client = client; }
    /**
     * 格式化代码 (Formats code using Prettier)
     * @param {string} code - The code to format.
     * @param {string} parser - The parser to use (e.g., 'babel', 'typescript').
     * @param {object} [options] - Prettier options.
     * @returns {Promise<object>}
     */
    async format(code, parser, options = {}) {
        return this.client._request('POST', '/prettier/format', null, { code, parser, options });
    }
    /**
     * 检查代码格式 (Checks code formatting using Prettier)
     * @param {string} code - The code to check.
     * @param {string} parser - The parser to use.
     * @param {object} [options] - Prettier options.
     * @returns {Promise<object>}
     */
    async check(code, parser, options = {}) {
        return this.client._request('POST', '/prettier/check', null, { code, parser, options });
    }
    /**
     * 批量格式化 (Batch format multiple code snippets)
     * @param {Array<object>} files - Array of file objects, e.g., [{ name: 'file.js', code: '...' }].
     * @param {string} parser - The parser to use for all files.
     * @param {object} [options] - Prettier options.
     * @returns {Promise<object>}
     */
    async batch(files, parser, options = {}) { // Assuming structure based on typical batch operations
        // files should be an array of objects, e.g., [{ code: '...', language: 'javascript' (or parser: 'babel'), options: {} }]
        return this.client._request('POST', '/prettier/batch', null, { files, parser, options });
    }
    /**
     * 获取支持的解析器 (Gets available Prettier parsers)
     * @returns {Promise<object>}
     */
    async getParsers() {
        return this.client._request('GET', '/prettier/parsers');
    }
    /**
     * 获取配置选项 (Gets Prettier configuration options)
     * @returns {Promise<object>}
     */
    async getOptions() {
        return this.client._request('GET', '/prettier/options');
    }
    /**
     * 健康检查 (Health check for Prettier API)
     * @returns {Promise<object>}
     */
    async health() {
        return this.client._request('GET', '/prettier/health');
    }
    /**
     * API信息 (Get Prettier API information)
     * @returns {Promise<object>}
     */
    async getInfo() {
        return this.client._request('GET', '/prettier/info');
    }
}

class PygmentsAPI {
    constructor(client) { this.client = client; }
    /**
     * 对代码进行语法高亮 (Highlights code syntax using Pygments)
     * @param {string} code - The code to highlight.
     * @param {string} language - The language of the code.
     * @param {object} [options] - Additional Pygments options (e.g., formatter, style).
     * @returns {Promise<object>}
     */
    async highlight(code, language, style = 'default', formatter = 'html', options = {}) {
        return this.client._request('POST', '/pygments/highlight', null, { code, language, style, formatter, ...options });
    }
}

class PythonQRCodeAPI {
    constructor(client) { this.client = client; }
    /**
     * 生成二维码图像 (Generates a QR code image)
     * @param {string} data - The data to encode in the QR code.
     * @param {object} [options] - Options like size, box_size, border, fill_color, back_color.
     * @returns {Promise<Blob>} - The QR code image as a Blob.
     */
    async generateQrcode(data, options = {}) {
        return this.client._request('POST', '/python-qrcode/generate-qrcode', null, { data, ...options });
    }
}

class SanitizeHtmlAPI {
    constructor(client) { this.client = client; }
    /**
     * 清理HTML内容，防止XSS攻击 (Sanitizes HTML content to prevent XSS attacks)
     * @param {string} html_content - The HTML content to sanitize.
     * @param {object} [options] - Sanitization options.
     * @returns {Promise<object>}
     */
    async sanitize(html_content, options = {}) {
        // API endpoint is /sanitize-html/sanitize-html and expects 'html_content'
        return this.client._request('POST', '/sanitize-html/sanitize-html', null, { html_content, options });
    }
}

class AjvAPI {
    constructor(client) { this.client = client; }
    /**
     * 验证JSON数据是否符合Schema (Validates JSON data against a schema using Ajv)
     * @param {object} schema - The JSON schema.
     * @param {object} data - The JSON data to validate.
     * @returns {Promise<object>}
     */
    async validate(schema, data) {
        return this.client._request('POST', '/ajv/validate', null, { schema, data });
    }
}

class ESLintAPI {
    constructor(client) { this.client = client; }
    /**
     * 对JavaScript/TypeScript代码进行静态分析 (Lints JavaScript/TypeScript code using ESLint)
     * @param {string} code - The code to lint.
     * @param {string} language - 'javascript' or 'typescript'.
     * @param {boolean} [fix=false] - Whether to attempt to fix linting issues.
     * @param {object} [eslintOptions] - Additional ESLint options (currently not directly used by API, but kept for future).
     * @returns {Promise<object>}
     */
    async lint(code, language, fix = false, eslintOptions = {}) {
        // API endpoint is /eslint/lint and expects 'code', 'language', 'fix'
        return this.client._request('POST', '/eslint/lint', null, { code, language, fix });
    }
}

class DiffAPI {
    constructor(client) { this.client = client; }
    /**
     * 比较两个文本的差异 (Compares two texts and returns the differences)
     * @param {string} text1 - The first text.
     * @param {string} text2 - The second text.
     * @param {object} [options] - Diffing options.
     * @returns {Promise<object>}
     */
    async compare(text1, text2, options = {}) {
        return this.client._request('POST', '/diff/compare', null, { text1, text2, ...options });
    }
}

class CsvParserAPI {
    constructor(client) { this.client = client; }
    /**
     * 将CSV转换为JSON (Parses CSV data into JSON)
     * @param {string} csvData - The CSV data as a string.
     * @param {object} [options] - CSV parsing options (e.g., delimiter, headers).
     * @returns {Promise<object>}
     */
    async parse(csvData, options = {}) {
        return this.client._request('POST', '/csv-parser/parse', null, { csv_data: csvData, options: options });
    }
}

class MermaidCliAPI {
    constructor(client) { this.client = client; }
    /**
     * 从文本定义生成图表 (Generates a diagram from Mermaid text definition)
     * @param {string} definition - The Mermaid diagram definition.
     * @param {string} [format='svg'] - Output format ('svg' or 'png').
     * @param {object} [options] - Additional options (currently not directly used by API, but kept for future).
     * @returns {Promise<Blob>} - The diagram image as a Blob.
     */
    async generateDiagram(definition, format = 'svg', options = {}) {
        // API returns a JSON with filePath, then the file is served from that path.
        const response = await this.client._request('POST', '/mermaid-cli/generate-diagram', null, { definition, format, ...options });
        if (response && response.filePath) {
            // The _request method should handle fetching the blob directly if the path is absolute
            // or if it's a relative path from the base URL.
            // Assuming filePath is relative to the base API URL.
            return this.client._request('GET', response.filePath);
        }
        throw new Error('Failed to retrieve diagram file path from MermaidCliAPI');
    }
}

class PDFKitAPI { 
    constructor(client) { this.client = client; }
    /**
     * 生成PDF文档 (Generates a PDF document using PDFKit)
     * @param {string} text_content - The text content for the PDF.
     * @param {object} [options] - PDF generation options (currently not directly used by API, but kept for future).
     * @returns {Promise<Blob>} - The PDF document as a Blob.
     */
    async generate(text_content, options = {}) {
        // API returns a JSON with filePath, then the file is served from that path.
        const response = await this.client._request('POST', '/pdfkit/generate-pdf', null, { text_content, ...options });
        if (response && response.filePath) {
            return this.client._request('GET', response.filePath);
        }
        throw new Error('Failed to retrieve PDF file path from PDFKitAPI');
    }
}

class PillowAPI {
    constructor(client) { this.client = client; }
    /**
     * 处理和编辑图像 (Processes and edits images using Pillow)
     * @param {File} file - The image file to process.
     * @param {string[]} operations - Array of operation strings (e.g., ["resize:200,200", "grayscale"]).
     * @param {string} [output_format='PNG'] - The desired output format (e.g., 'PNG', 'JPEG').
     * @returns {Promise<Blob>} - The processed image as a Blob.
     */
    async process(file, operations, output_format = 'PNG') {
        const formData = new FormData();
        formData.append('file', file);
        // API expects 'operations' as multiple form fields.
        operations.forEach(op => formData.append('operations', op));
        formData.append('output_format', output_format);
        // API directly returns the processed image blob.
        return this.client._request('POST', '/pillow/process-image', null, formData);
    }
}

// Export the main class for Node.js environments or as a global for browsers.
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AllBeApi;
    module.exports.default = AllBeApi; // For ES6 default import
} else if (typeof window !== 'undefined') {
    window.AllBeApi = AllBeApi;
}
