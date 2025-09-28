/**
 * Services Dropdown JavaScript Enhancement
 * Provides progressive enhancement for the services navigation dropdown
 */

class ServicesDropdown {
    constructor() {
        this.dropdownContainer = document.getElementById('servicesDropdown');
        this.mobileMenu = document.getElementById('mobileServicesMenu');
        this.servicesLink = document.querySelector('[data-services-trigger]');
        this.mobileCloseBtn = document.querySelector('.mobile-menu-close');
        this.isMobile = window.innerWidth <= 768;
        this.isOpen = false;
        this.hoverTimeout = null;
        
        this.init();
    }
    
    init() {
        if (!this.dropdownContainer) return;
        
        this.setupEventListeners();
        this.setupKeyboardNavigation();
        this.setupMobileHandlers();
        this.setupAccessibility();
        
        // Handle window resize
        window.addEventListener('resize', () => {
            this.isMobile = window.innerWidth <= 768;
            this.closeAllMenus();
        });
    }
    
    setupEventListeners() {
        // Desktop hover handlers
        if (this.servicesLink) {
            this.servicesLink.addEventListener('mouseenter', () => {
                if (!this.isMobile) {
                    this.clearHoverTimeout();
                    this.openDropdown();
                }
            });
            
            this.servicesLink.addEventListener('mouseleave', () => {
                if (!this.isMobile) {
                    this.setHoverTimeout();
                }
            });
            
            // Click handler for mobile
            this.servicesLink.addEventListener('click', (e) => {
                if (this.isMobile) {
                    e.preventDefault();
                    this.toggleMobileMenu();
                }
            });
        }
        
        // Dropdown hover handlers
        if (this.dropdownContainer) {
            this.dropdownContainer.addEventListener('mouseenter', () => {
                if (!this.isMobile) {
                    this.clearHoverTimeout();
                }
            });
            
            this.dropdownContainer.addEventListener('mouseleave', () => {
                if (!this.isMobile) {
                    this.setHoverTimeout();
                }
            });
        }
        
        // Click outside to close
        document.addEventListener('click', (e) => {
            if (!this.dropdownContainer?.contains(e.target) && 
                !this.servicesLink?.contains(e.target)) {
                this.closeDropdown();
            }
            
            if (this.mobileMenu && !this.mobileMenu.contains(e.target) && 
                !this.servicesLink?.contains(e.target)) {
                this.closeMobileMenu();
            }
        });
        
        // Escape key to close
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeAllMenus();
            }
        });
    }
    
    setupKeyboardNavigation() {
        // Tab navigation through menu items
        const menuItems = this.dropdownContainer?.querySelectorAll('[role="menuitem"]');
        
        if (menuItems) {
            menuItems.forEach((item, index) => {
                item.addEventListener('keydown', (e) => {
                    switch (e.key) {
                        case 'ArrowDown':
                            e.preventDefault();
                            this.focusNextItem(menuItems, index);
                            break;
                        case 'ArrowUp':
                            e.preventDefault();
                            this.focusPrevItem(menuItems, index);
                            break;
                        case 'Enter':
                        case ' ':
                            e.preventDefault();
                            item.click();
                            break;
                        case 'Escape':
                            this.closeAllMenus();
                            this.servicesLink?.focus();
                            break;
                    }
                });
            });
        }
    }
    
    setupMobileHandlers() {
        // Mobile menu close button
        if (this.mobileCloseBtn) {
            this.mobileCloseBtn.addEventListener('click', () => {
                this.closeMobileMenu();
            });
        }
        
        // Mobile category toggles
        const categoryToggles = document.querySelectorAll('.mobile-category-toggle');
        categoryToggles.forEach(toggle => {
            toggle.addEventListener('click', (e) => {
                e.preventDefault();
                this.toggleMobileCategory(toggle);
            });
        });
        
        // Touch handlers for mobile
        let touchStartY = 0;
        
        if (this.mobileMenu) {
            this.mobileMenu.addEventListener('touchstart', (e) => {
                touchStartY = e.touches[0].clientY;
            });
            
            this.mobileMenu.addEventListener('touchmove', (e) => {
                const touchY = e.touches[0].clientY;
                const deltaY = touchY - touchStartY;
                
                // Prevent overscroll
                if (this.mobileMenu.scrollTop === 0 && deltaY > 0) {
                    e.preventDefault();
                }
            });
        }
    }
    
    setupAccessibility() {
        // Set ARIA attributes
        if (this.servicesLink) {
            this.servicesLink.setAttribute('aria-haspopup', 'true');
            this.servicesLink.setAttribute('aria-expanded', 'false');
        }
        
        // Add focus management
        const firstMenuItem = this.dropdownContainer?.querySelector('[role="menuitem"]');
        if (firstMenuItem) {
            firstMenuItem.setAttribute('tabindex', '0');
        }
    }
    
    openDropdown() {
        if (this.isMobile) return;
        
        this.dropdownContainer?.classList.add('active');
        this.isOpen = true;
        
        if (this.servicesLink) {
            this.servicesLink.setAttribute('aria-expanded', 'true');
        }
        
        // Focus first menu item for keyboard users
        const firstMenuItem = this.dropdownContainer?.querySelector('[role="menuitem"]');
        if (document.activeElement === this.servicesLink && firstMenuItem) {
            setTimeout(() => firstMenuItem.focus(), 100);
        }
    }
    
    closeDropdown() {
        this.dropdownContainer?.classList.remove('active');
        this.isOpen = false;
        
        if (this.servicesLink) {
            this.servicesLink.setAttribute('aria-expanded', 'false');
        }
    }
    
    toggleMobileMenu() {
        if (this.mobileMenu?.classList.contains('active')) {
            this.closeMobileMenu();
        } else {
            this.openMobileMenu();
        }
    }
    
    openMobileMenu() {
        this.mobileMenu?.classList.add('active');
        document.body.style.overflow = 'hidden'; // Prevent background scroll
        
        // Focus first element for accessibility
        const firstLink = this.mobileMenu?.querySelector('a');
        if (firstLink) {
            setTimeout(() => firstLink.focus(), 100);
        }
    }
    
    closeMobileMenu() {
        this.mobileMenu?.classList.remove('active');
        document.body.style.overflow = ''; // Restore scroll
    }
    
    toggleMobileCategory(toggle) {
        const categoryHeader = toggle.closest('.mobile-category-header');
        const category = categoryHeader?.closest('.mobile-category');
        const products = category?.querySelector('.mobile-products');
        const isExpanded = toggle.getAttribute('aria-expanded') === 'true';
        
        if (products) {
            if (isExpanded) {
                products.classList.remove('active');
                toggle.setAttribute('aria-expanded', 'false');
                toggle.classList.remove('active');
            } else {
                products.classList.add('active');
                toggle.setAttribute('aria-expanded', 'true');
                toggle.classList.add('active');
            }
        }
    }
    
    closeAllMenus() {
        this.closeDropdown();
        this.closeMobileMenu();
    }
    
    setHoverTimeout() {
        this.hoverTimeout = setTimeout(() => {
            this.closeDropdown();
        }, 300); // 300ms delay before closing
    }
    
    clearHoverTimeout() {
        if (this.hoverTimeout) {
            clearTimeout(this.hoverTimeout);
            this.hoverTimeout = null;
        }
    }
    
    focusNextItem(items, currentIndex) {
        const nextIndex = (currentIndex + 1) % items.length;
        items[nextIndex].focus();
    }
    
    focusPrevItem(items, currentIndex) {
        const prevIndex = currentIndex === 0 ? items.length - 1 : currentIndex - 1;
        items[prevIndex].focus();
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ServicesDropdown();
});

// Handle dynamic content loading
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new ServicesDropdown();
    });
} else {
    new ServicesDropdown();
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ServicesDropdown;
}