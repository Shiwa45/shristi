// Category-Specific Pricing Calculator
class CategoryPricingCalculator {
    constructor(categoryConfig) {
        this.category = categoryConfig.category;
        this.minQuantity = categoryConfig.minQuantity || 25;
        this.gstPercentage = categoryConfig.gstPercentage || 18;
        this.basePrice = 100; // Default base price
        this.pricingReady = false;
        this.formData = {};
        this.pricing = {
            basePrice: 0,
            optionModifiers: {},
            subtotal: 0,
            discount: 0,
            gst: 0,
            total: 0
        };
        
        this.init();
    }
    
    init() {
        console.log('💰 Category Pricing Calculator Initialized for:', this.category);
        
        // Set initial quantity
        this.updateQuantityDisplay();
        
        // Initialize pricing display
        if (this.category === 'book-printing') {
            this.resetPricingDisplay();
        } else {
            this.updatePricingDisplay();
        }
        
        console.log('✅ Pricing calculator ready');
    }
    
    updatePricing(formData) {
        this.formData = { ...formData };
        const quantity = this.getValidQuantity();

        // For book printing we do not want to show any numbers until quantity is entered
        if (this.category === 'book-printing' && quantity === null) {
            this.pricingReady = false;
            this.resetPricingDisplay();
            return;
        }
        
        console.log('🧮 Calculating pricing for:', formData);
        
        // Calculate based on category
        if (this.category === 'book-printing') {
            this.calculateBookPricing(quantity);
        } else {
            this.calculateGenericPricing();
        }

        this.pricingReady = true;
        
        // Update display
        this.updatePricingDisplay();
    }
    
    calculateBookPricing(quantity) {
        let basePrice = 5.0; // Base price per page
        let totalPages = 0;
        let optionModifiers = {};
        const qty = quantity || this.minQuantity;
        
        // Calculate total pages
        if (this.formData.interior_color === 'combine_color') {
            const bwPages = parseInt(this.formData.bw_page_count) || 0;
            const colorPages = parseInt(this.formData.color_page_count) || 0;
            totalPages = bwPages + colorPages;
            
            // Different rates for B&W and color pages
            basePrice = (bwPages * 2.5) + (colorPages * 8.0);
        } else {
            totalPages = parseInt(this.formData.page_count) || 0;
            
            // Apply interior color pricing
            if (this.formData.interior_color === 'color_premium') {
                basePrice = totalPages * 8.0;
            } else if (this.formData.interior_color === 'color_standard') {
                basePrice = totalPages * 6.0;
            } else if (this.formData.interior_color === 'bw_premium') {
                basePrice = totalPages * 3.0;
            } else if (this.formData.interior_color === 'bw_standard') {
                basePrice = totalPages * 2.5;
            }
        }
        
        // Apply book size modifier
        if (this.formData.book_size) {
            const sizeModifiers = {
                'a4': 0,
                'letter': 25,
                'executive': 50,
                'a5': -25
            };
            optionModifiers['Book Size'] = sizeModifiers[this.formData.book_size] || 0;
        }
        
        // Apply paper type modifier
        if (this.formData.paper_type) {
            const paperModifiers = {
                '75gsm': 0,
                '100gsm': 50,
                '100gsm_art': 100,
                '130gsm_art': 150
            };
            optionModifiers['Paper Type'] = paperModifiers[this.formData.paper_type] || 0;
        }
        
        // Apply binding type modifier
        if (this.formData.binding_type) {
            const bindingModifiers = {
                'saddle_stitch': 0,
                'spiral_binding': 100,
                'paperback_perfect': 200,
                'hardcover': 500
            };
            optionModifiers['Binding Type'] = bindingModifiers[this.formData.binding_type] || 0;
        }
        
        // Apply cover finish modifier
        if (this.formData.cover_finish) {
            const finishModifiers = {
                'matte': 0,
                'glossy': 50
            };
            optionModifiers['Cover Finish'] = finishModifiers[this.formData.cover_finish] || 0;
        }
        
        // Apply design service
        if (this.formData.design_service === 'yes_design') {
            optionModifiers['Design Service'] = 1500 + (totalPages * 50);
        }
        
        // Apply ISBN allocation
        if (this.formData.isbn_allocation === 'assign_isbn') {
            optionModifiers['ISBN Allocation'] = 2000;
        }
        
        // Calculate totals
        let unitPrice = basePrice;
        
        // Add option modifiers
        Object.values(optionModifiers).forEach(modifier => {
            unitPrice += modifier;
        });
        
        const subtotal = unitPrice * qty;
        
        // Apply volume discount (example: 10% for orders over 100)
        let discount = 0;
        if (qty >= 100) {
            discount = subtotal * 0.1;
        }
        
        const afterDiscount = subtotal - discount;
        const gst = afterDiscount * (this.gstPercentage / 100);
        const total = afterDiscount + gst;
        
        // Update pricing object
        this.pricing = {
            basePrice: basePrice,
            optionModifiers: optionModifiers,
            unitPrice: unitPrice,
            quantity: qty,
            subtotal: subtotal,
            discount: discount,
            gst: gst,
            total: total
        };
    }    
    c
alculateGenericPricing() {
        // Generic pricing calculation for other categories
        let basePrice = 100;
        let optionModifiers = {};
        
        // Apply basic modifiers based on form data
        Object.entries(this.formData).forEach(([key, value]) => {
            // Extract price modifiers from form elements
            const element = document.querySelector(`[name="${key}"][value="${value}"]`);
            if (element) {
                const modifier = parseFloat(element.dataset.priceModifier) || 0;
                if (modifier !== 0) {
                    optionModifiers[key] = modifier;
                }
            }
        });
        
        const quantity = this.minQuantity;
        let unitPrice = basePrice;
        
        // Add option modifiers
        Object.values(optionModifiers).forEach(modifier => {
            unitPrice += modifier;
        });
        
        const subtotal = unitPrice * quantity;
        const gst = subtotal * (this.gstPercentage / 100);
        const total = subtotal + gst;
        
        this.pricing = {
            basePrice: basePrice,
            optionModifiers: optionModifiers,
            unitPrice: unitPrice,
            quantity: quantity,
            subtotal: subtotal,
            discount: 0,
            gst: gst,
            total: total
        };
    }
    
