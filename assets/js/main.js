// AllBeAPI - Main JavaScript
class AllBeAPIWebsite {
    constructor() {
        this.init();
    }

    init() {
        this.setupThemeToggle();
        this.setupCodeTabs();
        this.setupCopyButtons();
        this.setupScrollEffects();
        this.setupMobileMenu();
        this.setupLanguageSwitch();
    }

    // Theme Toggle Functionality
    setupThemeToggle() {
        const themeToggle = document.querySelector('.theme-toggle');
        const currentTheme = localStorage.getItem('theme') || 'light';
        
        // Set initial theme
        document.documentElement.setAttribute('data-theme', currentTheme);
        this.updateThemeToggleIcon(currentTheme);

        if (themeToggle) {
            themeToggle.addEventListener('click', () => {
                const current = document.documentElement.getAttribute('data-theme');
                const newTheme = current === 'dark' ? 'light' : 'dark';
                
                document.documentElement.setAttribute('data-theme', newTheme);
                localStorage.setItem('theme', newTheme);
                this.updateThemeToggleIcon(newTheme);
            });
        }
    }

    updateThemeToggleIcon(theme) {
        const themeToggle = document.querySelector('.theme-toggle');
        if (themeToggle) {
            themeToggle.innerHTML = theme === 'dark' ? '☀️' : '🌙';
            themeToggle.setAttribute('aria-label', `Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`);
        }
    }

    // Code Tabs Functionality
    setupCodeTabs() {
        const codeTabs = document.querySelectorAll('.code-tabs');
        
        codeTabs.forEach(tabContainer => {
            const tabs = tabContainer.querySelectorAll('.code-tab');
            const contents = tabContainer.parentElement.querySelectorAll('.code-content > .code-block');
            
            tabs.forEach((tab, index) => {
                tab.addEventListener('click', () => {
                    // Remove active class from all tabs and contents
                    tabs.forEach(t => t.classList.remove('active'));
                    contents.forEach(c => c.style.display = 'none');
                    
                    // Add active class to clicked tab and corresponding content
                    tab.classList.add('active');
                    if (contents[index]) {
                        contents[index].style.display = 'block';
                    }
                });
            });
            
            // Initialize first tab as active
            if (tabs.length > 0) {
                tabs[0].classList.add('active');
                if (contents[0]) {
                    contents[0].style.display = 'block';
                }
            }
        });
    }

    // Copy Code Functionality
    setupCopyButtons() {
        const codeBlocks = document.querySelectorAll('.code-block');
        
        codeBlocks.forEach(block => {
            const copyButton = document.createElement('button');
            copyButton.className = 'copy-button';
            copyButton.textContent = 'Copy';
            copyButton.setAttribute('aria-label', 'Copy code to clipboard');
            
            copyButton.addEventListener('click', async () => {
                const code = block.textContent;
                
                try {
                    await navigator.clipboard.writeText(code);
                    copyButton.textContent = 'Copied!';
                    copyButton.style.background = 'rgba(40, 167, 69, 0.8)';
                    
                    setTimeout(() => {
                        copyButton.textContent = 'Copy';
                        copyButton.style.background = '';
                    }, 2000);
                } catch (err) {
                    // Fallback for older browsers
                    this.fallbackCopyToClipboard(code);
                    copyButton.textContent = 'Copied!';
                    setTimeout(() => {
                        copyButton.textContent = 'Copy';
                    }, 2000);
                }
            });
            
            block.style.position = 'relative';
            block.appendChild(copyButton);
        });
    }

    fallbackCopyToClipboard(text) {
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        document.execCommand('copy');
        textArea.remove();
    }

