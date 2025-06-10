const express = require('express');
const path = require('path');
const fs = require('fs');
const { v4: uuidv4 } = require('uuid');
const cors = require('cors');
const puppeteer = require('puppeteer');

const app = express();
const port = 3012;

app.use(cors());
app.use(express.json({ limit: '50mb' }));

// Ensure directories exist
const outputDir = path.join(__dirname, 'output');
const templatesDir = path.join(__dirname, 'templates');

[outputDir, templatesDir].forEach(dir => {
    if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
    }
});

// Create a basic Three.js template if it doesn't exist
const templatePath = path.join(templatesDir, 'basic-scene.html');
if (!fs.existsSync(templatePath)) {
    const basicTemplate = `<!DOCTYPE html>
<html>
<head>
    <title>Three.js Scene</title>
    <style>
        body { margin: 0; overflow: hidden; background: #000; }
        canvas { display: block; }
    </style>
</head>
<body>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/OBJLoader.js"></script>
    <script>
        // Scene setup will be injected here
        {{SCENE_CODE}}
    </script>
</body>
</html>`;
    fs.writeFileSync(templatePath, basicTemplate);
}

// Generate 3D scene
app.post('/three-js/generate-scene', async (req, res) => {
    try {
        const { 
            sceneConfig, 
            renderOptions = {}, 
            outputFormat = 'png',
            width = 800,
            height = 600
        } = req.body;

        if (!sceneConfig) {
            return res.status(400).json({ error: 'Scene configuration is required' });
        }

        const sceneCode = generateSceneCode(sceneConfig, width, height);
        const template = fs.readFileSync(templatePath, 'utf8');
        const htmlContent = template.replace('{{SCENE_CODE}}', sceneCode);

        const filename = `scene-${uuidv4()}.${outputFormat}`;
        const outputPath = path.join(outputDir, filename);
        const tempHtmlPath = path.join(outputDir, `temp-${uuidv4()}.html`);

        // Write temporary HTML file
        fs.writeFileSync(tempHtmlPath, htmlContent);

        // Use Puppeteer to render the scene
        const browser = await puppeteer.launch({ 
            headless: true,
            args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-web-security']
        });
        
        const page = await browser.newPage();
        await page.setViewport({ width, height });
        
        // Load the HTML file
        await page.goto(`file://${tempHtmlPath}`, { waitUntil: 'networkidle0' });
        
        // Wait for Three.js to render
        await page.waitForTimeout(2000);
        
        // Take screenshot
        const screenshotOptions = {
            path: outputPath,
            type: outputFormat,
            clip: { x: 0, y: 0, width, height }
        };

        if (outputFormat === 'jpeg') {
            screenshotOptions.quality = renderOptions.quality || 90;
        }

        await page.screenshot(screenshotOptions);
        
        await browser.close();
        
        // Clean up temporary HTML file
        fs.unlinkSync(tempHtmlPath);

        res.json({
            success: true,
            message: '3D scene rendered successfully',
            filePath: `/three-js/output/${filename}`,
            sceneConfig: sceneConfig
        });

    } catch (error) {
        console.error('3D scene generation error:', error);
        res.status(500).json({ 
            error: 'Failed to generate 3D scene', 
            details: error.message 
        });
    }
});

// Generate 3D model viewer
app.post('/three-js/model-viewer', async (req, res) => {
    try {
        const { 
            modelUrl, 
            modelType = 'gltf',
            cameraPosition = { x: 5, y: 5, z: 5 },
            lighting = 'default',
            background = '#ffffff',
            outputFormat = 'png',
            width = 800,
            height = 600
        } = req.body;

        if (!modelUrl) {
            return res.status(400).json({ error: 'Model URL is required' });
        }

        const sceneCode = generateModelViewerCode({
            modelUrl,
            modelType,
            cameraPosition,
            lighting,
            background,
            width,
            height
        });

        const template = fs.readFileSync(templatePath, 'utf8');
        const htmlContent = template.replace('{{SCENE_CODE}}', sceneCode);

        const filename = `model-${uuidv4()}.${outputFormat}`;
        const outputPath = path.join(outputDir, filename);
        const tempHtmlPath = path.join(outputDir, `temp-${uuidv4()}.html`);

        // Write temporary HTML file
        fs.writeFileSync(tempHtmlPath, htmlContent);

        // Use Puppeteer to render the model
        const browser = await puppeteer.launch({ 
            headless: true,
            args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-web-security']
        });
        
        const page = await browser.newPage();
        await page.setViewport({ width, height });
        
        await page.goto(`file://${tempHtmlPath}`, { waitUntil: 'networkidle0' });
        await page.waitForTimeout(3000); // Wait longer for model loading
        
        await page.screenshot({
            path: outputPath,
            type: outputFormat,
            clip: { x: 0, y: 0, width, height }
        });
        
        await browser.close();
        fs.unlinkSync(tempHtmlPath);

        res.json({
            success: true,
            message: '3D model rendered successfully',
            filePath: `/three-js/output/${filename}`,
            modelUrl: modelUrl
        });

    } catch (error) {
        console.error('3D model viewer error:', error);
        res.status(500).json({ 
            error: 'Failed to render 3D model', 
            details: error.message 
        });
    }
});

