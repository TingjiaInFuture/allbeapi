const express = require('express');
const tf = require('@tensorflow/tfjs-node');
const cors = require('cors');
const fs = require('fs');
const path = require('path');
const { v4: uuidv4 } = require('uuid');
const multer = require('multer');
const sharp = require('sharp');

const app = express();
const port = 3010;

app.use(cors());
app.use(express.json({ limit: '50mb' }));

// Configure multer for file uploads
const upload = multer({ 
    dest: 'uploads/',
    limits: { fileSize: 50 * 1024 * 1024 } // 50MB limit
});

// Ensure directories exist
const outputDir = path.join(__dirname, 'output');
const modelsDir = path.join(__dirname, 'models');
const uploadsDir = path.join(__dirname, 'uploads');

[outputDir, modelsDir, uploadsDir].forEach(dir => {
    if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
    }
});

// Cache for loaded models
const modelCache = new Map();

// Load a pre-trained model (cached)
async function loadModel(modelName, modelUrl) {
    if (modelCache.has(modelName)) {
        return modelCache.get(modelName);
    }
    
    try {
        let model;
        if (modelUrl.startsWith('http')) {
            model = await tf.loadLayersModel(modelUrl);
        } else {
            model = await tf.loadLayersModel(`file://${path.join(modelsDir, modelUrl)}`);
        }
        modelCache.set(modelName, model);
        return model;
    } catch (error) {
        throw new Error(`Failed to load model ${modelName}: ${error.message}`);
    }
}

// Image classification endpoint
app.post('/tensorflow-js/classify-image', upload.single('image'), async (req, res) => {
    try {
        const { modelName = 'mobilenet', modelUrl } = req.body;
        
        if (!req.file) {
            return res.status(400).json({ error: 'No image file provided' });
        }

        // Load MobileNet for image classification if no custom model provided
        let model;
        if (modelName === 'mobilenet' && !modelUrl) {
            model = await tf.loadLayersModel('https://tfhub.dev/google/tfjs-model/imagenet/mobilenet_v3_small_100_224/classification/5/default/1', { fromTFHub: true });
        } else {
            model = await loadModel(modelName, modelUrl);
        }

        // Process the image
        const imageBuffer = fs.readFileSync(req.file.path);
        const processedImage = await sharp(imageBuffer)
            .resize(224, 224)
            .raw()
            .toBuffer();

        // Convert to tensor
        const imageTensor = tf.tensor3d(new Uint8Array(processedImage), [224, 224, 3])
            .expandDims(0)
            .div(255.0);

        // Make prediction
        const predictions = await model.predict(imageTensor).data();
        
        // Clean up
        imageTensor.dispose();
        fs.unlinkSync(req.file.path);

        // Format results
        const results = Array.from(predictions).map((probability, index) => ({
            class: index,
            probability: probability,
            confidence: Math.round(probability * 100)
        })).sort((a, b) => b.probability - a.probability).slice(0, 5);

        res.json({
            success: true,
            predictions: results,
            modelUsed: modelName
        });

    } catch (error) {
        console.error('Image classification error:', error);
        if (req.file && fs.existsSync(req.file.path)) {
            fs.unlinkSync(req.file.path);
        }
        res.status(500).json({ 
            error: 'Failed to classify image', 
            details: error.message 
        });
    }
});

// Text prediction endpoint
app.post('/tensorflow-js/predict-text', async (req, res) => {
    try {
        const { text, modelName = 'universal-sentence-encoder', maxLength = 100 } = req.body;
        
        if (!text) {
            return res.status(400).json({ error: 'No text provided' });
        }

        // For demonstration, using a simple text analysis
        // In production, you would load actual text models
        const words = text.toLowerCase().split(/\s+/);
        const sentiment = calculateSentiment(words);
        const entities = extractEntities(text);
        const summary = generateSummary(text, maxLength);

        res.json({
            success: true,
            originalText: text,
            analysis: {
                wordCount: words.length,
                sentiment: sentiment,
                entities: entities,
                summary: summary,
                language: detectLanguage(text)
            },
            modelUsed: modelName,
            timestamp: new Date().toISOString()
        });

    } catch (error) {
        console.error('Text prediction error:', error);
        res.status(500).json({ 
            error: 'Text prediction failed', 
            details: error.message 
        });
    }
});

