// 海洋主题交互脚本

class OceanAPIExplorer {
    constructor() {
        this.init();
    }

    init() {
        this.createAPIBlocks();
        this.setupEventListeners();
        this.createOceanEffects();
    }

    // 创建API服务木块
    createAPIBlocks() {
        const apisData = [
            {
                id: 'marked',
                icon: '📝',
                title: 'Marked API',
                description: 'Markdown 转 HTML',
                details: this.getMarkedDetails()
            },
            {
                id: 'beautifulsoup',
                icon: '🥄',
                title: 'Beautiful Soup API',
                description: 'HTML 解析与提取',
                details: this.getBeautifulSoupDetails()
            }
        ];

        const container = document.querySelector('.apis-ocean');
        apisData.forEach((api, index) => {
            const block = this.createAPIBlock(api, index);
            container.appendChild(block);
        });
    }

    createAPIBlock(api, index) {
        const block = document.createElement('div');
        block.className = 'api-floating-block';
        block.dataset.apiId = api.id;
        
        // 随机位置和动画延迟
        const randomDelay = Math.random() * 2;
        const randomDuration = 3 + Math.random() * 2;
        block.style.animationDelay = `${randomDelay}s`;
        block.style.animationDuration = `${randomDuration}s`;

        block.innerHTML = `
            <div class="api-block-content">
                <div class="api-block-icon">${api.icon}</div>
                <div class="api-block-title">${api.title}</div>
                <div class="api-block-desc">${api.description}</div>
            </div>
        `;

        block.addEventListener('click', () => this.openModal(api));
        
        return block;
    }

