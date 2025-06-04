// 海洋主题交互脚本

class OceanAPIExplorer {
    constructor() {
        this.apiBlocksContainer = document.querySelector('.apis-ocean');
        this.modalElements = {};
        this.loadingOverlayElement = null;
        
        this.particleCanvas = null;
        this.particleCtx = null;
        this.particleAnimationId = null;
        this.particles = [];

        this.apis = this._getApisData();

        this._initializeLoadingScreen();
    }

    _getApisData() {
        return [
            {
                id: 'pygments',
                icon: '🌈',
                title: 'Pygments API',
                description: '代码语法高亮',
                detailsPath: 'pygments/pygments.html'
            },
            {
                id: 'pillow',
                icon: '🖼️',
                title: 'Pillow API',
                description: '图像处理',
                detailsPath: 'pillow/pillow.html'
            },
            {
                id: 'python-qrcode',
                icon: '📱',
                title: 'python-qrcode API',
                description: '二维码生成',
                detailsPath: 'python-qrcode/python-qrcode.html'
            },
            {
                id: 'ajv',
                icon: '✅',
                title: 'Ajv API',
                description: 'JSON Schema 验证',
                detailsPath: 'ajv/ajv.html'
            },
            {
                id: 'eslint',
                icon: '🔍',
                title: 'ESLint API',
                description: 'JS/TS 静态分析',
                detailsPath: 'eslint/eslint.html'
            },
            {
                id: 'diff',
                icon: '🔄',
                title: 'Diff API',
                description: '文本内容比较',
                detailsPath: 'diff/diff.html'
            },
            {
                id: 'csv-parser',
                icon: '📊',
                title: 'CSV Parser API',
                description: 'CSV 转 JSON',
                detailsPath: 'csv-parser/csv-parser.html'
            },
            {
                id: 'mermaid-cli',
                icon: '📈',
                title: 'Mermaid CLI API',
                description: '文本生成图表',
                detailsPath: 'mermaid-cli/mermaid-cli.html'
            },
            {
                id: 'pdfkit',
                icon: '📄',
                title: 'PDFKit API',
                description: 'PDF 文档生成',
                detailsPath: 'pdfkit/pdfkit.html'
            },
            {
                id: 'sanitize-html',
                icon: '🛡️',
                title: 'sanitize-html API',
                description: 'HTML 清理 (XSS防护)',
                detailsPath: 'sanitize-html/sanitize-html.html'
            },
            {
                id: 'marked',
                icon: '📝',
                title: 'Marked API',
                description: 'Markdown 转 HTML',
                detailsPath: 'marked/marked.html' // Changed
            },
            {
                id: 'beautifulsoup',
                icon: '🥄',
                title: 'Beautiful Soup API',
                description: 'HTML 解析与提取',
                detailsPath: 'beautifulsoup/beautifulsoup.html' // Changed
            },
            {
                id: 'prettier',
                icon: '🎨',
                title: 'Prettier API',
                description: '代码格式化工具',
                detailsPath: 'Prettier/Prettier.html' // Changed
            }
            // Add other existing APIs if they were removed by mistake during merge
            // For example, if BeautifulSoup was meant to be kept:
            /*
            {
                id: 'beautifulsoup',
                icon: '🥄',
                title: 'Beautiful Soup API',
                description: 'HTML 解析与提取',
                detailsPath: 'beautifulsoup/beautifulsoup.html'
            }
            */
        ];
    }