// Custom model inference endpoint
app.post('/tensorflow-js/custom-inference', upload.single('data'), async (req, res) => {
    try {
        const { modelName, modelUrl, inputShape, outputFormat = 'json' } = req.body;
        
        if (!modelName && !modelUrl) {
            return res.status(400).json({ error: 'Model name or URL required' });
        }

        let model;
        if (modelUrl) {
            model = await loadModel(modelName || 'custom', modelUrl);
        } else if (modelCache.has(modelName)) {
            model = modelCache.get(modelName);
        } else {
            return res.status(404).json({ error: 'Model not found' });
        }

        let inputData;
        
        // Handle different input types
        if (req.file) {
            // File input
            const fileBuffer = fs.readFileSync(req.file.path);
            if (req.file.mimetype.startsWith('image/')) {
                inputData = await preprocessImage(fileBuffer, inputShape);
            } else {
                inputData = tf.tensor(JSON.parse(fileBuffer.toString()));
            }
            fs.unlinkSync(req.file.path);
        } else if (req.body.data) {
            // JSON input
            inputData = tf.tensor(JSON.parse(req.body.data));
        } else {
            return res.status(400).json({ error: 'No input data provided' });
        }

        // Run inference
        const startTime = Date.now();
        const prediction = await model.predict(inputData);
        const inferenceTime = Date.now() - startTime;
        
        const results = await prediction.data();
        
        // Clean up tensors
        inputData.dispose();
        prediction.dispose();

        res.json({
            success: true,
            results: Array.from(results),
            shape: prediction.shape,
            inferenceTime: `${inferenceTime}ms`,
            modelInfo: {
                name: modelName,
                inputShape: model.inputs[0].shape,
                outputShape: model.outputs[0].shape
            },
            memoryUsage: tf.memory()
        });

    } catch (error) {
        console.error('Custom inference error:', error);
        res.status(500).json({ 
            error: 'Custom inference failed', 
            details: error.message 
        });
    }
});

// Object detection endpoint
app.post('/tensorflow-js/detect-objects', upload.single('image'), async (req, res) => {
    try {
        const { modelName = 'coco-ssd', threshold = 0.5 } = req.body;
        
        if (!req.file) {
            return res.status(400).json({ error: 'No image file provided' });
        }

        // Load object detection model (COCO-SSD for demo)
        let model;
        try {
            model = await loadModel(modelName, 'https://tfhub.dev/tensorflow/tfjs-model/ssd_mobilenet_v2/1/default/1');
        } catch (error) {
            return res.status(500).json({ error: 'Failed to load object detection model' });
        }

        // Process the image
        const imageBuffer = fs.readFileSync(req.file.path);
        const processedImage = await sharp(imageBuffer)
            .resize(300, 300)
            .raw()
            .toBuffer();

        const imageTensor = tf.tensor3d(new Uint8Array(processedImage), [300, 300, 3])
            .expandDims(0)
            .div(255.0);

        // Run object detection
        const predictions = await model.executeAsync(imageTensor);
        
        // Process detection results
        const detections = await processDetections(predictions, threshold);
        
        // Clean up
        imageTensor.dispose();
        predictions.forEach(tensor => tensor.dispose());
        fs.unlinkSync(req.file.path);

        res.json({
            success: true,
            detections: detections,
            imageSize: { width: 300, height: 300 },
            threshold: threshold,
            modelUsed: modelName,
            processingTime: Date.now()
        });

    } catch (error) {
        console.error('Object detection error:', error);
        res.status(500).json({ 
            error: 'Object detection failed', 
            details: error.message 
        });
    }
});

// Batch inference endpoint
app.post('/tensorflow-js/batch-inference', upload.array('files', 10), async (req, res) => {
    try {
        const { modelName, operation = 'classify' } = req.body;
        
        if (!req.files || req.files.length === 0) {
            return res.status(400).json({ error: 'No files provided' });
        }

        if (!modelCache.has(modelName)) {
            return res.status(404).json({ error: 'Model not found' });
        }

        const model = modelCache.get(modelName);
        const results = [];

        for (const file of req.files) {
            try {
                const fileBuffer = fs.readFileSync(file.path);
                let inputTensor;

                if (file.mimetype.startsWith('image/')) {
                    inputTensor = await preprocessImage(fileBuffer);
                } else {
                    // Handle other file types
                    inputTensor = tf.tensor(JSON.parse(fileBuffer.toString()));
                }

                const prediction = await model.predict(inputTensor);
                const predictionData = await prediction.data();

                results.push({
                    filename: file.originalname,
                    results: Array.from(predictionData),
                    shape: prediction.shape
                });

                // Clean up
                inputTensor.dispose();
                prediction.dispose();
                fs.unlinkSync(file.path);

            } catch (fileError) {
                results.push({
                    filename: file.originalname,
                    error: fileError.message
                });
                if (fs.existsSync(file.path)) {
                    fs.unlinkSync(file.path);
                }
            }
        }

        res.json({
            success: true,
            batchResults: results,
            processedFiles: req.files.length,
            successfulInferences: results.filter(r => !r.error).length,
            memoryUsage: tf.memory()
        });

    } catch (error) {
        console.error('Batch inference error:', error);
        res.status(500).json({ 
            error: 'Batch inference failed', 
            details: error.message 
        });
    }
});

