// Performance Optimization for Phase 3 Features

// Lazy Loading Implementation
class LazyLoader {
    constructor() {
        this.imageObserver = null;
        this.init();
    }

    init() {
        if ('IntersectionObserver' in window) {
            this.imageObserver = new IntersectionObserver((entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        this.loadImage(img);
                        observer.unobserve(img);
                    }
                });
            }, {
                rootMargin: '50px'
            });

            this.observeImages();
        } else {
            // Fallback for older browsers
            this.loadAllImages();
        }
    }

    observeImages() {
        const lazyImages = document.querySelectorAll('img[data-src]');
        lazyImages.forEach(img => this.imageObserver.observe(img));
    }

    loadImage(img) {
        img.src = img.dataset.src;
        img.removeAttribute('data-src');
        img.classList.remove('loading-skeleton');
        img.classList.add('loaded');
    }

    loadAllImages() {
        const lazyImages = document.querySelectorAll('img[data-src]');
        lazyImages.forEach(img => this.loadImage(img));
    }
}

// Debounce Function for Performance
function debounce(func, wait, immediate) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            timeout = null;
            if (!immediate) func.apply(this, args);
        };
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func.apply(this, args);
    };
}

// Throttle Function for Scroll Events
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Cart Performance Optimizations
class CartOptimizer {
    constructor() {
        this.updateQueue = [];
        this.isUpdating = false;
        this.updateDelay = 300;

        this.init();
    }

    init() {
        this.bindEvents();
        this.preloadCriticalResources();
    }

    bindEvents() {
        // Debounced quantity updates
        document.addEventListener('input', debounce((e) => {
            if (e.target.classList.contains('quantity-input')) {
                this.queueUpdate(e.target);
            }
        }, this.updateDelay));

        // Optimized cart count updates
        document.addEventListener('cartUpdated', (e) => {
            this.updateCartCount(e.detail.count);
        });

        // Prefetch cart data on hover
        const cartLinks = document.querySelectorAll('a[href*="cart"]');
        cartLinks.forEach(link => {
            link.addEventListener('mouseenter', () => {
                this.prefetchCartData();
            }, { once: true });
        });
    }

    queueUpdate(input) {
        const itemId = input.closest('.cart-item').dataset.itemId;
        const quantity = parseInt(input.value);

        // Remove any existing updates for this item
        this.updateQueue = this.updateQueue.filter(update => update.itemId !== itemId);

        // Add new update to queue
        this.updateQueue.push({ itemId, quantity });

        if (!this.isUpdating) {
            this.processUpdateQueue();
        }
    }

    async processUpdateQueue() {
        if (this.updateQueue.length === 0) return;

        this.isUpdating = true;
        const updates = [...this.updateQueue];
        this.updateQueue = [];

        try {
            // Batch multiple updates into single request
            if (updates.length > 1) {
                await this.batchUpdateCart(updates);
            } else {
                await this.updateCartItem(updates[0]);
            }
        } catch (error) {
            console.error('Cart update failed:', error);
            this.showError('Failed to update cart. Please try again.');
        }

        this.isUpdating = false;

        // Process any queued updates
        if (this.updateQueue.length > 0) {
            setTimeout(() => this.processUpdateQueue(), 100);
        }
    }

    async batchUpdateCart(updates) {
        const response = await fetch('/orders/api/cart/batch-update/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken()
            },
            body: JSON.stringify({ updates })
        });

        if (!response.ok) throw new Error('Batch update failed');

        const data = await response.json();
        this.updateCartUI(data);
    }

    async updateCartItem(update) {
        const response = await fetch('/orders/api/cart/update/' + update.itemId + '/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken()
            },
            body: JSON.stringify({ quantity: update.quantity })
        });

        if (!response.ok) throw new Error('Update failed');

        const data = await response.json();
        this.updateCartUI(data);
    }

    updateCartUI(data) {
        // Update cart count in navbar
        const cartCountElements = document.querySelectorAll('.cart-count');
        cartCountElements.forEach(el => {
            el.textContent = data.cart_count;
            if (data.cart_count > 0) {
                el.classList.remove('hidden');
            } else {
                el.classList.add('hidden');
            }
        });

        // Update cart total
        const cartTotalElements = document.querySelectorAll('.cart-total');
        cartTotalElements.forEach(el => {
            el.textContent = '₹' + data.cart_total;
        });

        // Dispatch custom event
        document.dispatchEvent(new CustomEvent('cartUpdated', {
            detail: { count: data.cart_count, total: data.cart_total }
        }));
    }

    prefetchCartData() {
        fetch('/orders/api/cart/summary/', {
            method: 'GET',
            headers: {
                'X-CSRFToken': this.getCSRFToken()
            }
        }).then(response => response.json())
          .then(data => {
              // Cache the data for instant cart page load
              sessionStorage.setItem('cartData', JSON.stringify(data));
          })
          .catch(error => console.warn('Cart prefetch failed:', error));
    }

    preloadCriticalResources() {
        // Preload cart and checkout pages
        const link = document.createElement('link');
        link.rel = 'prefetch';
        link.href = '/orders/cart/';
        document.head.appendChild(link);
    }

    updateCartCount(count) {
        const cartBadges = document.querySelectorAll('.cart-badge');
        cartBadges.forEach(badge => {
            badge.textContent = count;
            badge.style.display = count > 0 ? 'inline' : 'none';
        });
    }

    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    }

    showError(message) {
        // Show error toast or notification
        if (window.showToast) {
            window.showToast(message, 'error');
        } else {
            console.error(message);
        }
    }
}