// Generate animation frames
app.post('/three-js/generate-animation', async (req, res) => {
    try {
        const { 
            sceneConfig,
            animationConfig = {},
            frameCount = 30,
            outputFormat = 'png',
            width = 800,
            height = 600
        } = req.body;

        if (!sceneConfig) {
            return res.status(400).json({ error: 'Scene configuration is required' });
        }

        const frames = [];
        const animationId = uuidv4();

        for (let i = 0; i < frameCount; i++) {
            const frameProgress = i / (frameCount - 1);
            const frameSceneCode = generateAnimationFrameCode(sceneConfig, animationConfig, frameProgress, width, height);
            
            const template = fs.readFileSync(templatePath, 'utf8');
            const htmlContent = template.replace('{{SCENE_CODE}}', frameSceneCode);

            const filename = `animation-${animationId}-frame-${String(i).padStart(4, '0')}.${outputFormat}`;
            const outputPath = path.join(outputDir, filename);
            const tempHtmlPath = path.join(outputDir, `temp-frame-${i}.html`);

            fs.writeFileSync(tempHtmlPath, htmlContent);

            const browser = await puppeteer.launch({ 
                headless: true,
                args: ['--no-sandbox', '--disable-setuid-sandbox']
            });
            
            const page = await browser.newPage();
            await page.setViewport({ width, height });
            await page.goto(`file://${tempHtmlPath}`, { waitUntil: 'networkidle0' });
            await page.waitForTimeout(1000);
            
            await page.screenshot({
                path: outputPath,
                type: outputFormat,
                clip: { x: 0, y: 0, width, height }
            });
            
            await browser.close();
            fs.unlinkSync(tempHtmlPath);

            frames.push(`/three-js/output/${filename}`);
        }

        res.json({
            success: true,
            message: 'Animation frames generated successfully',
            frameCount: frameCount,
            frames: frames,
            animationId: animationId
        });

    } catch (error) {
        console.error('Animation generation error:', error);
        res.status(500).json({ 
            error: 'Failed to generate animation frames', 
            details: error.message 
        });
    }
});

// Generate 3D scene with advanced features
app.post('/three-js/render-scene', async (req, res) => {
    try {
        const {
            sceneConfig = {},
            camera = { type: 'perspective', position: [0, 0, 5], target: [0, 0, 0] },
            objects = [],
            lights = [],
            materials = {},
            animations = [],
            environment = {},
            renderSettings = { width: 800, height: 600, quality: 'medium' }
        } = req.body;

        // Generate scene code
        const sceneCode = generateSceneCode({
            sceneConfig,
            camera,
            objects,
            lights,
            materials,
            animations,
            environment,
            renderSettings
        });

        // Create HTML file with the scene
        const htmlContent = await createSceneHTML(sceneCode);
        const htmlPath = path.join(outputDir, `scene_${uuidv4()}.html`);
        fs.writeFileSync(htmlPath, htmlContent);

        // Render scene using Puppeteer
        const imageBuffer = await renderSceneToImage(htmlPath, renderSettings);
        
        // Save rendered image
        const imageName = `render_${uuidv4()}.png`;
        const imagePath = path.join(outputDir, imageName);
        fs.writeFileSync(imagePath, imageBuffer);

        // Clean up HTML file
        fs.unlinkSync(htmlPath);

        res.json({
            success: true,
            renderUrl: `/three-js/output/${imageName}`,
            renderSettings: renderSettings,
            sceneInfo: {
                objectCount: objects.length,
                lightCount: lights.length,
                hasAnimations: animations.length > 0,
                hasEnvironment: Object.keys(environment).length > 0
            }
        });

    } catch (error) {
        console.error('Scene rendering error:', error);
        res.status(500).json({ 
            error: 'Scene rendering failed', 
            details: error.message 
        });
    }
});