// Health check endpoint
app.get('/health', (req, res) => {
    res.json({
        status: 'healthy',
        service: 'tensorflow-js',
        version: tf.version.tfjs,
        memory: tf.memory(),
        loadedModels: Array.from(modelCache.keys()),
        timestamp: new Date().toISOString()
    });
});

// Helper functions
async function preprocessImage(imageBuffer, targetShape = [224, 224, 3]) {
    const processedImage = await sharp(imageBuffer)
        .resize(targetShape[0], targetShape[1])
        .raw()
        .toBuffer();

    return tf.tensor3d(new Uint8Array(processedImage), targetShape)
        .expandDims(0)
        .div(255.0);
}

function calculateSentiment(words) {
    // Simple sentiment analysis (in production, use actual sentiment models)
    const positiveWords = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'love', 'like'];
    const negativeWords = ['bad', 'terrible', 'awful', 'hate', 'dislike', 'horrible', 'worst'];
    
    let score = 0;
    words.forEach(word => {
        if (positiveWords.includes(word)) score++;
        if (negativeWords.includes(word)) score--;
    });
    
    if (score > 0) return { label: 'positive', confidence: Math.min(score / words.length * 10, 1) };
    if (score < 0) return { label: 'negative', confidence: Math.min(Math.abs(score) / words.length * 10, 1) };
    return { label: 'neutral', confidence: 0.5 };
}

function extractEntities(text) {
    // Simple entity extraction (in production, use NLP models)
    const emailRegex = /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g;
    const urlRegex = /https?:\/\/[^\s]+/g;
    const phoneRegex = /\b\d{3}-\d{3}-\d{4}\b/g;
    
    return {
        emails: text.match(emailRegex) || [],
        urls: text.match(urlRegex) || [],
        phones: text.match(phoneRegex) || []
    };
}

function generateSummary(text, maxLength) {
    // Simple summarization (in production, use summarization models)
    const sentences = text.split(/[.!?]+/).filter(s => s.trim().length > 0);
    if (sentences.length <= 2) return text;
    
    return sentences.slice(0, 2).join('. ') + '.';
}

function detectLanguage(text) {
    // Simple language detection (in production, use language detection models)
    const commonWords = {
        en: ['the', 'and', 'is', 'in', 'to', 'of', 'a', 'that', 'it', 'with'],
        es: ['el', 'la', 'de', 'que', 'y', 'en', 'un', 'es', 'se', 'no'],
        fr: ['le', 'la', 'les', 'de', 'et', 'à', 'un', 'il', 'être', 'et'],
        zh: ['的', '一', '是', '在', '不', '了', '有', '和', '人', '这']
    };
    
    const words = text.toLowerCase().split(/\s+/);
    let maxMatches = 0;
    let detectedLang = 'unknown';
    
    Object.entries(commonWords).forEach(([lang, langWords]) => {
        const matches = words.filter(word => langWords.includes(word)).length;
        if (matches > maxMatches) {
            maxMatches = matches;
            detectedLang = lang;
        }
    });
    
    return detectedLang;
}

async function processDetections(predictions, threshold) {
    // Process object detection results
    const [boxes, scores, classes] = predictions;
    const boxesData = await boxes.data();
    const scoresData = await scores.data();
    const classesData = await classes.data();
    
    const detections = [];
    for (let i = 0; i < scoresData.length; i++) {
        if (scoresData[i] > threshold) {
            detections.push({
                class: classesData[i],
                confidence: scoresData[i],
                bbox: [
                    boxesData[i * 4],     // y1
                    boxesData[i * 4 + 1], // x1
                    boxesData[i * 4 + 2], // y2
                    boxesData[i * 4 + 3]  // x2
                ]
            });
        }
    }
    
    return detections;
}

app.listen(port, () => {
    console.log(`TensorFlow.js API listening at http://localhost:${port}`);
    console.log(`TensorFlow.js version: ${tf.version.tfjs}`);
});