// Design Tool Performance Optimizations
class DesignToolOptimizer {
    constructor() {
        this.canvas = null;
        this.renderQueue = [];
        this.isRendering = false;

        this.init();
    }

    init() {
        this.optimizeCanvas();
        this.setupAutoSave();
        this.optimizeTemplateLoading();
    }

    optimizeCanvas() {
        // Use requestAnimationFrame for smooth rendering
        const canvas = document.querySelector('#design-canvas');
        if (!canvas) return;

        this.canvas = canvas;

        // Optimize canvas context
        const ctx = canvas.getContext('2d');
        if (ctx) {
            ctx.imageSmoothingEnabled = true;
            ctx.imageSmoothingQuality = 'high';
        }

        // Use RAF for canvas updates
        this.bindCanvasEvents();
    }

    bindCanvasEvents() {
        if (!this.canvas) return;

        const throttledRender = throttle(() => {
            this.queueRender();
        }, 16); // 60fps

        this.canvas.addEventListener('mousemove', throttledRender);
        this.canvas.addEventListener('touchmove', throttledRender);
    }

    queueRender() {
        if (!this.isRendering) {
            this.isRendering = true;
            requestAnimationFrame(() => {
                this.render();
                this.isRendering = false;
            });
        }
    }

    render() {
        // Implement efficient canvas rendering
        if (window.fabric && window.fabric.Canvas) {
            const fabricCanvas = window.fabric.Canvas.instances[0];
            if (fabricCanvas) {
                fabricCanvas.renderAll();
            }
        }
    }

    setupAutoSave() {
        let saveTimeout;
        const autoSave = debounce(() => {
            if (window.saveDesign) {
                window.saveDesign(true); // true for auto-save
            }
        }, 5000);

        // Listen for canvas changes
        document.addEventListener('canvasChanged', autoSave);

        // Save before page unload
        window.addEventListener('beforeunload', (e) => {
            if (window.hasUnsavedChanges) {
                e.preventDefault();
                e.returnValue = '';
            }
        });
    }

    optimizeTemplateLoading() {
        // Lazy load templates
        const templateGrid = document.querySelector('.template-grid');
        if (!templateGrid) return;

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    this.loadTemplate(entry.target);
                    observer.unobserve(entry.target);
                }
            });
        });

        const templates = templateGrid.querySelectorAll('.template-item');
        templates.forEach(template => observer.observe(template));
    }

    loadTemplate(templateElement) {
        const templateId = templateElement.dataset.templateId;
        if (!templateId) return;

        fetch(`/design-tool/api/template/${templateId}/`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    templateElement.classList.add('loaded');
                    // Cache template data
                    sessionStorage.setItem(`template_${templateId}`, JSON.stringify(data));
                }
            })
            .catch(error => console.warn('Template preload failed:', error));
    }
}

// Quote System Performance
class QuoteOptimizer {
    constructor() {
        this.init();
    }

    init() {
        this.optimizeQuoteGeneration();
        this.setupProgressiveLoading();
    }

    optimizeQuoteGeneration() {
        const generateBtn = document.querySelector('#generate-quote-btn');
        if (!generateBtn) return;

        generateBtn.addEventListener('click', async (e) => {
            e.preventDefault();

            // Show loading state
            this.showLoadingState(generateBtn);

            try {
                const result = await this.generateQuote();
                if (result.success) {
                    window.location.href = result.quote_url;
                } else {
                    throw new Error(result.error);
                }
            } catch (error) {
                this.showError('Failed to generate quote: ' + error.message);
            } finally {
                this.hideLoadingState(generateBtn);
            }
        });
    }

    async generateQuote() {
        const response = await fetch('/orders/api/quote/generate/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken()
            }
        });

        if (!response.ok) throw new Error('Network error');
        return response.json();
    }

    setupProgressiveLoading() {
        // Load quote items progressively
        const quoteItems = document.querySelectorAll('.quote-item');
        if (quoteItems.length === 0) return;

        quoteItems.forEach((item, index) => {
            setTimeout(() => {
                item.classList.add('animate-in');
            }, index * 100);
        });
    }

    showLoadingState(button) {
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Generating...';
    }

    hideLoadingState(button) {
        button.disabled = false;
        button.innerHTML = '<i class="fas fa-file-invoice mr-2"></i>Generate Quote';
    }

    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    }

    showError(message) {
        if (window.showToast) {
            window.showToast(message, 'error');
        } else {
            alert(message);
        }
    }
}