// Generate 3D model from parameters
app.post('/three-js/generate-model', async (req, res) => {
    try {
        const {
            modelType = 'box',
            parameters = {},
            material = { type: 'basic', color: 0x00ff00 },
            export_format = 'gltf',
            includeTextures = false
        } = req.body;

        const modelCode = generateModelCode(modelType, parameters, material);
        const sceneCode = `
            ${modelCode}
            
            // Setup scene
            const scene = new THREE.Scene();
            const camera = new THREE.PerspectiveCamera(75, 1, 0.1, 1000);
            const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
            
            renderer.setSize(800, 600);
            renderer.shadowMap.enabled = true;
            renderer.shadowMap.type = THREE.PCFSoftShadowMap;
            
            // Add lighting
            const ambientLight = new THREE.AmbientLight(0x404040, 0.6);
            scene.add(ambientLight);
            
            const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
            directionalLight.position.set(10, 10, 5);
            directionalLight.castShadow = true;
            scene.add(directionalLight);
            
            // Add the generated model
            scene.add(generatedModel);
            
            // Position camera
            camera.position.z = 5;
            
            // Render
            renderer.render(scene, camera);
            
            // Export functionality would go here
            console.log('Model generated:', generatedModel);
        `;

        const htmlContent = await createSceneHTML(sceneCode);
        const htmlPath = path.join(outputDir, `model_${uuidv4()}.html`);
        fs.writeFileSync(htmlPath, htmlContent);

        // Render the model
        const imageBuffer = await renderSceneToImage(htmlPath, { width: 800, height: 600 });
        
        const imageName = `model_${uuidv4()}.png`;
        const imagePath = path.join(outputDir, imageName);
        fs.writeFileSync(imagePath, imageBuffer);

        // Clean up
        fs.unlinkSync(htmlPath);

        res.json({
            success: true,
            modelType: modelType,
            parameters: parameters,
            previewUrl: `/three-js/output/${imageName}`,
            exportFormat: export_format,
            modelInfo: {
                type: modelType,
                materialType: material.type,
                hasTextures: includeTextures
            }
        });

    } catch (error) {
        console.error('Model generation error:', error);
        res.status(500).json({ 
            error: 'Model generation failed', 
            details: error.message 
        });
    }
});

// Create animated 3D scenes
app.post('/three-js/animate-object', async (req, res) => {
    try {
        const {
            object = { type: 'box', size: [1, 1, 1] },
            animations = [],
            duration = 5000,
            fps = 30,
            outputFormat = 'gif',
            camera = { position: [0, 0, 5], target: [0, 0, 0] }
        } = req.body;

        const frameCount = Math.floor((duration / 1000) * fps);
        const frames = [];

        // Generate animation code
        const animationCode = generateAnimationCode(object, animations, duration, fps);
        
        for (let frame = 0; frame < frameCount; frame++) {
            const progress = frame / (frameCount - 1);
            const frameCode = `
                ${animationCode}
                
                // Set animation progress
                const animationProgress = ${progress};
                updateAnimation(animationProgress);
                
                renderer.render(scene, camera);
            `;

            const htmlContent = await createSceneHTML(frameCode);
            const htmlPath = path.join(outputDir, `frame_${frame}.html`);
            fs.writeFileSync(htmlPath, htmlContent);

            // Render frame
            const frameBuffer = await renderSceneToImage(htmlPath, { width: 400, height: 400 });
            frames.push(frameBuffer);

            // Clean up frame HTML
            fs.unlinkSync(htmlPath);
        }

        // Create animation output
        let outputPath;
        if (outputFormat === 'gif') {
            outputPath = await createGifFromFrames(frames, fps);
        } else {
            // Save as image sequence
            outputPath = await saveFrameSequence(frames);
        }

        res.json({
            success: true,
            animationUrl: `/three-js/output/${path.basename(outputPath)}`,
            frameCount: frameCount,
            duration: duration,
            fps: fps,
            format: outputFormat,
            animationInfo: {
                objectType: object.type,
                animationCount: animations.length
            }
        });

    } catch (error) {
        console.error('Animation error:', error);
        res.status(500).json({ 
            error: 'Animation creation failed', 
            details: error.message 
        });
    }
});

