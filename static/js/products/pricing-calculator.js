// Pricing Calculator for Static Products

class PricingCalculator {
    constructor(productId, options = {}) {
        this.productId = productId;
        this.currentSelections = {
            quantity: 100,
            size: null,
            paper: null,
            finish: null,
            binding: null,
            color: null,
            rushOrder: false,
            designService: false
        };

        this.elements = {
            basePrice: document.getElementById('base-price'),
            quantityDisplay: document.getElementById('quantity-display'),
            subtotalPrice: document.getElementById('subtotal-price'),
            totalPrice: document.getElementById('total-price'),
            pricePerUnit: document.getElementById('price-per-unit'),
            quantityDiscount: document.getElementById('quantity-discount'),
            sizeCost: document.getElementById('size-cost'),
            paperCost: document.getElementById('paper-cost'),
            colorCost: document.getElementById('color-cost'),
            finishCost: document.getElementById('finish-cost'),
            rushOrderCost: document.getElementById('rush-order-cost'),
            designServiceCost: document.getElementById('design-service-cost'),
            loader: document.getElementById('pricing-loader')
        };

        this.init();
    }

    init() {
        this.bindEvents();
        this.updatePrice();
    }

    bindEvents() {
        // Quantity selection events are handled by global functions
        // Size, paper, finish, etc. events are handled by global functions
        // Additional service checkboxes
        const rushOrderCheckbox = document.getElementById('rush-order');
        const designServiceCheckbox = document.getElementById('design-service');

        if (rushOrderCheckbox) {
            rushOrderCheckbox.addEventListener('change', (e) => {
                this.currentSelections.rushOrder = e.target.checked;
                this.updatePrice();
            });
        }

        if (designServiceCheckbox) {
            designServiceCheckbox.addEventListener('change', (e) => {
                this.currentSelections.designService = e.target.checked;
                this.updatePrice();
            });
        }
    }

    showLoader() {
        if (this.elements.loader) {
            this.elements.loader.classList.remove('hidden');
        }
    }

    hideLoader() {
        if (this.elements.loader) {
            this.elements.loader.classList.add('hidden');
        }
    }

    async updatePrice() {
        this.showLoader();

        try {
            const params = new URLSearchParams({
                quantity: this.currentSelections.quantity,
                ...(this.currentSelections.size && { size: this.currentSelections.size }),
                ...(this.currentSelections.paper && { paper: this.currentSelections.paper }),
                ...(this.currentSelections.finish && { finish: this.currentSelections.finish }),
                ...(this.currentSelections.binding && { binding: this.currentSelections.binding }),
                ...(this.currentSelections.color && { color: this.currentSelections.color }),
                rush_order: this.currentSelections.rushOrder,
                design_service: this.currentSelections.designService
            });

            const response = await fetch(`/services/api/pricing/${this.productId}/?${params}`);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            if (data.success) {
                this.updatePriceDisplay(data.pricing, data.breakdown);
            } else {
                console.error('Pricing calculation failed:', data.error);
                this.showError('Failed to calculate price. Please try again.');
            }
        } catch (error) {
            console.error('Error calculating price:', error);
            this.showError('Failed to calculate price. Please check your connection.');
        } finally {
            this.hideLoader();
        }
    }

    updatePriceDisplay(pricing, breakdown) {
        // Update quantity display
        if (this.elements.quantityDisplay) {
            this.elements.quantityDisplay.textContent = `${pricing.quantity} pieces`;
        }

        // Update price breakdown
        if (this.elements.subtotalPrice) {
            this.elements.subtotalPrice.textContent = `¹${Math.round(pricing.subtotal_after_discount)}`;
        }

        if (this.elements.totalPrice) {
            this.elements.totalPrice.textContent = `¹${Math.round(pricing.total_price)}`;
        }

        if (this.elements.pricePerUnit) {
            this.elements.pricePerUnit.textContent = `¹${Math.round(pricing.price_per_unit)}`;
        }

        // Show/hide and update modifiers
        this.updateModifierRow('size-cost-row', this.elements.sizeCost, breakdown.size_modifier);
        this.updateModifierRow('paper-cost-row', this.elements.paperCost, breakdown.paper_modifier);
        this.updateModifierRow('finish-cost-row', this.elements.finishCost, breakdown.finish_modifier);

        // Quantity discount
        if (pricing.discount_amount > 0) {
            this.showRow('quantity-discount-row');
            if (this.elements.quantityDiscount) {
                this.elements.quantityDiscount.textContent = `-¹${Math.round(pricing.discount_amount)}`;
            }
        } else {
            this.hideRow('quantity-discount-row');
        }

        // Rush order
        if (pricing.rush_amount > 0) {
            this.showRow('rush-order-row');
            if (this.elements.rushOrderCost) {
                this.elements.rushOrderCost.textContent = `+¹${Math.round(pricing.rush_amount)}`;
            }
        } else {
            this.hideRow('rush-order-row');
        }

        // Design service
        if (pricing.design_amount > 0) {
            this.showRow('design-service-row');
            if (this.elements.designServiceCost) {
                this.elements.designServiceCost.textContent = `+¹${Math.round(pricing.design_amount)}`;
            }
        } else {
            this.hideRow('design-service-row');
        }
    }

