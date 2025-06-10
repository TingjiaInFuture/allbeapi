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
        this.mermaidCli = new MermaidCliAPI(this);
        this.pdfkit = new PDFKitAPI(this);
        this.tensorflowJs = new TensorFlowJsAPI(this);
        this.opencvFfmpeg = new OpenCVFfmpegAPI(this);
        this.threeJs = new ThreeJsAPI(this);
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

class TensorFlowJsAPI {
    constructor(client) { this.client = client; }
    
    /**
     * 图像分类 (Image classification using TensorFlow.js)
     * @param {File|Blob} imageFile - The image file to classify.
     * @param {object} [options] - Classification options.
     * @returns {Promise<object>}
     */
    async classifyImage(imageFile, options = {}) {
        const formData = new FormData();
        formData.append('image', imageFile);
        Object.keys(options).forEach(key => {
            formData.append(key, options[key]);
        });
        return this.client._request('POST', '/tensorflow-js/classify-image', null, formData);
    }
    
    /**
     * 文本预测 (Text prediction using TensorFlow.js)
     * @param {string} text - The input text.
     * @param {object} [options] - Prediction options.
     * @returns {Promise<object>}
     */
    async predictText(text, options = {}) {
        return this.client._request('POST', '/tensorflow-js/predict-text', null, { text, ...options });
    }
    
    /**
     * 自定义模型推理 (Custom model inference)
     * @param {File|object} data - Input data for inference.
     * @param {object} options - Model configuration.
     * @returns {Promise<object>}
     */
    async customInference(data, options = {}) {
        const formData = new FormData();
        if (data instanceof File || data instanceof Blob) {
            formData.append('data', data);
        } else {
            formData.append('data', JSON.stringify(data));
        }
        Object.keys(options).forEach(key => {
            formData.append(key, options[key]);
        });
        return this.client._request('POST', '/tensorflow-js/custom-inference', null, formData);
    }
    
    /**
     * 对象检测 (Object detection using TensorFlow.js)
     * @param {File|Blob} imageFile - The image file to analyze.
     * @param {object} options - Detection options.
     * @returns {Promise<object>}
     */
    async detectObjects(imageFile, options = {}) {
        const formData = new FormData();
        formData.append('image', imageFile);
        Object.keys(options).forEach(key => {
            formData.append(key, options[key]);
        });
        return this.client._request('POST', '/tensorflow-js/detect-objects', null, formData);
    }
    
    /**
     * 批量推理 (Batch inference)
     * @param {FileList|File[]} files - Array of files for batch processing.
     * @param {object} options - Inference options.
     * @returns {Promise<object>}
     */
    async batchInference(files, options = {}) {
        const formData = new FormData();
        Array.from(files).forEach((file, index) => {
            formData.append('files', file);
        });
        Object.keys(options).forEach(key => {
            formData.append(key, options[key]);
        });
        return this.client._request('POST', '/tensorflow-js/batch-inference', null, formData);
    }
    
    /**
     * 获取模型信息 (Get model information)
     * @param {string} modelName - The model name.
     * @returns {Promise<object>}
     */
    async getModelInfo(modelName) {
        return this.client._request('GET', `/tensorflow-js/model-info/${modelName}`);
    }
    
    /**
     * 获取内存状态 (Get memory status)
     * @returns {Promise<object>}
     */
    async getMemoryStatus() {
        return this.client._request('GET', '/tensorflow-js/memory-status');
    }
}

class OpenCVFfmpegAPI {
    constructor(client) { this.client = client; }
    
    /**
     * 高级图像处理 (Advanced image processing using OpenCV)
     * @param {File|Blob} imageFile - The image file to process.
     * @param {Array} operations - Array of operations to perform.
     * @returns {Promise<Blob>}
     */
    async processImage(imageFile, operations = []) {
        const formData = new FormData();
        formData.append('image', imageFile);
        formData.append('operations', JSON.stringify(operations));
        return this.client._request('POST', '/opencv-ffmpeg/process-image', null, formData);
    }
    
    /**
     * 高级视频处理 (Advanced video processing using FFmpeg)
     * @param {File|Blob} videoFile - The video file to process.
     * @param {Array} operations - Array of operations to perform.
     * @param {string} outputFormat - Output format (mp4, avi, mov, etc.).
     * @returns {Promise<object>}
     */
    async processVideo(videoFile, operations = [], outputFormat = 'mp4') {
        const formData = new FormData();
        formData.append('video', videoFile);
        formData.append('operations', JSON.stringify(operations));
        formData.append('outputFormat', outputFormat);
        return this.client._request('POST', '/opencv-ffmpeg/process-video', null, formData);
    }
    
