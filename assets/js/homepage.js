/**
 * AllBeAPI Platform - 增强交互功能
 */

class AllBeAPIHomepage {
    constructor() {
        this.init();
    }

    init() {
        this.setupScrollIndicator();
        this.setupSmoothScroll();
        this.setupScrollAnimations();
        this.setupHeaderEffects();
        this.setupTypewriter();
        this.setupParticles();
        this.setupThemeToggle();
        this.setupAPIDemo();
    }

    // 滚动进度指示器
    setupScrollIndicator() {
        const indicator = document.getElementById('scroll-indicator');
        if (!indicator) return;

        window.addEventListener('scroll', () => {
            const scrolled = (window.pageYOffset / (document.documentElement.scrollHeight - window.innerHeight)) * 100;
            indicator.style.transform = `scaleX(${Math.min(scrolled, 100)}%)`;
        });
    }

    // 平滑滚动
    setupSmoothScroll() {
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', (e) => {
                e.preventDefault();
                const target = document.querySelector(anchor.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
    }

    // 滚动动画
    setupScrollAnimations() {
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-on-scroll');
                    // 为数字添加计数动画
                    if (entry.target.classList.contains('stat-item')) {
                        this.animateCounter(entry.target);
                    }
                }
            });
        }, observerOptions);

        document.querySelectorAll('.feature-card, .stat-item, .code-block').forEach(el => {
            observer.observe(el);
        });
    }

    // 数字计数动画
    animateCounter(element) {
        const counter = element.querySelector('h3');
        if (!counter || counter.dataset.animated) return;

        counter.dataset.animated = 'true';
        const text = counter.textContent;
        const isInfinity = text === '∞';
        
        if (isInfinity) {
            counter.style.transform = 'rotate(90deg)';
            return;
        }

        const number = parseFloat(text.replace(/[^0-9.]/g, ''));
        const suffix = text.replace(/[0-9.]/g, '');
        
        let current = 0;
        const increment = number / 50;
        const timer = setInterval(() => {
            current += increment;
            if (current >= number) {
                current = number;
                clearInterval(timer);
            }
            counter.textContent = Math.floor(current) + suffix;
        }, 30);
    }

    // Header效果
    setupHeaderEffects() {
        const header = document.querySelector('header');
        if (!header) return;

        window.addEventListener('scroll', () => {
            if (window.scrollY > 100) {
                header.style.background = 'rgba(255, 255, 255, 0.98)';
                header.style.boxShadow = '0 4px 6px -1px rgba(0, 0, 0, 0.1)';
            } else {
                header.style.background = 'rgba(255, 255, 255, 0.95)';
                header.style.boxShadow = 'none';
            }
        });
    }

    // 打字机效果
    setupTypewriter() {
        const subtitle = document.querySelector('.hero .subtitle');
        if (!subtitle) return;

        const text = subtitle.textContent;
        subtitle.textContent = '';
        subtitle.style.borderRight = '2px solid white';
        
        let i = 0;
        const typeWriter = () => {
            if (i < text.length) {
                subtitle.textContent += text.charAt(i);
                i++;
                setTimeout(typeWriter, 50);
            } else {
                setTimeout(() => {
                    subtitle.style.borderRight = 'none';
                }, 1000);
            }
        };

        // 延迟开始打字机效果
        setTimeout(typeWriter, 1000);
    }

    // 粒子背景效果
    setupParticles() {
        const hero = document.querySelector('.hero');
        if (!hero) return;

        const canvas = document.createElement('canvas');
        canvas.style.position = 'absolute';
        canvas.style.top = '0';
        canvas.style.left = '0';
        canvas.style.width = '100%';
        canvas.style.height = '100%';
        canvas.style.pointerEvents = 'none';
        canvas.style.opacity = '0.3';
        hero.appendChild(canvas);

        const ctx = canvas.getContext('2d');
        let particles = [];

        const resizeCanvas = () => {
            canvas.width = hero.offsetWidth;
            canvas.height = hero.offsetHeight;
        };

        const createParticles = () => {
            particles = [];
            for (let i = 0; i < 50; i++) {
                particles.push({
                    x: Math.random() * canvas.width,
                    y: Math.random() * canvas.height,
                    radius: Math.random() * 3 + 1,
                    speedX: (Math.random() - 0.5) * 0.5,
                    speedY: (Math.random() - 0.5) * 0.5,
                    opacity: Math.random() * 0.8 + 0.2
                });
            }
        };

        const animate = () => {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            
            particles.forEach(particle => {
                particle.x += particle.speedX;
                particle.y += particle.speedY;

                if (particle.x < 0 || particle.x > canvas.width) particle.speedX *= -1;
                if (particle.y < 0 || particle.y > canvas.height) particle.speedY *= -1;

                ctx.beginPath();
                ctx.arc(particle.x, particle.y, particle.radius, 0, Math.PI * 2);
                ctx.fillStyle = `rgba(255, 255, 255, ${particle.opacity})`;
                ctx.fill();
            });

            requestAnimationFrame(animate);
        };

        resizeCanvas();
        createParticles();
        animate();

        window.addEventListener('resize', () => {
            resizeCanvas();
            createParticles();
        });
    }

    // 主题切换
    setupThemeToggle() {
        const themeToggle = document.createElement('button');
        themeToggle.innerHTML = '🌙';
        themeToggle.style.cssText = `
            position: fixed;
            top: 50%;
            right: 20px;
            transform: translateY(-50%);
            background: var(--gradient-primary);
            border: none;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            font-size: 20px;
            cursor: pointer;
            z-index: 1000;
            box-shadow: var(--shadow);
            transition: all 0.3s ease;
        `;

        themeToggle.addEventListener('click', () => {
            document.body.classList.toggle('dark-theme');
            themeToggle.innerHTML = document.body.classList.contains('dark-theme') ? '☀️' : '🌙';
        });

        document.body.appendChild(themeToggle);
    }

    // API演示功能
    setupAPIDemo() {
        const demoButton = document.createElement('button');
        demoButton.textContent = '🚀 试用API';
        demoButton.className = 'demo-button';
        demoButton.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: var(--gradient-primary);
            color: white;
            border: none;
            padding: 12px 20px;
            border-radius: 25px;
            font-weight: 600;
            cursor: pointer;
            z-index: 1000;
            box-shadow: var(--shadow-lg);
            transition: all 0.3s ease;
        `;

        demoButton.addEventListener('click', () => {
            this.showAPIDemo();
        });

        demoButton.addEventListener('mouseenter', () => {
            demoButton.style.transform = 'translateY(-3px) scale(1.05)';
        });

        demoButton.addEventListener('mouseleave', () => {
            demoButton.style.transform = 'translateY(0) scale(1)';
        });

        document.body.appendChild(demoButton);
    }

    // 显示API演示弹窗
    showAPIDemo() {
        const modal = document.createElement('div');
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.8);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 10000;
            opacity: 0;
            transition: opacity 0.3s ease;
        `;

        const content = document.createElement('div');
        content.style.cssText = `
            background: white;
            padding: 2rem;
            border-radius: 1rem;
            max-width: 600px;
            width: 90%;
            max-height: 80vh;
            overflow-y: auto;
            position: relative;
            transform: translateY(20px);
            transition: transform 0.3s ease;
        `;

        content.innerHTML = `
            <button onclick="this.closest('.demo-modal').remove()" style="
                position: absolute;
                top: 1rem;
                right: 1rem;
                background: none;
                border: none;
                font-size: 24px;
                cursor: pointer;
                color: #6b7280;
            ">×</button>
            <h2 style="margin-bottom: 1rem; color: var(--text-primary);">API 快速体验</h2>
            <p style="margin-bottom: 2rem; color: var(--text-secondary);">选择一个API服务进行快速体验：</p>
            
            <div style="display: grid; gap: 1rem;">
                <button class="api-test-btn" data-api="tensorflowjs">
                    🧠 TensorFlow.js - 图像分类
                </button>
                <button class="api-test-btn" data-api="opencv">
                    🎨 OpenCV - 图像处理
                </button>
                <button class="api-test-btn" data-api="threejs">
                    🎮 Three.js - 3D渲染
                </button>
                <button class="api-test-btn" data-api="tools">
                    🛠️ 开发工具 - 代码检查
                </button>
            </div>
            
            <div id="demo-result" style="margin-top: 2rem; display: none;">
                <h3>API响应结果：</h3>
                <pre id="result-content" style="
                    background: #f3f4f6;
                    padding: 1rem;
                    border-radius: 0.5rem;
                    overflow-x: auto;
                    font-size: 0.875rem;
                "></pre>
            </div>
        `;

        modal.appendChild(content);
        modal.className = 'demo-modal';
        document.body.appendChild(modal);

        // 添加按钮样式
        const style = document.createElement('style');
        style.textContent = `
            .api-test-btn {
                background: var(--gradient-primary);
                color: white;
                border: none;
                padding: 1rem;
                border-radius: 0.5rem;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
            }
            .api-test-btn:hover {
                transform: translateY(-2px);
                box-shadow: var(--shadow-lg);
            }
        `;
        document.head.appendChild(style);

        // 动画显示
        setTimeout(() => {
            modal.style.opacity = '1';
            content.style.transform = 'translateY(0)';
        }, 10);

        // 添加API测试功能
        content.querySelectorAll('.api-test-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                this.testAPI(btn.dataset.api);
            });
        });
    }

    // 测试API功能
    async testAPI(apiType) {
        const resultDiv = document.getElementById('demo-result');
        const resultContent = document.getElementById('result-content');
        
        resultDiv.style.display = 'block';
        resultContent.textContent = '正在调用API...';

        // 模拟API调用
        setTimeout(() => {
            const mockResults = {
                tensorflowjs: {
                    success: true,
                    predictions: [
                        { className: 'cat', probability: 0.95 },
                        { className: 'dog', probability: 0.03 },
                        { className: 'bird', probability: 0.02 }
                    ],
                    processingTime: '245ms'
                },
                opencv: {
                    success: true,
                    operations: ['blur', 'edge_detection'],
                    outputFormat: 'PNG',
                    processingTime: '156ms',
                    fileSize: '2.3MB'
                },
                threejs: {
                    success: true,
                    scene: {
                        objects: 3,
                        lights: 2,
                        vertices: 1024,
                        triangles: 512
                    },
                    renderTime: '89ms'
                },
                tools: {
                    success: true,
                    eslint: {
                        errors: 0,
                        warnings: 2,
                        fixableIssues: 1
                    },
                    processingTime: '67ms'
                }
            };

            resultContent.textContent = JSON.stringify(mockResults[apiType], null, 2);
        }, 1000);
    }

    // 添加错误处理
    handleError(error) {
        console.error('AllBeAPI Homepage Error:', error);
    }
}

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    try {
        new AllBeAPIHomepage();
    } catch (error) {
        console.error('Failed to initialize AllBeAPI Homepage:', error);
    }
});

// 导出到全局
window.AllBeAPIHomepage = AllBeAPIHomepage;