    _initializeLoadingScreen() {
        document.body.style.opacity = '0';
        document.body.style.transform = 'scale(0.95)';

        this.loadingOverlayElement = document.createElement('div');
        this.loadingOverlayElement.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(135deg, #0c4a6e, #0369a1);
            z-index: 9999;
            display: flex;
            justify-content: center;
            align-items: center;
            flex-direction: column;
            color: #f0f9ff;
            font-family: 'SF Mono', Monaco, Consolas, monospace;
        `;
        this.loadingOverlayElement.innerHTML = `
            <div style="font-size: 3em; margin-bottom: 20px; animation: ocean-pulse 2s ease-in-out infinite;">🌊</div>
            <div style="font-size: 1.5em; text-align: center;">
                <div style="margin-bottom: 10px;">开源库API化平台</div>
                <div style="font-size: 0.8em; opacity: 0.7;">正在加载海洋...</div>
            </div>
            <div style="margin-top: 30px; width: 200px; height: 4px; background: rgba(56, 189, 248, 0.2); border-radius: 2px; overflow: hidden;">
                <div style="width: 0%; height: 100%; background: linear-gradient(90deg, #38bdf8, #60a5fa); border-radius: 2px; animation: ocean-loading-bar 2s ease-out forwards;"></div>
            </div>
        `;
        document.body.appendChild(this.loadingOverlayElement);

        const style = document.createElement('style');
        style.textContent = `
            @keyframes ocean-pulse {
                0%, 100% { transform: scale(1); opacity: 1; }
                50% { transform: scale(1.2); opacity: 0.8; }
            }
            @keyframes ocean-loading-bar {
                to { width: 100%; }
            }
        `;
        document.head.appendChild(style);

        this._initMainApplication();
        if (this.loadingOverlayElement) {
            this.loadingOverlayElement.remove();
        }
        document.body.style.opacity = '1';
        document.body.style.transform = 'scale(1)';
        document.body.style.transition = 'opacity 0.5s ease-out, transform 0.5s ease-out';
    }

    _initMainApplication() {
        this._createAPIBlocks();
        this._setupModal();
        this._setupGlobalEventListeners();
        this._createOceanVisualEffects();
        this._setupMouseRippleEffect();
    }

    _createAPIBlocks() {
        this.apis.forEach((api, index) => {
            const block = this._createSingleAPIBlock(api, index);
            this.apiBlocksContainer.appendChild(block);
        });
    }    _createSingleAPIBlock(api, index) {
        const block = document.createElement('div');
        block.className = 'api-floating-block';
        block.dataset.apiId = api.id;
        
        const randomDelay = Math.random() * 2;
        const randomDuration = 3 + Math.random() * 2;
        block.style.animationDelay = `${randomDelay}s`;
        block.style.animationDuration = `${randomDuration}s`;

        // 检查是否有演示支持
        const demoSupported = ['marked', 'prettier', 'beautifulsoup', 'pygments', 'diff', 'csv-parser', 'sanitize-html', 'ajv'].includes(api.id);
        
        const demoButton = demoSupported ? 
            `<button class="api-demo-btn" onclick="event.stopPropagation(); window.open('demo.html#${api.id}', '_blank')">
                🚀 快速演示
            </button>` : '';

        block.innerHTML = `
            <div class="api-block-content">
                <div class="api-block-icon">${api.icon}</div>
                <div class="api-block-title">${api.title}</div>
                <div class="api-block-desc">${api.description}</div>
                ${demoButton}
            </div>
        `;

        block.addEventListener('click', () => this.openModal(api));
        return block;
    }

    _setupModal() {
        const modalHTML = `
            <div class="modal-overlay">
                <div class="modal-content">
                    <div class="modal-header">
                        <div class="modal-title"></div>
                        <button class="modal-close">&times;</button>
                    </div>
                    <div class="modal-body">
                        <div class="api-details"></div>
                    </div>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modalHTML);

        this.modalElements.overlay = document.querySelector('.modal-overlay');
        this.modalElements.content = document.querySelector('.modal-content');
        this.modalElements.title = document.querySelector('.modal-title');
        this.modalElements.details = document.querySelector('.api-details');
        this.modalElements.closeButton = document.querySelector('.modal-close');
    }