// Get available scene templates
app.get('/three-js/scene-templates', (req, res) => {
    try {
        const templates = {
            basic: {
                name: 'Basic Scene',
                description: 'Simple scene with basic lighting and a single object',
                objects: ['box', 'sphere', 'cylinder'],
                features: ['basic_lighting', 'orbit_controls']
            },
            architectural: {
                name: 'Architectural Visualization',
                description: 'Scene optimized for architectural models',
                objects: ['building', 'room', 'furniture'],
                features: ['realistic_lighting', 'shadows', 'materials']
            },
            product: {
                name: 'Product Showcase',
                description: 'Scene for product visualization',
                objects: ['product_pedestal', 'spotlight_rig'],
                features: ['studio_lighting', 'reflections', 'materials']
            },
            landscape: {
                name: 'Landscape/Terrain',
                description: 'Outdoor scene with terrain and nature elements',
                objects: ['terrain', 'trees', 'sky'],
                features: ['skybox', 'fog', 'particle_systems']
            },
            abstract: {
                name: 'Abstract/Artistic',
                description: 'Creative scene for abstract visualizations',
                objects: ['geometric_shapes', 'fractals'],
                features: ['custom_shaders', 'post_processing', 'particle_systems']
            }
        };

        res.json({
            success: true,
            templates: templates,
            totalTemplates: Object.keys(templates).length
        });

    } catch (error) {
        console.error('Templates error:', error);
        res.status(500).json({ 
            error: 'Failed to get templates', 
            details: error.message 
        });
    }
});

// Create panoramic/360 renders
app.post('/three-js/render-panoramic', async (req, res) => {
    try {
        const {
            scene = {},
            quality = 'medium',
            format = 'equirectangular',
            resolution = { width: 2048, height: 1024 }
        } = req.body;

        const panoramicCode = `
            // Create panoramic scene
            const scene = new THREE.Scene();
            ${generateSceneFromConfig(scene)}
            
            // Create cube camera for panoramic rendering
            const cubeRenderTarget = new THREE.WebGLCubeRenderTarget(512);
            const cubeCamera = new THREE.CubeCamera(0.1, 1000, cubeRenderTarget);
            scene.add(cubeCamera);
            
            // Render panoramic view
            cubeCamera.update(renderer, scene);
            
            // Convert to equirectangular
            const panoramicMaterial = new THREE.MeshBasicMaterial({
                map: cubeRenderTarget.texture,
                side: THREE.BackSide
            });
            
            const panoramicGeometry = new THREE.SphereGeometry(500, 64, 32);
            const panoramicMesh = new THREE.Mesh(panoramicGeometry, panoramicMaterial);
            
            const panoramicScene = new THREE.Scene();
            panoramicScene.add(panoramicMesh);
            
            const panoramicCamera = new THREE.PerspectiveCamera(90, ${resolution.width}/${resolution.height}, 0.1, 1000);
            
            // Render final panoramic image
            renderer.setSize(${resolution.width}, ${resolution.height});
            renderer.render(panoramicScene, panoramicCamera);
        `;

        const htmlContent = await createSceneHTML(panoramicCode);
        const htmlPath = path.join(outputDir, `panoramic_${uuidv4()}.html`);
        fs.writeFileSync(htmlPath, htmlContent);

        const imageBuffer = await renderSceneToImage(htmlPath, resolution);
        
        const imageName = `panoramic_${uuidv4()}.png`;
        const imagePath = path.join(outputDir, imageName);
        fs.writeFileSync(imagePath, imageBuffer);

        fs.unlinkSync(htmlPath);

        res.json({
            success: true,
            panoramicUrl: `/three-js/output/${imageName}`,
            format: format,
            resolution: resolution,
            quality: quality
        });

    } catch (error) {
        console.error('Panoramic rendering error:', error);
        res.status(500).json({ 
            error: 'Panoramic rendering failed', 
            details: error.message 
        });
    }
});

