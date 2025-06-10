const express = require('express');
const cv = require('opencv4nodejs');
const ffmpeg = require('fluent-ffmpeg');
const cors = require('cors');
const fs = require('fs');
const path = require('path');
const { v4: uuidv4 } = require('uuid');
const multer = require('multer');

const app = express();
const port = 3011;

app.use(cors());
app.use(express.json({ limit: '100mb' }));

// Configure multer for file uploads
const upload = multer({ 
    dest: 'uploads/',
    limits: { fileSize: 100 * 1024 * 1024 } // 100MB limit
});

// Ensure directories exist
const outputDir = path.join(__dirname, 'output');
const uploadsDir = path.join(__dirname, 'uploads');

[outputDir, uploadsDir].forEach(dir => {
    if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
    }
});

// Advanced image processing with OpenCV
app.post('/opencv-ffmpeg/process-image', upload.single('image'), async (req, res) => {
    try {
        const { operations } = req.body;
        
        if (!req.file) {
            return res.status(400).json({ error: 'No image file provided' });
        }

        if (!operations) {
            return res.status(400).json({ error: 'No operations specified' });
        }

        let img = cv.imread(req.file.path);
        const operationsList = JSON.parse(operations);

        for (const op of operationsList) {
            switch (op.type) {
                case 'blur':
                    const kSize = new cv.Size(op.kernelSize || 15, op.kernelSize || 15);
                    img = img.gaussianBlur(kSize, op.sigmaX || 0, op.sigmaY || 0);
                    break;

                case 'edge_detection':
                    const gray = img.bgrToGray();
                    img = gray.canny(op.threshold1 || 100, op.threshold2 || 200);
                    break;

                case 'morphology':
                    const kernel = cv.getStructuringElement(cv.MORPH_RECT, new cv.Size(op.kernelSize || 5, op.kernelSize || 5));
                    const morphOp = op.operation || cv.MORPH_OPEN;
                    img = img.morphologyEx(morphOp, kernel);
                    break;

                case 'histogram_equalization':
                    if (img.channels === 3) {
                        const channels = img.split();
                        const equalizedChannels = channels.map(channel => channel.equalizeHist());
                        img = new cv.Mat(equalizedChannels).merge();
                    } else {
                        img = img.equalizeHist();
                    }
                    break;

                case 'contour_detection':
                    const grayImg = img.channels === 3 ? img.bgrToGray() : img;
                    const contours = grayImg.findContours(cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE);
                    img = img.drawContours(contours, -1, new cv.Vec3(0, 255, 0), 2);
                    break;

                case 'face_detection':
                    try {
                        const classifier = new cv.CascadeClassifier(cv.HAAR_FRONTALFACE_ALT2);
                        const grayImg = img.channels === 3 ? img.bgrToGray() : img;
                        const faces = classifier.detectMultiScale(grayImg);
                        
                        faces.objects.forEach(face => {
                            img = img.drawRectangle(
                                new cv.Point2(face.x, face.y),
                                new cv.Point2(face.x + face.width, face.y + face.height),
                                new cv.Vec3(0, 255, 0),
                                2
                            );
                        });
                    } catch (error) {
                        console.warn('Face detection failed:', error.message);
                    }
                    break;

                case 'resize':
                    const newSize = new cv.Size(op.width || 640, op.height || 480);
                    img = img.resize(newSize.height, newSize.width);
                    break;

                case 'rotate':
                    const angle = op.angle || 90;
                    const center = new cv.Point2(img.cols / 2, img.rows / 2);
                    const rotMat = cv.getRotationMatrix2D(center, angle, 1);
                    img = img.warpAffine(rotMat, new cv.Size(img.cols, img.rows));
                    break;

                case 'color_space':
                    const colorSpace = op.target || 'BGR2HSV';
                    switch (colorSpace) {
                        case 'BGR2HSV':
                            img = img.cvtColor(cv.COLOR_BGR2HSV);
                            break;
                        case 'BGR2LAB':
                            img = img.cvtColor(cv.COLOR_BGR2LAB);
                            break;
                        case 'BGR2GRAY':
                            img = img.bgrToGray();
                            break;
                    }
                    break;

                default:
                    console.warn(`Unknown operation: ${op.type}`);
            }
        }

        const filename = `processed-${uuidv4()}.jpg`;
        const outputPath = path.join(outputDir, filename);
        
        cv.imwrite(outputPath, img);
        
        // Clean up
        fs.unlinkSync(req.file.path);

        res.json({
            success: true,
            message: 'Image processed successfully',
            filePath: `/opencv-ffmpeg/output/${filename}`,
            operations: operationsList
        });

    } catch (error) {
        console.error('Image processing error:', error);
        if (req.file && fs.existsSync(req.file.path)) {
            fs.unlinkSync(req.file.path);
        }
        res.status(500).json({ 
            error: 'Failed to process image', 
            details: error.message 
        });
    }
});