    updatePricingDisplay() {
        if (this.category === 'book-printing' && !this.pricingReady) {
            this.resetPricingDisplay();
            return;
        }

        // Update cost per unit
        const costPerUnit = document.getElementById('cost-per-unit');
        if (costPerUnit) {
            costPerUnit.textContent = `₹${this.formatPrice(this.pricing.unitPrice || 0)}`;
        }
        
        // Update quantity display
        this.updateQuantityDisplay();
        
        // Update subtotal
        const subtotal = document.getElementById('subtotal');
        if (subtotal) {
            subtotal.textContent = `₹${this.formatPrice(this.pricing.subtotal || 0)}`;
        }
        
        // Update discount
        const discountRow = document.getElementById('discount-row');
        const discountAmount = document.getElementById('discount-amount');
        if (this.pricing.discount > 0) {
            if (discountRow) discountRow.style.display = 'flex';
            if (discountAmount) discountAmount.textContent = `- ₹${this.formatPrice(this.pricing.discount)}`;
        } else {
            if (discountRow) discountRow.style.display = 'none';
        }
        
        // Update GST
        const gstAmount = document.getElementById('gst-amount');
        if (gstAmount) {
            gstAmount.textContent = `₹${this.formatPrice(this.pricing.gst || 0)}`;
        }
        
        // Update total
        const totalPrice = document.getElementById('total-price');
        if (totalPrice) {
            totalPrice.textContent = `₹${this.formatPrice(this.pricing.total || 0)}`;
            
            // Add animation
            totalPrice.classList.add('price-update');
            setTimeout(() => totalPrice.classList.remove('price-update'), 600);
        }
    }
    
    updateQuantityDisplay() {
        const quantityDisplay = document.getElementById('quantity-display');
        if (quantityDisplay) {
            const qty = this.pricing.quantity || (this.pricingReady ? this.minQuantity : null);
            quantityDisplay.textContent = qty ? `${qty} pieces` : 'Enter quantity';
        }
    }
    
    resetPricingDisplay() {
        this.pricingReady = false;

        const setText = (id, value) => {
            const el = document.getElementById(id);
            if (el) el.textContent = value;
        };

        setText('cost-per-unit', '₹ N/A');
        setText('subtotal', 'Enter quantity');
        setText('discount-amount', '- ₹ 0');
        setText('gst-amount', 'Enter quantity');
        setText('total-price', 'Enter quantity');

        const discountRow = document.getElementById('discount-row');
        if (discountRow) discountRow.style.display = 'none';

        this.pricing = {
            basePrice: 0,
            optionModifiers: {},
            unitPrice: 0,
            quantity: null,
            subtotal: 0,
            discount: 0,
            gst: 0,
            total: 0
        };
    }

    getValidQuantity() {
        const quantity = parseInt(this.formData.quantity);
        if (isNaN(quantity)) return null;
        return Math.max(quantity, this.minQuantity);
    }
    
    formatPrice(price) {
        return parseFloat(price).toLocaleString('en-IN', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    }
    
    getPricingBreakdown() {
        return { ...this.pricing };
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    if (window.categoryConfig) {
        console.log('🚀 Starting Category Pricing Calculator...');
        window.categoryPricingCalculator = new CategoryPricingCalculator(window.categoryConfig);
    } else {
        console.warn('⚠️ Category config not found for pricing calculator');
    }
});

// Add CSS animation for price updates
const style = document.createElement('style');
style.textContent = `
    .price-update {
        animation: priceChange 0.6s ease-in-out;
    }
    
    @keyframes priceChange {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.05); color: #10b981; }
    }
`;
document.head.appendChild(style);
