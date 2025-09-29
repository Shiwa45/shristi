// Create: static/js/products/dynamic-pricing-calculator.js

class DynamicPricingCalculator {
    constructor() {
        this.basePrice = parseFloat(document.getElementById('base-price')?.textContent?.replace('₹', '').replace(',', '')) || 100;
        this.quantity = 25;
        this.modifiers = {};
        this.init();
    }

    init() {
        console.log('🔢 Pricing Calculator Initialized');
        
        // Listen to all form field changes
        this.attachFieldListeners();
        
        // Initial calculation
        this.calculatePrice();
    }

    attachFieldListeners() {
        // Listen to radio buttons
        document.querySelectorAll('input[type="radio"]').forEach(radio => {
            radio.addEventListener('change', (e) => this.handleFieldChange(e));
        });

        // Listen to select dropdowns
        document.querySelectorAll('select').forEach(select => {
            select.addEventListener('change', (e) => this.handleFieldChange(e));
        });

        // Listen to number inputs
        document.querySelectorAll('input[type="number"]').forEach(input => {
            input.addEventListener('input', (e) => this.handleFieldChange(e));
        });

        console.log('✅ Field listeners attached');
    }

    handleFieldChange(event) {
        const field = event.target;
        const fieldName = field.name;
        const fieldValue = field.value;

        console.log(`📝 Field changed: ${fieldName} = ${fieldValue}`);

        // Handle quantity field
        if (fieldName === 'copies' || fieldName === 'quantity') {
            this.quantity = parseInt(fieldValue) || 25;
            this.updateQuantityDisplay();
        }

        // Get price modifier from the field
        let priceModifier = 0;
        
        if (field.type === 'radio' || field.tagName === 'SELECT') {
            // For radio and select, get price_modifier from data attribute or option
            if (field.type === 'radio') {
                priceModifier = parseFloat(field.dataset.priceModifier) || 0;
            } else {
                const selectedOption = field.options[field.selectedIndex];
                priceModifier = parseFloat(selectedOption.dataset.priceModifier) || 0;
            }
        }

        // Store the modifier for this field
        if (priceModifier !== 0 || fieldName in this.modifiers) {
            this.modifiers[fieldName] = priceModifier;
        }

        console.log('💰 Current modifiers:', this.modifiers);

        // Recalculate price
        this.calculatePrice();

        // Handle conditional fields
        this.handleConditionalFields(fieldName, fieldValue);
    }

    calculatePrice() {
        // Start with base price
        let unitPrice = this.basePrice;

        // Add all modifiers
        let totalModifiers = 0;
        Object.values(this.modifiers).forEach(modifier => {
            totalModifiers += modifier;
            unitPrice += modifier;
        });

        // Calculate total
        const totalPrice = unitPrice * this.quantity;

        console.log(`🧮 Calculation: (${this.basePrice} + ${totalModifiers}) × ${this.quantity} = ${totalPrice}`);

        // Update display
        this.updateDisplay(unitPrice, totalPrice, totalModifiers);
    }

    updateDisplay(unitPrice, totalPrice, totalModifiers) {
        // Update total price
        const totalPriceEl = document.getElementById('total-price');
        if (totalPriceEl) {
            totalPriceEl.textContent = `₹${this.formatPrice(totalPrice)}`;
            // Add animation
            totalPriceEl.classList.add('price-update');
            setTimeout(() => totalPriceEl.classList.remove('price-update'), 600);
        }

        // Update price per unit
        const pricePerUnitEl = document.getElementById('price-per-unit');
        if (pricePerUnitEl) {
            pricePerUnitEl.textContent = `₹${this.formatPrice(unitPrice)} per piece`;
        }

        // Update base price display
        const basePriceEl = document.getElementById('base-price');
        if (basePriceEl) {
            basePriceEl.textContent = `₹${this.formatPrice(this.basePrice)}`;
        }

        // Update cost breakdown rows
        this.updateCostBreakdown();
    }

    updateCostBreakdown() {
        // Show/hide modifier rows
        Object.entries(this.modifiers).forEach(([fieldName, modifier]) => {
            const rowId = `${fieldName}-cost-row`;
            const costId = `${fieldName}-cost`;
            
            const row = document.getElementById(rowId);
            const cost = document.getElementById(costId);

            if (modifier !== 0) {
                if (row) row.classList.remove('hidden');
                if (cost) {
                    const totalCost = modifier * this.quantity;
                    cost.textContent = (totalCost >= 0 ? '+' : '') + `₹${this.formatPrice(Math.abs(totalCost))}`;
                    cost.className = totalCost >= 0 ? 'font-medium text-orange-600' : 'font-medium text-green-600';
                }
            } else {
                if (row) row.classList.add('hidden');
            }
        });
    }

    updateQuantityDisplay() {
        const quantityDisplayEl = document.getElementById('quantity-display');
        if (quantityDisplayEl) {
            quantityDisplayEl.textContent = `${this.quantity} pieces`;
        }
    }

    handleConditionalFields(triggerField, value) {
        // Find all fields with show conditions
        document.querySelectorAll('[data-show-condition]').forEach(wrapper => {
            try {
                const condition = JSON.parse(wrapper.dataset.showCondition || '{}');
                
                if (condition.field === triggerField) {
                    const shouldShow = this.checkCondition(condition, value);
                    
                    if (shouldShow) {
                        wrapper.classList.remove('hidden');
                        wrapper.style.display = '';
                    } else {
                        wrapper.classList.add('hidden');
                        wrapper.style.display = 'none';
                    }

                    console.log(`👁️ Conditional field ${wrapper.dataset.field}: ${shouldShow ? 'SHOW' : 'HIDE'}`);
                }
            } catch (e) {
                console.error('Error handling conditional field:', e);
            }
        });
    }

    checkCondition(condition, value) {
        const operator = condition.operator || 'equals';
        const targetValue = condition.value;

        switch (operator) {
            case 'equals':
                return value === targetValue;
            case 'not_equals':
                return value !== targetValue;
            case 'contains':
                return value.includes(targetValue);
            case 'greater_than':
                return parseFloat(value) > parseFloat(targetValue);
            case 'less_than':
                return parseFloat(value) < parseFloat(targetValue);
            default:
                return true;
        }
    }

    formatPrice(price) {
        return price.toLocaleString('en-IN', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Starting Pricing Calculator...');
    window.pricingCalculator = new DynamicPricingCalculator();
});

// Add CSS animation
const style = document.createElement('style');
style.textContent = `
    .price-update {
        animation: priceChange 0.6s ease-in-out;
    }
    
    @keyframes priceChange {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.1); color: #10b981; }
    }
`;
document.head.appendChild(style);