// Advanced video processing with FFmpeg
app.post('/opencv-ffmpeg/process-video', upload.single('video'), async (req, res) => {
    try {
        const { operations = '[]', outputFormat = 'mp4' } = req.body;
        
        if (!req.file) {
            return res.status(400).json({ error: 'No video file provided' });
        }

        const operationsList = JSON.parse(operations);
        const outputFilename = `processed_${uuidv4()}.${outputFormat}`;
        const outputPath = path.join(outputDir, outputFilename);
        
        let ffmpegCommand = ffmpeg(req.file.path)
            .output(outputPath);

        // Apply video processing operations
        for (const op of operationsList) {
            switch (op.type) {
                case 'resize':
                    ffmpegCommand = ffmpegCommand.size(`${op.width}x${op.height}`);
                    break;
                
                case 'trim':
                    if (op.start) ffmpegCommand = ffmpegCommand.seekInput(op.start);
                    if (op.duration) ffmpegCommand = ffmpegCommand.duration(op.duration);
                    break;
                
                case 'fps':
                    ffmpegCommand = ffmpegCommand.fps(op.fps);
                    break;
                
                case 'codec':
                    ffmpegCommand = ffmpegCommand.videoCodec(op.codec);
                    break;
                
                case 'bitrate':
                    ffmpegCommand = ffmpegCommand.videoBitrate(op.bitrate);
                    break;
                
                case 'filter':
                    ffmpegCommand = ffmpegCommand.videoFilters(op.filter);
                    break;
                
                case 'audio_remove':
                    ffmpegCommand = ffmpegCommand.noAudio();
                    break;
                
                case 'watermark':
                    if (op.text) {
                        ffmpegCommand = ffmpegCommand.videoFilters({
                            filter: 'drawtext',
                            options: {
                                text: op.text,
                                fontsize: op.fontSize || 24,
                                fontcolor: op.color || 'white',
                                x: op.x || 10,
                                y: op.y || 10
                            }
                        });
                    }
                    break;
            }
        }

        // Process video
        ffmpegCommand
            .on('progress', (progress) => {
                console.log(`Processing: ${progress.percent}% done`);
            })
            .on('end', () => {
                // Clean up input file
                fs.unlinkSync(req.file.path);
                
                res.json({
                    success: true,
                    outputFile: outputFilename,
                    downloadUrl: `/opencv-ffmpeg/output/${outputFilename}`,
                    operations: operationsList,
                    format: outputFormat
                });
            })
            .on('error', (err) => {
                console.error('FFmpeg error:', err);
                if (fs.existsSync(req.file.path)) fs.unlinkSync(req.file.path);
                res.status(500).json({ 
                    error: 'Video processing failed', 
                    details: err.message 
                });
            })
            .run();

    } catch (error) {
        console.error('Video processing error:', error);
        if (req.file && fs.existsSync(req.file.path)) {
            fs.unlinkSync(req.file.path);
        }
        res.status(500).json({ 
            error: 'Video processing failed', 
            details: error.message 
        });
    }
});