    updateModifierRow(rowId, element, modifier) {
        if (modifier && modifier !== 0) {
            this.showRow(rowId);
            if (element) {
                const sign = modifier > 0 ? '+' : '';
                element.textContent = `${sign}¹${Math.round(modifier)}`;
            }
        } else {
            this.hideRow(rowId);
        }
    }

    showRow(rowId) {
        const row = document.getElementById(rowId);
        if (row) {
            row.classList.remove('hidden');
        }
    }

    hideRow(rowId) {
        const row = document.getElementById(rowId);
        if (row) {
            row.classList.add('hidden');
        }
    }

    showError(message) {
        // Create or update error message
        let errorElement = document.getElementById('pricing-error');
        if (!errorElement) {
            errorElement = document.createElement('div');
            errorElement.id = 'pricing-error';
            errorElement.className = 'bg-red-100 text-red-700 px-4 py-2 rounded-lg text-sm mt-4';

            const calculator = document.querySelector('.pricing-calculator');
            if (calculator) {
                calculator.appendChild(errorElement);
            }
        }

        errorElement.textContent = message;
        errorElement.classList.remove('hidden');

        // Hide error after 5 seconds
        setTimeout(() => {
            errorElement.classList.add('hidden');
        }, 5000);
    }

    // Public methods for option selection
    selectQuantity(quantity, discountPercent = 0) {
        this.currentSelections.quantity = quantity;

        // Update active state for quantity buttons
        document.querySelectorAll('.quantity-option').forEach(btn => {
            btn.classList.remove('active');
        });

        const selectedBtn = document.querySelector(`[data-quantity="${quantity}"]`);
        if (selectedBtn) {
            selectedBtn.classList.add('active');
        }

        this.updatePrice();
    }

    selectSize(size, modifier) {
        this.currentSelections.size = size;

        // Update active state for size buttons
        document.querySelectorAll('.size-option').forEach(btn => {
            btn.classList.remove('active');
        });

        const selectedBtn = document.querySelector(`[data-size="${size}"]`);
        if (selectedBtn) {
            selectedBtn.classList.add('active');
        }

        this.updatePrice();
    }

    selectPaper(paper) {
        this.currentSelections.paper = paper;
        this.updatePrice();
    }

    selectFinish(finish, modifier) {
        this.currentSelections.finish = finish;

        // Update active state for finish buttons
        document.querySelectorAll('.finish-option').forEach(btn => {
            btn.classList.remove('active');
        });

        const selectedBtn = document.querySelector(`[data-finish="${finish}"]`);
        if (selectedBtn) {
            selectedBtn.classList.add('active');
        }

        this.updatePrice();
    }

    selectColor(color, modifier) {
        this.currentSelections.color = color;
        this.updatePrice();
    }

    selectCustomQuantity(quantity) {
        const qty = parseInt(quantity);
        if (qty > 0) {
            this.selectQuantity(qty);
        }
    }
}

// Global functions for event handlers
let pricingCalculator;

function selectQuantity(quantity, discountPercent = 0) {
    if (pricingCalculator) {
        pricingCalculator.selectQuantity(quantity, discountPercent);
    }
}

function selectSize(size, modifier) {
    if (pricingCalculator) {
        pricingCalculator.selectSize(size, modifier);
    }
}

function selectPaper(paper, modifier = 0) {
    if (pricingCalculator) {
        pricingCalculator.selectPaper(paper);
    }
}

function selectFinish(finish, modifier) {
    if (pricingCalculator) {
        pricingCalculator.selectFinish(finish, modifier);
    }
}

function selectColor(color, modifier) {
    if (pricingCalculator) {
        pricingCalculator.selectColor(color, modifier);
    }
}

function selectCustomQuantity(quantity) {
    if (pricingCalculator) {
        pricingCalculator.selectCustomQuantity(quantity);
    }
}

function toggleRushOrder(checked) {
    if (pricingCalculator) {
        pricingCalculator.currentSelections.rushOrder = checked;
        pricingCalculator.updatePrice();
    }
}

function toggleDesignService(checked) {
    if (pricingCalculator) {
        pricingCalculator.currentSelections.designService = checked;
        pricingCalculator.updatePrice();
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    if (window.productData && window.productData.id) {
        pricingCalculator = new PricingCalculator(window.productData.id);
    }
});

// Cart and quote functions
function addToCart() {
    if (!pricingCalculator) return;

    // Implement cart functionality
    alert('Add to cart functionality will be implemented in Phase 4');
}

function getQuote() {
    if (!pricingCalculator) return;

    // Implement quote functionality
    alert('Get quote functionality will be implemented in Phase 4');
}

function contactSupport() {
    // Implement support contact
    alert('Contact support functionality to be implemented');
}