    // 设置事件监听器
    setupEventListeners() {
        // 创建模态框
        this.createModal();
        
        // ESC 键关闭模态框
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeModal();
            }
        });

        // 点击遮罩关闭模态框
        const overlay = document.querySelector('.modal-overlay');
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                this.closeModal();
            }
        });
    }

    // 创建模态框HTML
    createModal() {
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
        
        // 绑定关闭按钮事件
        document.querySelector('.modal-close').addEventListener('click', () => {
            this.closeModal();
        });
    }    // 打开模态框
    openModal(api) {
        const overlay = document.querySelector('.modal-overlay');
        const title = document.querySelector('.modal-title');
        const details = document.querySelector('.api-details');
        
        title.textContent = api.title;
        details.innerHTML = api.details;
        
        // 添加打开动画序列
        overlay.classList.add('active');
        document.body.style.overflow = 'hidden';
        
        // 创建波浪展开效果
        const content = document.querySelector('.modal-content');
        content.style.transform = 'translate(-50%, -50%) scale(0.3) rotateY(90deg)';
        content.style.opacity = '0';
        
        setTimeout(() => {
            content.style.transition = 'all 0.6s cubic-bezier(0.34, 1.56, 0.64, 1)';
            content.style.transform = 'translate(-50%, -50%) scale(1) rotateY(0deg)';
            content.style.opacity = '1';
        }, 50);
        
        // 添加内容淡入动画
        setTimeout(() => {
            const apiDetails = document.querySelector('.api-details');
            apiDetails.style.opacity = '0';
            apiDetails.style.transform = 'translateY(20px)';
            
            setTimeout(() => {
                apiDetails.style.transition = 'all 0.4s ease-out';
                apiDetails.style.opacity = '1';
                apiDetails.style.transform = 'translateY(0)';
            }, 200);
        }, 100);
        
        // 添加代码块动画
        setTimeout(() => {
            const codeBlocks = document.querySelectorAll('.modal-body pre, .modal-body code');
            codeBlocks.forEach((block, index) => {
                block.style.opacity = '0';
                block.style.transform = 'translateX(-20px)';
                
                setTimeout(() => {
                    block.style.transition = 'all 0.3s ease-out';
                    block.style.opacity = '1';
                    block.style.transform = 'translateX(0)';
                }, index * 100);
            });
        }, 400);
    }    // 关闭模态框
    closeModal() {
        const overlay = document.querySelector('.modal-overlay');
        const content = document.querySelector('.modal-content');
        
        // 添加关闭动画
        content.style.transition = 'all 0.3s cubic-bezier(0.4, 0, 1, 1)';
        content.style.transform = 'translate(-50%, -50%) scale(0.8) rotateY(-15deg)';
        content.style.opacity = '0';
        
        setTimeout(() => {
            overlay.classList.remove('active');
            document.body.style.overflow = '';
            
            // 重置样式
            content.style.transition = '';
            content.style.transform = '';
            content.style.opacity = '';
        }, 300);
    }

    // 创建海洋特效
    createOceanEffects() {
        this.createFloatingBubbles();
        this.addWaveParticles();
    }

    // 创建漂浮气泡
    createFloatingBubbles() {
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

        // 创建多个气泡
        for (let i = 0; i < 15; i++) {
            setTimeout(() => {
                this.createBubble(bubbleContainer);
            }, i * 1000);
        }

        // 定期创建新气泡
        setInterval(() => {
            this.createBubble(bubbleContainer);
        }, 3000);
    }

    createBubble(container) {
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
            animation: bubble-rise ${duration}ms linear forwards;
        `;

        // 添加气泡上升动画
        const style = document.createElement('style');
        style.textContent = `
            @keyframes bubble-rise {
                to {
                    transform: translateY(-${window.innerHeight + 100}px) translateX(${Math.random() * 200 - 100}px);
                    opacity: 0;
                }
            }
        `;
        document.head.appendChild(style);

        container.appendChild(bubble);

        // 动画结束后移除气泡
        setTimeout(() => {
            if (bubble.parentNode) {
                bubble.parentNode.removeChild(bubble);
            }
            if (style.parentNode) {
                style.parentNode.removeChild(style);
            }
        }, duration);
    }

    // 添加波浪粒子效果
    addWaveParticles() {
        const canvas = document.createElement('canvas');
        canvas.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 0;
            opacity: 0.3;
        `;
        document.body.appendChild(canvas);

        const ctx = canvas.getContext('2d');
        let animationId;

        const resizeCanvas = () => {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        };

        const particles = [];
        const particleCount = 50;

        // 初始化粒子
        for (let i = 0; i < particleCount; i++) {
            particles.push({
                x: Math.random() * canvas.width,
                y: Math.random() * canvas.height,
                radius: Math.random() * 2 + 1,
                vx: (Math.random() - 0.5) * 0.5,
                vy: (Math.random() - 0.5) * 0.5,
                opacity: Math.random() * 0.5 + 0.2
            });
        }

        const animateParticles = () => {
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            particles.forEach(particle => {
                // 更新位置
                particle.x += particle.vx;
                particle.y += particle.vy;

                // 边界检查
                if (particle.x < 0 || particle.x > canvas.width) particle.vx *= -1;
                if (particle.y < 0 || particle.y > canvas.height) particle.vy *= -1;

                // 绘制粒子
                ctx.beginPath();
                ctx.arc(particle.x, particle.y, particle.radius, 0, Math.PI * 2);
                ctx.fillStyle = `rgba(56, 189, 248, ${particle.opacity})`;
                ctx.fill();
            });

            animationId = requestAnimationFrame(animateParticles);
        };

        resizeCanvas();
        animateParticles();

        window.addEventListener('resize', resizeCanvas);

        // 清理函数
        window.addEventListener('beforeunload', () => {
            if (animationId) {
                cancelAnimationFrame(animationId);
            }
        });
    }    // Marked API 详细信息
    getMarkedDetails() {
        return `
            <h3>📝 Markdown 转 HTML 服务</h3>
            <p>将 Markdown 文本实时转换为 HTML。基于强大的 <a href="https://github.com/markedjs/marked" target="_blank">marked</a> 库。</p>
            
            <p><strong>API 端点:</strong></p>
            <pre><code>POST https://res.allbeapi.top/marked/render</code></pre>

            <div class="code-block">
                <p class="title">请求体 (JSON):</p>
                <pre><code>{
    "markdown": "# 标题\\n\\n这是一段 **Markdown** 文本。"
}</code></pre>
            </div>

            <div class="code-block">
                <p class="title">响应体 (HTML):</p>
                <pre><code>&lt;h1 id="标题"&gt;标题&lt;/h1&gt;
&lt;p&gt;这是一段 &lt;strong&gt;Markdown&lt;/strong&gt; 文本。&lt;/p&gt;</code></pre>
            </div>
            
            <h3>🐍 Python 示例</h3>
            <pre><code>import requests
import json

api_url = "https://res.allbeapi.top/marked/render"
markdown_content = {
    "markdown": "# 测试标题\\n\\n这是从 Python 发送的 **Markdown** 内容。\\n\\n* 列表项 1\\n* 列表项 2"
}

response = requests.post(api_url, json=markdown_content)

if response.status_code == 200:
    html_output = response.text
    print("转换后的 HTML:")
    print(html_output)
else:
    print(f"请求失败，状态码: {response.status_code}")
    print(response.text)</code></pre>

            <h3>🌐 cURL 示例</h3>
            <pre><code>curl -X POST -H "Content-Type: application/json" \\
-d '{"markdown": "# Hello World\\n\\nThis is **bold**."}' \\
https://res.allbeapi.top/marked/render</code></pre>

            <h3>🌐 JavaScript 示例</h3>
            <pre><code>// 使用 fetch API
const markdownContent = {
    markdown: "# 标题\\n\\n这是 **JavaScript** 调用示例。"
};

fetch('https://res.allbeapi.top/marked/render', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify(markdownContent)
})
.then(response => response.text())
.then(html => {
    console.log('转换后的 HTML:', html);
    document.getElementById('output').innerHTML = html;
})
.catch(error => {
    console.error('错误:', error);
});</code></pre>
        `;
    }    // Beautiful Soup API 详细信息
    getBeautifulSoupDetails() {
        return `
            <h3>🥄 HTML 解析与提取服务</h3>
            <p>强大的 HTML/XML 解析工具，提供丰富的文档解析和数据提取功能。基于著名的 <a href="https://github.com/waylan/beautifulsoup" target="_blank">Beautiful Soup</a> 库。</p>
            
            <h3>1. HTML 解析</h3>
            <p><strong>API 端点:</strong></p>
            <pre><code>POST https://res.allbeapi.top/beautifulsoup/parse</code></pre>
            
            <div class="code-block">
                <p class="title">请求体 (JSON):</p>
                <pre><code>{
    "html": "&lt;html&gt;&lt;head&gt;&lt;title&gt;页面标题&lt;/title&gt;&lt;/head&gt;&lt;body&gt;&lt;p&gt;内容&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;",
    "parser": "html.parser"
}</code></pre>
            </div>

            <div class="code-block">
                <p class="title">响应体 (JSON):</p>
                <pre><code>{
    "title": "页面标题",
    "text": "页面标题\\n内容",
    "html": "格式化后的HTML"
}</code></pre>
            </div>

            <h3>2. 元素提取</h3>
            <p><strong>API 端点:</strong></p>
            <pre><code>POST https://res.allbeapi.top/beautifulsoup/extract</code></pre>
            
            <div class="code-block">
                <p class="title">请求体 (JSON):</p>
                <pre><code>{
    "html": "HTML内容",
    "selector": "CSS选择器或标签名",
    "attribute": "属性名（可选）"
}</code></pre>
            </div>

            <h3>3. 链接提取</h3>
            <p><strong>API 端点:</strong></p>
            <pre><code>POST https://res.allbeapi.top/beautifulsoup/links</code></pre>
            
            <div class="code-block">
                <p class="title">请求体 (JSON):</p>
                <pre><code>{
    "html": "HTML内容",
    "base_url": "https://example.com"
}</code></pre>
            </div>

            <h3>4. 图片提取</h3>
            <p><strong>API 端点:</strong></p>
            <pre><code>POST https://res.allbeapi.top/beautifulsoup/images</code></pre>

            <h3>5. HTML 清理</h3>
            <p><strong>API 端点:</strong></p>
            <pre><code>POST https://res.allbeapi.top/beautifulsoup/clean</code></pre>
            
            <div class="code-block">
                <p class="title">请求体 (JSON):</p>
                <pre><code>{
    "html": "HTML内容",
    "remove_tags": ["script", "style"],
    "remove_comments": true
}</code></pre>
            </div>

            <h3>6. 网页抓取</h3>
            <p><strong>API 端点:</strong></p>
            <pre><code>POST https://res.allbeapi.top/beautifulsoup/fetch</code></pre>
            
            <div class="code-block">
                <p class="title">请求体 (JSON):</p>
                <pre><code>{
    "url": "https://example.com",
    "selector": "CSS选择器（可选）"
}</code></pre>
            </div>

            <h3>🐍 Python 示例</h3>
            <pre><code>import requests

# 解析HTML
response = requests.post('https://res.allbeapi.top/beautifulsoup/parse', json={
    "html": "&lt;div&gt;&lt;h1&gt;标题&lt;/h1&gt;&lt;p&gt;段落&lt;/p&gt;&lt;/div&gt;"
})

# 提取所有链接
response = requests.post('https://res.allbeapi.top/beautifulsoup/links', json={
    "html": "&lt;a href='#'&gt;链接1&lt;/a&gt;&lt;a href='/page'&gt;链接2&lt;/a&gt;",
    "base_url": "https://example.com"
})

# 清理HTML
response = requests.post('https://res.allbeapi.top/beautifulsoup/clean', json={
    "html": "&lt;div&gt;&lt;script&gt;alert()&lt;/script&gt;&lt;p&gt;内容&lt;/p&gt;&lt;/div&gt;",
    "remove_tags": ["script"]
})</code></pre>

            <h3>🌐 JavaScript 示例</h3>
            <pre><code>// 解析HTML并提取标题
const htmlContent = {
    html: "&lt;html&gt;&lt;head&gt;&lt;title&gt;我的网页&lt;/title&gt;&lt;/head&gt;&lt;body&gt;&lt;h1&gt;欢迎&lt;/h1&gt;&lt;/body&gt;&lt;/html&gt;"
};

fetch('https://res.allbeapi.top/beautifulsoup/parse', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify(htmlContent)
})
.then(response => response.json())
.then(data => {
    console.log('页面标题:', data.title);
    console.log('文本内容:', data.text);
})
.catch(error => {
    console.error('错误:', error);
});

// 提取所有链接
const linkExtraction = {
    html: "&lt;a href='/home'&gt;首页&lt;/a&gt;&lt;a href='/about'&gt;关于我们&lt;/a&gt;",
    base_url: "https://example.com"
};

fetch('https://res.allbeapi.top/beautifulsoup/links', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify(linkExtraction)
})
.then(response => response.json())
.then(links => {
    console.log('提取的链接:', links);
});</code></pre>
        `;
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    // 添加页面加载动画
    document.body.style.opacity = '0';
    document.body.style.transform = 'scale(0.95)';
    
    // 创建加载效果
    const loadingOverlay = document.createElement('div');
    loadingOverlay.style.cssText = `
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
    
    loadingOverlay.innerHTML = `
        <div style="font-size: 3em; margin-bottom: 20px; animation: pulse 2s ease-in-out infinite;">🌊</div>
        <div style="font-size: 1.5em; text-align: center;">
            <div style="margin-bottom: 10px;">开源库API化平台</div>
            <div style="font-size: 0.8em; opacity: 0.7;">正在加载海洋...</div>
        </div>
        <div style="margin-top: 30px; width: 200px; height: 4px; background: rgba(56, 189, 248, 0.2); border-radius: 2px; overflow: hidden;">
            <div style="width: 0%; height: 100%; background: linear-gradient(90deg, #38bdf8, #60a5fa); border-radius: 2px; animation: loading-bar 2s ease-out forwards;"></div>
        </div>
    `;
    
    document.body.appendChild(loadingOverlay);
    
    // 添加加载动画样式
    const style = document.createElement('style');
    style.textContent = `
        @keyframes pulse {
            0%, 100% { transform: scale(1); opacity: 1; }
            50% { transform: scale(1.2); opacity: 0.8; }
        }
        @keyframes loading-bar {
            to { width: 100%; }
        }
    `;
    document.head.appendChild(style);
    
    // 初始化主应用
    setTimeout(() => {
        new OceanAPIExplorer();
        
        // 移除加载屏幕
        setTimeout(() => {
            loadingOverlay.style.transition = 'opacity 0.8s ease-out';
            loadingOverlay.style.opacity = '0';
            
            // 显示主内容
            document.body.style.transition = 'opacity 1s ease-in-out, transform 1s ease-in-out';
            document.body.style.opacity = '1';
            document.body.style.transform = 'scale(1)';
            
            setTimeout(() => {
                if (loadingOverlay.parentNode) {
                    loadingOverlay.parentNode.removeChild(loadingOverlay);
                }
                if (style.parentNode) {
                    style.parentNode.removeChild(style);
                }
            }, 800);
        }, 500);
    }, 2000);
    
    // 添加鼠标跟踪水波效果
    let mouseX = 0, mouseY = 0;
    document.addEventListener('mousemove', (e) => {
        mouseX = e.clientX;
        mouseY = e.clientY;
        
        // 创建鼠标跟踪的水波纹
        if (Math.random() < 0.1) { // 减少频率
            createMouseRipple(mouseX, mouseY);
        }
    });
    
    function createMouseRipple(x, y) {
        const ripple = document.createElement('div');
        ripple.style.cssText = `
            position: fixed;
            left: ${x - 10}px;
            top: ${y - 10}px;
            width: 20px;
            height: 20px;
            border: 2px solid rgba(56, 189, 248, 0.5);
            border-radius: 50%;
            pointer-events: none;
            z-index: 100;
            animation: mouse-ripple 1.5s ease-out forwards;
        `;
        
        document.body.appendChild(ripple);
        
        setTimeout(() => {
            if (ripple.parentNode) {
                ripple.parentNode.removeChild(ripple);
            }
        }, 1500);
    }
    
    // 添加鼠标波纹动画
    const rippleStyle = document.createElement('style');
    rippleStyle.textContent = `
        @keyframes mouse-ripple {
            to {
                transform: scale(3);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(rippleStyle);
});

// 导出供其他脚本使用
window.OceanAPIExplorer = OceanAPIExplorer;