// Object detection using OpenCV
app.post('/opencv-ffmpeg/detect-objects', upload.single('image'), async (req, res) => {
    try {
        const { method = 'contours', threshold = 100, minArea = 500 } = req.body;
        
        if (!req.file) {
            return res.status(400).json({ error: 'No image file provided' });
        }

        const img = cv.imread(req.file.path);
        const originalSize = { width: img.cols, height: img.rows };
        let detections = [];

        switch (method) {
            case 'contours':
                const gray = img.bgrToGray();
                const blurred = gray.gaussianBlur(new cv.Size(5, 5), 0);
                const edges = blurred.canny(threshold, threshold * 2);
                const contours = edges.findContours(cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE);
                
                detections = contours.map((contour, index) => {
                    const area = contour.area;
                    if (area > minArea) {
                        const boundingRect = contour.boundingRect();
                        return {
                            id: index,
                            type: 'contour',
                            area: area,
                            perimeter: contour.arcLength(true),
                            boundingBox: {
                                x: boundingRect.x,
                                y: boundingRect.y,
                                width: boundingRect.width,
                                height: boundingRect.height
                            }
                        };
                    }
                    return null;
                }).filter(d => d !== null);
                break;

            case 'template_matching':
                // Requires template image - simplified implementation
                const templatePath = req.body.templatePath;
                if (templatePath && fs.existsSync(templatePath)) {
                    const template = cv.imread(templatePath);
                    const result = img.matchTemplate(template, cv.TM_CCOEFF_NORMED);
                    const minMax = result.minMaxLoc();
                    
                    if (minMax.maxVal > 0.8) {
                        detections.push({
                            type: 'template_match',
                            confidence: minMax.maxVal,
                            location: minMax.maxLoc,
                            templateSize: { width: template.cols, height: template.rows }
                        });
                    }
                }
                break;

            case 'blob_detection':
                const params = new cv.SimpleBlobDetectorParams();
                params.filterByArea = true;
                params.minArea = minArea;
                params.maxArea = originalSize.width * originalSize.height * 0.5;
                
                const detector = new cv.SimpleBlobDetector(params);
                const keypoints = detector.detect(img);
                
                detections = keypoints.map((kp, index) => ({
                    id: index,
                    type: 'blob',
                    center: { x: kp.pt.x, y: kp.pt.y },
                    size: kp.size,
                    angle: kp.angle
                }));
                break;
        }

        // Clean up
        fs.unlinkSync(req.file.path);

        res.json({
            success: true,
            detections: detections,
            method: method,
            imageSize: originalSize,
            parameters: { threshold, minArea },
            detectionCount: detections.length
        });

    } catch (error) {
        console.error('Object detection error:', error);
        if (req.file && fs.existsSync(req.file.path)) {
            fs.unlinkSync(req.file.path);
        }
        res.status(500).json({ 
            error: 'Object detection failed', 
            details: error.message 
        });
    }
});

// Feature extraction from images
app.post('/opencv-ffmpeg/extract-features', upload.single('image'), async (req, res) => {
    try {
        const { method = 'orb', maxFeatures = 500 } = req.body;
        
        if (!req.file) {
            return res.status(400).json({ error: 'No image file provided' });
        }

        const img = cv.imread(req.file.path);
        const gray = img.channels === 3 ? img.bgrToGray() : img;
        
        let keypoints = [];
        let descriptors = null;

        switch (method.toLowerCase()) {
            case 'orb':
                const orb = new cv.ORBDetector(maxFeatures);
                const orbResult = orb.detectAndCompute(gray);
                keypoints = orbResult.keypoints;
                descriptors = orbResult.descriptors;
                break;

            case 'sift':
                try {
                    const sift = new cv.SIFTDetector({ nFeatures: maxFeatures });
                    const siftResult = sift.detectAndCompute(gray);
                    keypoints = siftResult.keypoints;
                    descriptors = siftResult.descriptors;
                } catch (error) {
                    console.warn('SIFT not available, falling back to ORB');
                    const orb = new cv.ORBDetector(maxFeatures);
                    const orbResult = orb.detectAndCompute(gray);
                    keypoints = orbResult.keypoints;
                    descriptors = orbResult.descriptors;
                }
                break;

            case 'fast':
                const fast = new cv.FastFeatureDetector();
                keypoints = fast.detect(gray);
                // FAST only detects keypoints, no descriptors
                break;

            case 'harris':
                const corners = gray.cornerHarris(2, 3, 0.04);
                const threshold = 0.01 * corners.minMaxLoc().maxVal;
                keypoints = [];
                
                for (let i = 0; i < corners.rows; i++) {
                    for (let j = 0; j < corners.cols; j++) {
                        if (corners.at(i, j) > threshold) {
                            keypoints.push({
                                pt: { x: j, y: i },
                                size: 1,
                                angle: 0,
                                response: corners.at(i, j)
                            });
                        }
                    }
                }
                break;
        }

        // Extract feature information
        const features = keypoints.map((kp, index) => ({
            id: index,
            point: { x: kp.pt.x, y: kp.pt.y },
            size: kp.size,
            angle: kp.angle,
            response: kp.response || 0
        }));

        // Calculate image statistics
        const mean = gray.mean();
        const stdDev = gray.stdDev();

        // Clean up
        fs.unlinkSync(req.file.path);

        res.json({
            success: true,
            method: method,
            features: features,
            featureCount: features.length,
            imageStats: {
                size: { width: img.cols, height: img.rows },
                channels: img.channels,
                mean: mean,
                stdDev: stdDev
            },
            descriptorShape: descriptors ? {
                rows: descriptors.rows,
                cols: descriptors.cols,
                type: descriptors.type
            } : null
        });

    } catch (error) {
        console.error('Feature extraction error:', error);
        if (req.file && fs.existsSync(req.file.path)) {
            fs.unlinkSync(req.file.path);
        }
        res.status(500).json({ 
            error: 'Feature extraction failed', 
            details: error.message 
        });
    }
});

