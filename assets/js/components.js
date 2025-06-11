// Components JavaScript for AllBeAPI
(function() {
    'use strict';

    // Component initialization
    window.initializeComponents = function() {
        initThemeToggle();
        initSmoothScrolling();
        initBackToTop();
        initTabs();
        initDemoInteractions();
        initGitHubStats();
        initAnimations();
    };

    // Theme Toggle
    function initThemeToggle() {
        const themeToggle = document.querySelector('.theme-toggle');
        if (!themeToggle) return;

        themeToggle.addEventListener('click', () => {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            
            // Update toggle icon
            updateThemeIcon(newTheme);
        });

        // Initial icon setup
        updateThemeIcon(document.documentElement.getAttribute('data-theme'));
    }

    function updateThemeIcon(theme) {
        const toggle = document.querySelector('.theme-toggle');
        if (!toggle) return;

        const darkIcon = toggle.querySelector('.theme-icon-dark');
        const lightIcon = toggle.querySelector('.theme-icon-light');
        
        if (theme === 'dark') {
            if (darkIcon) darkIcon.style.display = 'none';
            if (lightIcon) lightIcon.style.display = 'inline';
        } else {
            if (darkIcon) darkIcon.style.display = 'inline';
            if (lightIcon) lightIcon.style.display = 'none';
        }
    }

    // Smooth Scrolling
    function initSmoothScrolling() {
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
    }

    // Back to Top Button
    function initBackToTop() {
        const backToTop = document.getElementById('back-to-top');
        if (!backToTop) return;

        window.addEventListener('scroll', () => {
            if (window.pageYOffset > 300) {
                backToTop.classList.add('visible');
            } else {
                backToTop.classList.remove('visible');
            }
        });

        backToTop.addEventListener('click', () => {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }

    // Tab System
    function initTabs() {
        // Demo tabs
        document.querySelectorAll('.demo-tab').forEach(tab => {
            tab.addEventListener('click', () => {
                const container = tab.closest('.demo-container') || tab.closest('.about-demo');
                if (!container) return;

                const targetLang = tab.dataset.lang;
                
                // Update active tab
                container.querySelectorAll('.demo-tab').forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                
                // Update active content
                container.querySelectorAll('.demo-code').forEach(code => {
                    code.classList.remove('active');
                    if (code.dataset.lang === targetLang) {
                        code.classList.add('active');
                    }
                });
            });
        });

        // Quickstart tabs
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const container = btn.closest('.quickstart-tabs');
                if (!container) return;

                const targetTab = btn.dataset.tab;
                
                // Update active button
                container.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                
                // Update active pane
                container.querySelectorAll('.tab-pane').forEach(pane => {
                    pane.classList.remove('active');
                    if (pane.dataset.tab === targetTab) {
                        pane.classList.add('active');
                    }
                });
            });
        });
    }

    // Demo Interactions
    function initDemoInteractions() {
        const demoBtn = document.getElementById('demo-btn');
        const demoResult = document.getElementById('demo-result');
        
        if (demoBtn && demoResult) {
            demoBtn.addEventListener('click', async () => {
                demoBtn.textContent = 'Converting...';
                demoBtn.disabled = true;
                
                try {
                    // Simulate API call (replace with actual AllBeAPI call)
                    await new Promise(resolve => setTimeout(resolve, 1000));
                    
                    const markdown = "# Hello AllBeAPI\nThis is a **live demo** of markdown conversion!";
                    const html = `<h1>Hello AllBeAPI</h1>\n<p>This is a <strong>live demo</strong> of markdown conversion!</p>`;
                    
                    demoResult.innerHTML = `
                        <div class="demo-output-content">
                            <h5>Input (Markdown):</h5>
                            <pre><code>${markdown}</code></pre>
                            <h5>Output (HTML):</h5>
                            <pre><code>${escapeHtml(html)}</code></pre>
                            <h5>Rendered Result:</h5>
                            <div class="rendered-output">${html}</div>
                        </div>
                    `;
                } catch (error) {
                    demoResult.innerHTML = `<div class="error">Error: ${error.message}</div>`;
                } finally {
                    demoBtn.textContent = 'Try Markdown Conversion';
                    demoBtn.disabled = false;
                }
            });
        }
    }

    // GitHub Stats
    function initGitHubStats() {
        const statsElements = {
            stars: document.getElementById('github-stars'),
            contributors: document.getElementById('github-contributors'),
            forks: document.getElementById('github-forks'),
            issues: document.getElementById('github-issues')
        };

        // Only fetch if elements exist
        if (Object.values(statsElements).some(el => el)) {
            fetchGitHubStats(statsElements);
        }
    }

    async function fetchGitHubStats(elements) {
        try {
            const response = await fetch('https://api.github.com/repos/TingjiaInFuture/allbeapi');
            const data = await response.json();
            
            if (elements.stars) elements.stars.textContent = data.stargazers_count || '0';
            if (elements.forks) elements.forks.textContent = data.forks_count || '0';
            if (elements.issues) elements.issues.textContent = data.open_issues_count || '0';
            
            // Fetch contributors count separately
            try {
                const contributorsResponse = await fetch('https://api.github.com/repos/TingjiaInFuture/allbeapi/contributors');
                const contributors = await contributorsResponse.json();
                if (elements.contributors && Array.isArray(contributors)) {
                    elements.contributors.textContent = contributors.length;
                }
            } catch (error) {
                console.log('Could not fetch contributors:', error);
                if (elements.contributors) elements.contributors.textContent = '1+';
            }
        } catch (error) {
            console.log('Could not fetch GitHub stats:', error);
            // Set default values
            if (elements.stars) elements.stars.textContent = '⭐';
            if (elements.contributors) elements.contributors.textContent = '1+';
            if (elements.forks) elements.forks.textContent = '🍴';
            if (elements.issues) elements.issues.textContent = '📝';
        }
    }

    // Animations
    function initAnimations() {
        // Intersection Observer for fade-in animations
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-in');
                }
            });
        }, observerOptions);

        // Observe elements for animation
        document.querySelectorAll('.feature-card, .about-card, .contribute-card').forEach(el => {
            observer.observe(el);
        });

        // Parallax effect for hero background
        window.addEventListener('scroll', () => {
            const scrolled = window.pageYOffset;
            const hero = document.querySelector('.hero');
            if (hero) {
                hero.style.transform = `translateY(${scrolled * 0.5}px)`;
            }
        });
    }

    // Utility Functions
    function escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, m => map[m]);
    }

    // Copy to clipboard functionality
    function initCopyButtons() {
        document.querySelectorAll('.code-block').forEach(block => {
            const copyBtn = document.createElement('button');
            copyBtn.className = 'copy-btn';
            copyBtn.innerHTML = '📋';
            copyBtn.title = 'Copy to clipboard';
            
            copyBtn.addEventListener('click', async () => {
                const code = block.querySelector('code').textContent;
                try {
                    await navigator.clipboard.writeText(code);
                    copyBtn.innerHTML = '✅';
                    setTimeout(() => {
                        copyBtn.innerHTML = '📋';
                    }, 2000);
                } catch (error) {
                    console.error('Failed to copy:', error);
                }
            });
            
            block.style.position = 'relative';
            block.appendChild(copyBtn);
        });
    }

    // Initialize copy buttons after components load
    document.addEventListener('DOMContentLoaded', () => {
        setTimeout(initCopyButtons, 500); // Wait for components to load
    });

    // Error handling for component loading
    window.addEventListener('error', (event) => {
        console.error('Component error:', event.error);
    });

    // Performance monitoring
    if ('performance' in window) {
        window.addEventListener('load', () => {
            setTimeout(() => {
                const perfData = performance.getEntriesByType('navigation')[0];
                console.log('Page load time:', perfData.loadEventEnd - perfData.fetchStart, 'ms');
            }, 0);
        });
    }

})();