    _setupGlobalEventListeners() {
        this.modalElements.closeButton.addEventListener('click', () => this.closeModal());
        
        this.modalElements.overlay.addEventListener('click', (e) => {
            if (e.target === this.modalElements.overlay) {
                this.closeModal();
            }
        });

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.modalElements.overlay.classList.contains('active')) {
                this.closeModal();
            }
        });

        window.addEventListener('resize', () => this._resizeParticleCanvas());
    }
    
    async openModal(api) { // Added async
        this.modalElements.title.textContent = api.title;
        
        // Fetch details from HTML file
        if (api.detailsPath) {
            try {
                const response = await fetch(api.detailsPath);
                // For file:/// URLs, response.status might be 0 on success in some browsers/contexts,
                // while response.ok (true for statuses 200-299) might be false.
                // We treat status 0 as success for local files if response.ok is false.
                if (response.ok || response.status === 0) { 
                    const detailsHTML = await response.text();
                    this.modalElements.details.innerHTML = detailsHTML;
                } else {
                    // If not ok and status is not 0, then it's a more definite error (e.g., 404)
                    console.error(`Failed to load details from ${api.detailsPath}. Status: ${response.status}, StatusText: ${response.statusText}`);
                    throw new Error(`HTTP error! status: ${response.status} for path ${api.detailsPath}`);
                }
            } catch (error) {
                console.error('Error fetching API details:', error);
                this.modalElements.details.innerHTML = '<p>Error loading details.</p>';
            }
        } else {
            // Fallback or error if detailsPath is not defined
            this.modalElements.details.innerHTML = '<p>Details not available.</p>';
        }
        
        this.modalElements.overlay.classList.add('active');
        
        this.modalElements.content.style.transform = 'translate(-50%, -50%) scale(0.3) rotateY(90deg)';
        this.modalElements.content.style.opacity = '0';
        
        setTimeout(() => {
            this.modalElements.content.style.transition = 'all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275)';
            this.modalElements.content.style.transform = 'translate(-50%, -50%) scale(1) rotateY(0deg)';
        }, 50);
        
        setTimeout(() => {
            this.modalElements.content.style.opacity = '1';
        }, 100);
        
        setTimeout(() => {
            const codeBlocks = this.modalElements.details.querySelectorAll('pre');
            codeBlocks.forEach((block, i) => {
                block.style.opacity = '0';
                block.style.transform = 'translateY(20px)';
                setTimeout(() => {
                    block.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
                    block.style.opacity = '1';
                    block.style.transform = 'translateY(0)';
                }, i * 100);
            });
        }, 400);
    }

    closeModal() {
        this.modalElements.content.style.transition = 'all 0.3s cubic-bezier(0.4, 0, 1, 1)';
        this.modalElements.content.style.transform = 'translate(-50%, -50%) scale(0.8) rotateY(-15deg)';
        this.modalElements.content.style.opacity = '0';
        
        setTimeout(() => {
            this.modalElements.overlay.classList.remove('active');
        }, 300);
    }

    _createOceanVisualEffects() {
        this._createFloatingBubbles();
        this._addWaveParticles();
    }

    _createFloatingBubbles() {
        const bubbleContainer = document.createElement('div');
        bubbleContainer.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 1;
            overflow: hidden;
        `;
        document.body.appendChild(bubbleContainer);

        for (let i = 0; i < 15; i++) {
            this._createBubble(bubbleContainer);
        }
        setInterval(() => this._createBubble(bubbleContainer), 3000);
    }

    _createBubble(container) {
        const bubble = document.createElement('div');
        const size = Math.random() * 30 + 10;
        const startX = Math.random() * window.innerWidth;
        const duration = Math.random() * 8000 + 5000;
        const opacity = Math.random() * 0.3 + 0.1;

        bubble.style.cssText = `
            position: absolute;
            bottom: -50px;
            left: ${startX}px;
            width: ${size}px;
            height: ${size}px;
            background: radial-gradient(circle, rgba(56, 189, 248, ${opacity}) 0%, transparent 70%);
            border-radius: 50%;
            animation: ocean-bubble-rise ${duration}ms linear forwards;
        `;
        
        // Ensure keyframes are defined only once or are unique if params change
        if (!document.getElementById('ocean-bubble-rise-keyframes')) {
            const style = document.createElement('style');
            style.id = 'ocean-bubble-rise-keyframes';
            // Generic keyframe, actual Y translation handled by JS if needed, or keep as is if window.innerHeight is fairly static
            style.textContent = `
                @keyframes ocean-bubble-rise {
                    to {
                        transform: translateY(-${window.innerHeight + 100}px) translateX(${Math.random() * 200 - 100}px);
                        opacity: 0;
                    }
                }
            `; // Note: Math.random() in keyframes means it's fixed at definition time.
               // For truly dynamic end X positions per bubble, JS animation is better.
               // Given the current structure, this will create one version of keyframes.
            document.head.appendChild(style);
        }

        container.appendChild(bubble);
        setTimeout(() => bubble.remove(), duration);
    }

    _addWaveParticles() {
        this.particleCanvas = document.createElement('canvas');
        this.particleCanvas.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 0;
            opacity: 0.3;
        `;
        document.body.appendChild(this.particleCanvas);
        this.particleCtx = this.particleCanvas.getContext('2d');

        this._resizeParticleCanvas(); // Initial size
        this._createInitialParticles();
        this._animateParticles();
    }

    _resizeParticleCanvas() {
        if (!this.particleCanvas) return;
        this.particleCanvas.width = window.innerWidth;
        this.particleCanvas.height = window.innerHeight;
    }

    _createInitialParticles() {
        const particleCount = 50;
        for (let i = 0; i < particleCount; i++) {
            this.particles.push({
                x: Math.random() * this.particleCanvas.width,
                y: Math.random() * this.particleCanvas.height,
                radius: Math.random() * 1.5 + 0.5,
                vx: Math.random() * 0.4 - 0.2, // Slower horizontal movement
                vy: Math.random() * 0.6 - 0.3, // Slower vertical movement
                color: 'rgba(200, 220, 255, 0.5)'
            });
        }
    }

    _animateParticles() {
        if (!this.particleCtx || !this.particleCanvas) return;
        this.particleCtx.clearRect(0, 0, this.particleCanvas.width, this.particleCanvas.height);

        this.particles.forEach(p => {
            p.x += p.vx;
            p.y += p.vy;

            if (p.x < 0 || p.x > this.particleCanvas.width) p.vx *= -1;
            if (p.y < 0 || p.y > this.particleCanvas.height) p.vy *= -1;

            this.particleCtx.beginPath();
            this.particleCtx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
            this.particleCtx.fillStyle = p.color;
            this.particleCtx.fill();
        });

        this.particleAnimationId = requestAnimationFrame(() => this._animateParticles());
    }

    _setupMouseRippleEffect() {
        document.addEventListener('mousemove', (e) => {
            this._createMouseRipple(e.clientX, e.clientY);
        });

        const rippleStyle = document.createElement('style');
        // Ensure ID to prevent multiple appends if this method were called multiple times
        rippleStyle.id = 'ocean-mouse-ripple-keyframes'; 
        if (!document.getElementById(rippleStyle.id)) {
            rippleStyle.textContent = `
                @keyframes ocean-mouse-ripple {
                    to {
                        transform: scale(3);
                        opacity: 0;
                    }
                }
            `;
            document.head.appendChild(rippleStyle);
        }
    }

    _createMouseRipple(x, y) {
        const ripple = document.createElement('div');
        ripple.style.cssText = `
            position: fixed;
            left: ${x}px;
            top: ${y}px;
            width: 30px;
            height: 30px;
            background: rgba(56, 189, 248, 0.3);
            border-radius: 50%;
            transform: translate(-50%, -50%) scale(0);
            animation: ocean-mouse-ripple 0.7s ease-out;
            pointer-events: none;
            z-index: 999;
        `;
        document.body.appendChild(ripple);
        setTimeout(() => ripple.remove(), 700);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.oceanExplorer = new OceanAPIExplorer();
});