// Health check endpoint
app.get('/health', (req, res) => {
    res.json({
        status: 'healthy',
        service: 'three-js',
        features: {
            sceneRendering: true,
            modelGeneration: true,
            animation: true,
            panoramicRendering: true,
            templates: true
        },
        supportedFormats: ['png', 'jpg', 'gif', 'gltf', 'obj'],
        timestamp: new Date().toISOString()
    });
});

// Helper functions
function generateSceneCode(config) {
    const { camera, objects, lights, materials, animations, environment, renderSettings } = config;
    
    return `
        // Scene setup
        const scene = new THREE.Scene();
        const camera = new THREE.${camera.type === 'orthographic' ? 'OrthographicCamera' : 'PerspectiveCamera'}(
            75, ${renderSettings.width}/${renderSettings.height}, 0.1, 1000
        );
        
        const renderer = new THREE.WebGLRenderer({ 
            antialias: ${renderSettings.quality !== 'low'}, 
            alpha: true 
        });
        renderer.setSize(${renderSettings.width}, ${renderSettings.height});
        
        ${environment.background ? `scene.background = new THREE.Color(${environment.background});` : ''}
        ${environment.fog ? `scene.fog = new THREE.Fog(${environment.fog.color}, ${environment.fog.near}, ${environment.fog.far});` : ''}
        
        // Camera positioning
        camera.position.set(${camera.position.join(', ')});
        ${camera.target ? `camera.lookAt(${camera.target.join(', ')});` : ''}
        
        // Add lights
        ${lights.map(light => generateLightCode(light)).join('\n')}
        
        // Add objects
        ${objects.map(obj => generateObjectCode(obj, materials)).join('\n')}
        
        // Animation setup
        ${animations.length > 0 ? generateAnimationSetup(animations) : ''}
        
        // Render
        renderer.render(scene, camera);
    `;
}

function generateLightCode(light) {
    switch (light.type) {
        case 'ambient':
            return `
                const ambientLight = new THREE.AmbientLight(${light.color || 0x404040}, ${light.intensity || 0.5});
                scene.add(ambientLight);
            `;
        case 'directional':
            return `
                const directionalLight = new THREE.DirectionalLight(${light.color || 0xffffff}, ${light.intensity || 1});
                directionalLight.position.set(${light.position ? light.position.join(', ') : '10, 10, 5'});
                ${light.castShadow ? 'directionalLight.castShadow = true;' : ''}
                scene.add(directionalLight);
            `;
        case 'point':
            return `
                const pointLight = new THREE.PointLight(${light.color || 0xffffff}, ${light.intensity || 1}, ${light.distance || 0});
                pointLight.position.set(${light.position ? light.position.join(', ') : '0, 10, 0'});
                scene.add(pointLight);
            `;
        case 'spot':
            return `
                const spotLight = new THREE.SpotLight(${light.color || 0xffffff}, ${light.intensity || 1});
                spotLight.position.set(${light.position ? light.position.join(', ') : '10, 10, 10'});
                ${light.target ? `spotLight.target.position.set(${light.target.join(', ')});` : ''}
                scene.add(spotLight);
            `;
        default:
            return '';
    }
}

function generateObjectCode(obj, materials) {
    const materialCode = generateMaterialCode(obj.material || 'basic', materials[obj.material] || {});
    
    switch (obj.type) {
        case 'box':
            return `
                const boxGeometry = new THREE.BoxGeometry(${obj.size ? obj.size.join(', ') : '1, 1, 1'});
                ${materialCode}
                const box = new THREE.Mesh(boxGeometry, material);
                ${obj.position ? `box.position.set(${obj.position.join(', ')});` : ''}
                ${obj.rotation ? `box.rotation.set(${obj.rotation.join(', ')});` : ''}
                scene.add(box);
            `;
        case 'sphere':
            return `
                const sphereGeometry = new THREE.SphereGeometry(${obj.radius || 1}, ${obj.segments || 32}, ${obj.rings || 32});
                ${materialCode}
                const sphere = new THREE.Mesh(sphereGeometry, material);
                ${obj.position ? `sphere.position.set(${obj.position.join(', ')});` : ''}
                scene.add(sphere);
            `;
        case 'cylinder':
            return `
                const cylinderGeometry = new THREE.CylinderGeometry(
                    ${obj.radiusTop || 1}, ${obj.radiusBottom || 1}, ${obj.height || 1}, ${obj.segments || 32}
                );
                ${materialCode}
                const cylinder = new THREE.Mesh(cylinderGeometry, material);
                ${obj.position ? `cylinder.position.set(${obj.position.join(', ')});` : ''}
                scene.add(cylinder);
            `;
        case 'plane':
            return `
                const planeGeometry = new THREE.PlaneGeometry(${obj.width || 1}, ${obj.height || 1});
                ${materialCode}
                const plane = new THREE.Mesh(planeGeometry, material);
                ${obj.position ? `plane.position.set(${obj.position.join(', ')});` : ''}
                ${obj.rotation ? `plane.rotation.set(${obj.rotation.join(', ')});` : ''}
                scene.add(plane);
            `;
        default:
            return '';
    }
}