    // Scroll Effects
    setupScrollEffects() {
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('fade-in-up');
                }
            });
        }, observerOptions);

        // Observe elements that should animate on scroll
        const animatedElements = document.querySelectorAll('.feature-card, .api-card, .stat-card');
        animatedElements.forEach(el => {
            observer.observe(el);
        });

        // Navbar scroll effect
        const navbar = document.querySelector('.navbar');
        if (navbar) {
            window.addEventListener('scroll', () => {
                if (window.scrollY > 50) {
                    navbar.style.background = 'rgba(255, 255, 255, 0.98)';
                    navbar.style.backdropFilter = 'blur(20px)';
                    navbar.style.boxShadow = '0 2px 20px rgba(0,0,0,0.1)';
                } else {
                    navbar.style.background = 'rgba(255, 255, 255, 0.95)';
                    navbar.style.backdropFilter = 'blur(10px)';
                    navbar.style.boxShadow = 'none';
                }
            });
        }
    }

    // Mobile Menu
    setupMobileMenu() {
        const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
        const navbarNav = document.querySelector('.navbar-nav');
        
        if (mobileMenuToggle && navbarNav) {
            mobileMenuToggle.addEventListener('click', () => {
                navbarNav.classList.toggle('active');
                mobileMenuToggle.classList.toggle('active');
            });

            // Close menu when clicking outside
            document.addEventListener('click', (e) => {
                if (!mobileMenuToggle.contains(e.target) && !navbarNav.contains(e.target)) {
                    navbarNav.classList.remove('active');
                    mobileMenuToggle.classList.remove('active');
                }
            });
        }
    }

    // Language Switch
    setupLanguageSwitch() {
        const currentPath = window.location.pathname;
        const languageLinks = document.querySelectorAll('.language-switch a');
        
        languageLinks.forEach(link => {
            const href = link.getAttribute('href');
            if (currentPath.includes(href) || (href === 'index.html' && currentPath === '/')) {
                link.classList.add('active');
            }
        });
    }

    // Utility method for smooth scrolling
    smoothScrollTo(elementId) {
        const element = document.getElementById(elementId);
        if (element) {
            element.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    }

    // API Demo functionality
    async demoAPI(service, method, params = {}) {
        const demoOutput = document.getElementById('demo-output');
        if (!demoOutput) return;

        demoOutput.innerHTML = '<div class="loading">Loading...</div>';
        
        try {
            // This would integrate with the actual AllBeAPI
            const apiClient = new AllBeApi();
            let result;
            
            switch(service) {
                case 'marked':
                    result = await apiClient.marked.render(params.markdown || '# Hello AllBeAPI');
                    break;
                case 'qrcode':
                    result = await apiClient.pythonQrcode.generateQrcode(params.data || 'https://allbeapi.com');
                    break;
                default:
                    result = { message: 'Demo not implemented for this service' };
            }
            
            demoOutput.innerHTML = `<pre><code>${JSON.stringify(result, null, 2)}</code></pre>`;
        } catch (error) {
            demoOutput.innerHTML = `<div class="alert alert-danger">Error: ${error.message}</div>`;
        }
    }
}

// Analytics and Performance
class WebsiteAnalytics {
    constructor() {
        this.startTime = performance.now();
        this.setupPerformanceTracking();
    }

    setupPerformanceTracking() {
        window.addEventListener('load', () => {
            const loadTime = performance.now() - this.startTime;
            console.log(`Page loaded in ${loadTime.toFixed(2)}ms`);
            
            // Track performance metrics
            if ('performance' in window && 'getEntriesByType' in performance) {
                const navigation = performance.getEntriesByType('navigation')[0];
                if (navigation) {
                    this.trackMetrics({
                        loadTime: navigation.loadEventEnd - navigation.loadEventStart,
                        domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
                        firstPaint: this.getFirstPaint()
                    });
                }
            }
        });
    }

    getFirstPaint() {
        const paintEntries = performance.getEntriesByType('paint');
        const firstPaint = paintEntries.find(entry => entry.name === 'first-contentful-paint');
        return firstPaint ? firstPaint.startTime : null;
    }

    trackMetrics(metrics) {
        // This could send data to analytics service
        console.log('Performance metrics:', metrics);
    }

    trackEvent(eventName, parameters = {}) {
        // This could integrate with Google Analytics, etc.
        console.log(`Event: ${eventName}`, parameters);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    const website = new AllBeAPIWebsite();
    const analytics = new WebsiteAnalytics();
    
    // Make instances globally available for debugging
    window.allbeapiWebsite = website;
    window.allbeapiAnalytics = analytics;
    
    // Track page view
    analytics.trackEvent('page_view', {
        page: window.location.pathname,
        title: document.title
    });
});

// Service Worker Registration (for PWA features)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
            .then(registration => {
                console.log('SW registered: ', registration);
            })
            .catch(registrationError => {
                console.log('SW registration failed: ', registrationError);
            });
    });
}