// Extract frames from video
app.post('/opencv-ffmpeg/video-to-frames', upload.single('video'), async (req, res) => {
    try {
        const { 
            frameRate = 1, 
            format = 'jpg', 
            quality = 90,
            startTime = 0,
            duration = null,
            maxFrames = 100
        } = req.body;
        
        if (!req.file) {
            return res.status(400).json({ error: 'No video file provided' });
        }

        const framesDir = path.join(outputDir, `frames_${uuidv4()}`);
        fs.mkdirSync(framesDir, { recursive: true });
        
        const framePattern = path.join(framesDir, `frame_%04d.${format}`);
        
        let ffmpegCommand = ffmpeg(req.file.path)
            .seekInput(startTime)
            .outputOptions([
                `-vf fps=${frameRate}`,
                `-q:v ${quality}`
            ])
            .output(framePattern);

        if (duration) {
            ffmpegCommand = ffmpegCommand.duration(duration);
        }

        ffmpegCommand
            .on('end', () => {
                const frameFiles = fs.readdirSync(framesDir)
                    .filter(file => file.startsWith('frame_'))
                    .slice(0, maxFrames)
                    .map(file => ({
                        filename: file,
                        url: `/opencv-ffmpeg/output/frames_${path.basename(framesDir)}/${file}`
                    }));

                // Clean up input file
                fs.unlinkSync(req.file.path);

                res.json({
                    success: true,
                    framesExtracted: frameFiles.length,
                    frames: frameFiles,
                    framesDirectory: path.basename(framesDir),
                    parameters: {
                        frameRate,
                        format,
                        quality,
                        startTime,
                        duration,
                        maxFrames
                    }
                });
            })
            .on('error', (err) => {
                console.error('Frame extraction error:', err);
                if (fs.existsSync(req.file.path)) fs.unlinkSync(req.file.path);
                res.status(500).json({ 
                    error: 'Frame extraction failed', 
                    details: err.message 
                });
            })
            .run();

    } catch (error) {
        console.error('Video to frames error:', error);
        if (req.file && fs.existsSync(req.file.path)) {
            fs.unlinkSync(req.file.path);
        }
        res.status(500).json({ 
            error: 'Video to frames conversion failed', 
            details: error.message 
        });
    }
});

// Health check endpoint
app.get('/health', (req, res) => {
    res.json({
        status: 'healthy',
        service: 'opencv-ffmpeg',
        opencv: cv.version,
        features: {
            imageProcessing: true,
            videoProcessing: true,
            objectDetection: true,
            featureExtraction: true,
            frameExtraction: true
        },
        timestamp: new Date().toISOString()
    });
});

// Serve static files from the output directory
app.use('/opencv-ffmpeg/output', express.static(outputDir));

app.listen(port, () => {
    console.log(`OpenCV + FFmpeg API listening at http://localhost:${port}`);
    console.log(`OpenCV version: ${cv.version}`);
});