// Mobile Touch Optimizations
class TouchOptimizer {
    constructor() {
        this.init();
    }

    init() {
        if (!this.isTouchDevice()) return;

        this.optimizeTouchTargets();
        this.setupSwipeGestures();
        this.optimizeScrolling();
    }

    isTouchDevice() {
        return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    }

    optimizeTouchTargets() {
        // Ensure minimum touch target size
        const buttons = document.querySelectorAll('button, .btn, a[role="button"]');
        buttons.forEach(btn => {
            const rect = btn.getBoundingClientRect();
            if (rect.width < 44 || rect.height < 44) {
                btn.style.minWidth = '44px';
                btn.style.minHeight = '44px';
                btn.style.padding = Math.max(parseInt(btn.style.padding) || 8, 12) + 'px';
            }
        });
    }

    setupSwipeGestures() {
        // Add swipe to remove for cart items
        const cartItems = document.querySelectorAll('.cart-item');
        cartItems.forEach(item => {
            this.addSwipeToRemove(item);
        });

        // Add swipe navigation for quote carousel
        const quoteCarousel = document.querySelector('.quote-carousel');
        if (quoteCarousel) {
            this.addSwipeNavigation(quoteCarousel);
        }
    }

    addSwipeToRemove(element) {
        let startX, currentX, isDragging = false;

        element.addEventListener('touchstart', (e) => {
            startX = e.touches[0].clientX;
            isDragging = true;
            element.style.transition = 'none';
        });

        element.addEventListener('touchmove', (e) => {
            if (!isDragging) return;

            currentX = e.touches[0].clientX;
            const diff = currentX - startX;

            if (Math.abs(diff) > 10) {
                element.style.transform = `translateX(${diff}px)`;
                element.style.opacity = Math.max(0.3, 1 - Math.abs(diff) / 200);
            }
        });

        element.addEventListener('touchend', (e) => {
            if (!isDragging) return;
            isDragging = false;

            const diff = currentX - startX;
            element.style.transition = 'transform 0.3s ease, opacity 0.3s ease';

            if (Math.abs(diff) > 100) {
                // Remove item
                element.style.transform = `translateX(${diff > 0 ? '100%' : '-100%'})`;
                element.style.opacity = '0';
                setTimeout(() => {
                    const itemId = element.dataset.itemId;
                    if (itemId && window.removeItem) {
                        window.removeItem(itemId);
                    }
                }, 300);
            } else {
                // Snap back
                element.style.transform = 'translateX(0)';
                element.style.opacity = '1';
            }
        });
    }

    addSwipeNavigation(carousel) {
        let startX, currentX, isDragging = false;

        carousel.addEventListener('touchstart', (e) => {
            startX = e.touches[0].clientX;
            isDragging = true;
        });

        carousel.addEventListener('touchmove', (e) => {
            if (!isDragging) return;
            e.preventDefault();
            currentX = e.touches[0].clientX;
        });

        carousel.addEventListener('touchend', (e) => {
            if (!isDragging) return;
            isDragging = false;

            const diff = startX - currentX;
            const threshold = 50;

            if (Math.abs(diff) > threshold) {
                if (diff > 0 && window.nextQuote) {
                    window.nextQuote();
                } else if (diff < 0 && window.prevQuote) {
                    window.prevQuote();
                }
            }
        });
    }

    optimizeScrolling() {
        // Smooth scrolling for iOS
        document.documentElement.style.webkitOverflowScrolling = 'touch';

        // Prevent zoom on double tap
        let lastTouchEnd = 0;
        document.addEventListener('touchend', (e) => {
            const now = new Date().getTime();
            if (now - lastTouchEnd <= 300) {
                e.preventDefault();
            }
            lastTouchEnd = now;
        }, false);
    }
}

// Initialize Performance Optimizations
document.addEventListener('DOMContentLoaded', () => {
    // Initialize all optimizers
    new LazyLoader();
    new CartOptimizer();
    new DesignToolOptimizer();
    new QuoteOptimizer();
    new TouchOptimizer();

    // Global performance monitoring
    if ('PerformanceObserver' in window) {
        const observer = new PerformanceObserver((list) => {
            const entries = list.getEntries();
            entries.forEach(entry => {
                if (entry.duration > 100) {
                    console.warn(`Slow operation detected: ${entry.name} took ${entry.duration}ms`);
                }
            });
        });

        observer.observe({ entryTypes: ['measure'] });
    }

    // Service Worker registration for caching
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/static/js/sw.js')
            .then(registration => {
                console.log('Service Worker registered:', registration);
            })
            .catch(error => {
                console.log('Service Worker registration failed:', error);
            });
    }
});

// Export for use in other modules
window.PerformanceOptimizer = {
    LazyLoader,
    CartOptimizer,
    DesignToolOptimizer,
    QuoteOptimizer,
    TouchOptimizer,
    debounce,
    throttle
};