function generateMaterialCode(type, params) {
    switch (type) {
        case 'basic':
            return `const material = new THREE.MeshBasicMaterial({ color: ${params.color || 0x00ff00} });`;
        case 'lambert':
            return `const material = new THREE.MeshLambertMaterial({ color: ${params.color || 0x00ff00} });`;
        case 'phong':
            return `const material = new THREE.MeshPhongMaterial({ 
                color: ${params.color || 0x00ff00},
                shininess: ${params.shininess || 30}
            });`;
        case 'standard':
            return `const material = new THREE.MeshStandardMaterial({ 
                color: ${params.color || 0x00ff00},
                metalness: ${params.metalness || 0},
                roughness: ${params.roughness || 0.5}
            });`;
        default:
            return `const material = new THREE.MeshBasicMaterial({ color: 0x00ff00 });`;
    }
}

function generateAnimationSetup(animations) {
    return animations.map((anim, index) => {
        const keyframes = anim.keyframes.map(kf => `{
            time: ${kf.time},
            value: ${JSON.stringify(kf.value)}
        }`);

        return `
            // Animation ${index + 1}
            const mixer${index} = new THREE.AnimationMixer(object);
            const clip${index} = new THREE.AnimationClip('animateAction${index}', -1, [
                ${keyframes.join(', ')}
            ]);
            mixer${index}.clipAction(clip${index}).play();
        `;
    }).join('\n');
}

function generateAnimationCode(object, animations, duration, fps) {
    const baseCode = `
        // Object setup
        const geometry = new THREE.BoxGeometry(${object.size.join(', ')});
        const material = new THREE.MeshBasicMaterial({ color: 0x00ff00 });
        const obj = new THREE.Mesh(geometry, material);
        scene.add(obj);
        
        // Animation function
        function updateAnimation(progress) {
            obj.rotation.x = progress * Math.PI * 2;
            obj.rotation.y = progress * Math.PI * 2;
        }
    `;

    const animationCode = animations.map((anim, index) => {
        const keyframes = anim.keyframes.map(kf => `{
            time: ${kf.time},
            value: ${JSON.stringify(kf.value)}
        }`);

        return `
            // Animation ${index + 1}
            const mixer${index} = new THREE.AnimationMixer(obj);
            const clip${index} = new THREE.AnimationClip('animateAction${index}', -1, [
                ${keyframes.join(', ')}
            ]);
            mixer${index}.clipAction(clip${index}).play();
        `;
    }).join('\n');

    return `${baseCode}\n${animationCode}`;
}

async function createSceneHTML(sceneCode) {
    const template = fs.readFileSync(path.join(templatesDir, 'basic-scene.html'), 'utf8');
    return template.replace('{{SCENE_CODE}}', sceneCode);
}

async function renderSceneToImage(htmlPath, settings) {
    const browser = await puppeteer.launch({ 
        args: ['--no-sandbox', '--disable-setuid-sandbox'],
        headless: 'new'
    });
    
    const page = await browser.newPage();
    await page.setViewport({ 
        width: settings.width || 800, 
        height: settings.height || 600 
    });
    
    await page.goto(`file://${htmlPath}`, { waitUntil: 'networkidle0' });
    
    // Wait for Three.js to render
    await page.waitForTimeout(2000);
    
    const screenshot = await page.screenshot({ 
        type: 'png',
        fullPage: false
    });
    
    await browser.close();
    return screenshot;
}

// Serve static files from the output directory
app.use('/three-js/output', express.static(outputDir));

app.listen(port, () => {
    console.log(`Three.js API listening at http://localhost:${port}`);
});
