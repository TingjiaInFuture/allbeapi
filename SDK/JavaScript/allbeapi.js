/**
 * AllBeAPI JavaScript SDK
 * Base URL: https://res.allbeapi.top
 *
 * This SDK provides a convenient way to interact with the AllBeAPI services.
 * It includes a main client class `AllBeApi` and specific classes for each API service.
 */

class AllBeApi {
    /**
     * Initializes a new instance of the AllBeApi client.
     * @param {string} [baseUrl='https://res.allbeapi.top'] - The base URL for the API.
     */
    constructor(baseUrl = 'https://res.allbeapi.top') {
        this.baseUrl = baseUrl;

        this.eslint = new ESLintAPI(this);
        this.mermaidCli = new MermaidCliAPI(this); // mermaid-cli -> mermaidCli
        this.pdfkit = new PDFKitAPI(this); // pdfkit -> pdfkit (using PDFKitAPI for consistency)
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
            path.includes('/pillow/process')) {
            return response.blob(); // Expected to be image/*
        } else if (path.includes('/pdfkit/generate')) {
            return response.blob(); // Expected to be application/pdf
        } else if (contentType && contentType.includes('application/json')) {
            return response.json();
        }
        
        return response.text(); // Fallback for other types or if content-type is missing
    }
}

class ESLintAPI {
    constructor(client) { this.client = client; }
    /**
     * 对JavaScript/TypeScript代码进行静态分析 (Lints JavaScript/TypeScript code using ESLint)
     * @param {string} code - The code to lint.
     * @param {object} [rules] - ESLint rules configuration.
     * @param {object} [options] - Additional ESLint options (e.g., parser, plugins).
     * @returns {Promise<object>}
     */
    async lint(code, rules = {}, options = {}) {
        return this.client._request('POST', '/eslint/lint', null, { code, rules, ...options });
    }
}

class MermaidCliAPI {
    constructor(client) { this.client = client; }
    /**
     * 从文本定义生成图表 (Generates a diagram from Mermaid text definition)
     * @param {string} mermaidDefinition - The Mermaid diagram definition.
     * @param {object} [options] - Options like theme, outputFormat (though API likely returns image).
     * @returns {Promise<Blob>} - The diagram image as a Blob.
     */
    async generateDiagram(mermaidDefinition, options = {}) {
        return this.client._request('POST', '/mermaid-cli/generate-diagram', null, { mermaid: mermaidDefinition, ...options });
    }
}

class PDFKitAPI { // Changed from PdfkitAPI to PDFKitAPI for consistency
    constructor(client) { this.client = client; }
    /**
     * 生成PDF文档 (Generates a PDF document using PDFKit)
     * @param {string} content - The HTML content or text for the PDF.
     * @param {object} [options] - PDF generation options (e.g., title, layout, metadata).
     * @returns {Promise<Blob>} - The PDF document as a Blob.
     */
    async generate(content, options = {}) {
        return this.client._request('POST', '/pdfkit/generate', null, { content, ...options });
    }
}

// Export the main class for Node.js environments or as a global for browsers.
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AllBeApi;
    module.exports.default = AllBeApi; // For ES6 default import
} else if (typeof window !== 'undefined') {
    window.AllBeApi = AllBeApi;
}