    /**
     * 对象检测 (Object detection using OpenCV)
     * @param {File|Blob} imageFile - The image file to analyze.
     * @param {object} options - Detection options.
     * @returns {Promise<object>}
     */
    async detectObjects(imageFile, options = {}) {
        const formData = new FormData();
        formData.append('image', imageFile);
        Object.keys(options).forEach(key => {
            formData.append(key, options[key]);
        });
        return this.client._request('POST', '/opencv-ffmpeg/detect-objects', null, formData);
    }
    
    /**
     * 特征提取 (Feature extraction from images)
     * @param {File|Blob} imageFile - The image file to analyze.
     * @param {object} options - Extraction options.
     * @returns {Promise<object>}
     */
    async extractFeatures(imageFile, options = {}) {
        const formData = new FormData();
        formData.append('image', imageFile);
        Object.keys(options).forEach(key => {
            formData.append(key, options[key]);
        });
        return this.client._request('POST', '/opencv-ffmpeg/extract-features', null, formData);
    }
    
    /**
     * 视频帧提取 (Extract frames from video)
     * @param {File|Blob} videoFile - The video file to process.
     * @param {object} options - Frame extraction options.
     * @returns {Promise<object>}
     */
    async videoToFrames(videoFile, options = {}) {
        const formData = new FormData();
        formData.append('video', videoFile);
        Object.keys(options).forEach(key => {
            formData.append(key, options[key]);
        });
        return this.client._request('POST', '/opencv-ffmpeg/video-to-frames', null, formData);
    }
}

class ThreeJsAPI {
    constructor(client) { this.client = client; }
    
    /**
     * 渲染3D场景 (Render 3D scene using Three.js)
     * @param {object} sceneConfig - Scene configuration.
     * @returns {Promise<object>}
     */
    async renderScene(sceneConfig) {
        return this.client._request('POST', '/three-js/render-scene', null, sceneConfig);
    }
    
    /**
     * 生成3D模型 (Generate 3D model)
     * @param {string} modelType - Type of model to generate.
     * @param {object} parameters - Model parameters.
     * @param {object} options - Additional options.
     * @returns {Promise<object>}
     */
    async generateModel(modelType, parameters = {}, options = {}) {
        return this.client._request('POST', '/three-js/generate-model', null, {
            modelType,
            parameters,
            ...options
        });
    }
    
    /**
     * 创建动画对象 (Create animated object)
     * @param {object} object - Object to animate.
     * @param {Array} animations - Animation definitions.
     * @param {object} options - Animation options.
     * @returns {Promise<object>}
     */
    async animateObject(object, animations = [], options = {}) {
        return this.client._request('POST', '/three-js/animate-object', null, {
            object,
            animations,
            ...options
        });
    }
    
    /**
     * 获取场景模板 (Get available scene templates)
     * @returns {Promise<object>}
     */
    async getSceneTemplates() {
        return this.client._request('GET', '/three-js/scene-templates');
    }
    
    /**
     * 渲染全景图 (Render panoramic/360 view)
     * @param {object} scene - Scene configuration.
     * @param {object} options - Rendering options.
     * @returns {Promise<object>}
     */
    async renderPanoramic(scene, options = {}) {
        return this.client._request('POST', '/three-js/render-panoramic', null, {
            scene,
            ...options
        });
    }
}

// Export the main class for Node.js environments or as a global for browsers.
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AllBeApi;
    module.exports.default = AllBeApi; // For ES6 default import
} else if (typeof window !== 'undefined') {
    window.AllBeApi = AllBeApi;
}

// 使用示例 (Usage Examples)
/*
// 初始化客户端
const api = new AllBeApi('https://res.allbeapi.top');

// 机器学习推理示例
const imageFile = document.getElementById('imageInput').files[0];
api.tensorflowJs.classifyImage(imageFile, { modelName: 'mobilenet' })
    .then(result => console.log('Classification:', result))
    .catch(error => console.error('Error:', error));

// 图像处理示例
const operations = [
    { type: 'blur', kernelSize: 15 },
    { type: 'edge_detection', threshold1: 100, threshold2: 200 }
];
api.opencvFfmpeg.processImage(imageFile, operations)
    .then(result => console.log('Processed image:', result))
    .catch(error => console.error('Error:', error));

// 3D渲染示例
const sceneConfig = {
    objects: [
        { type: 'box', size: [1, 1, 1], position: [0, 0, 0] },
        { type: 'sphere', radius: 0.5, position: [2, 0, 0] }
    ],
    lights: [
        { type: 'ambient', color: 0x404040, intensity: 0.6 },
        { type: 'directional', color: 0xffffff, intensity: 0.8, position: [10, 10, 5] }
    ],
    camera: { position: [0, 0, 5], target: [0, 0, 0] }
};
api.threeJs.renderScene(sceneConfig)
    .then(result => console.log('Rendered scene:', result))
    .catch(error => console.error('Error:', error));
*/
