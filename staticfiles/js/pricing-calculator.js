// static/js/pricing-calculator.js
// Advanced pricing calculator for personalized quotes

class PricingCalculator {
    constructor(productId, formSelector = '#pricing-form') {
        this.productId = productId;
        this.form = document.querySelector(formSelector);
        this.isLoading = false;
        this.cache = new Map();
        
        // DOM elements
        this.unitPriceDisplay = document.getElementById('unit-price');
        this.totalPriceDisplay = document.getElementById('total-price');
        this.savingsDisplay = document.getElementById('savings-display');
        this.savingsAmount = document.getElementById('savings-amount');
        this.loadingIndicator = document.getElementById('pricing-loading');
        
        // Initialize
        this.init();
    }
    
    init() {
        if (!this.form) {
            console.error('Pricing form not found');
            return;
        }
        
        // Bind events
        this.bindEvents();
        
        // Load initial options
        this.loadProductOptions();
        
        // Initial price calculation
        this.calculatePrice();
    }
    
    bindEvents() {
        // Form change events
        this.form.addEventListener('change', (e) => {
            this.handleFormChange(e);
        });
        
        this.form.addEventListener('input', (e) => {
            if (e.target.type === 'number') {
                this.debounce(this.calculatePrice.bind(this), 500)();
            }
        });
        
        // Quantity slider (if exists)
        const quantitySlider = this.form.querySelector('[name="quantity"][type="range"]');
        if (quantitySlider) {
            quantitySlider.addEventListener('input', (e) => {
                const quantityInput = this.form.querySelector('[name="quantity"][type="number"]');
                if (quantityInput) {
                    quantityInput.value = e.target.value;
                }
                this.calculatePrice();
            });
        }
        
        // Paper type info buttons
        this.form.querySelectorAll('.paper-info-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.showPaperInfo(e.target.dataset.paperType);
            });
        });
    }
    
    async loadProductOptions() {
        try {
            const response = await fetch(`/services/api/options/${this.productId}/`);
            const data = await response.json();
            
            if (data.success) {
                this.populateOptions(data.options);
            }
        } catch (error) {
            console.error('Failed to load product options:', error);
        }
    }
    
    populateOptions(options) {
        // Populate size options
        this.populateSelect('size', options.sizes);
        
        // Populate paper type options
        this.populateSelect('paper_type', options.paper_types);
        
        // Populate finish options
        this.populateSelect('finish', options.finishes);
        
        // Update quantity suggestions based on tiers
        if (options.quantity_tiers && options.quantity_tiers.length > 0) {
            this.updateQuantitySuggestions(options.quantity_tiers);
        }
    }
    
    populateSelect(name, options) {
        const select = this.form.querySelector(`[name="${name}"]`);
        if (!select || !options || options.length === 0) return;
        
        // Keep the first option (usually "Select...")
        const firstOption = select.querySelector('option');
        select.innerHTML = '';
        if (firstOption) {
            select.appendChild(firstOption);
        }
        
        // Add new options
        options.forEach(option => {
            if (option) { // Skip empty values
                const optionElement = document.createElement('option');
                optionElement.value = option;
                optionElement.textContent = option;
                select.appendChild(optionElement);
            }
        });
    }
    
    updateQuantitySuggestions(tiers) {
        const quantityInput = this.form.querySelector('[name="quantity"]');
        if (!quantityInput) return;
        
        // Create quantity suggestion buttons
        const suggestionsContainer = document.createElement('div');
        suggestionsContainer.className = 'quantity-suggestions mt-2';
        suggestionsContainer.innerHTML = '<span class="text-sm text-gray-600">Popular quantities:</span>';
        
        tiers.slice(0, 5).forEach(tier => {
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'ml-2 px-3 py-1 text-xs bg-gray-200 text-gray-700 rounded hover:bg-gray-300 transition';
            btn.textContent = tier.toLocaleString();
            btn.addEventListener('click', () => {
                quantityInput.value = tier;
                this.calculatePrice();
            });
            suggestionsContainer.appendChild(btn);
        });
        
        // Insert after quantity input
        quantityInput.parentNode.insertBefore(suggestionsContainer, quantityInput.nextSibling);
    }
    
    handleFormChange(e) {
        const { name, value } = e.target;
        
        // Handle dependent options
        if (name === 'size' || name === 'paper_type') {
            this.updateDependentOptions();
        }
        
        // Calculate price
        this.calculatePrice();
    }
    
    async updateDependentOptions() {
        // This could be enhanced to load dependent options
        // For example, if certain finishes are only available for certain paper types
    }
    
    async calculatePrice() {
        if (this.isLoading) return;
        
        const formData = this.getFormData();
        
        // Validate required fields
        if (!this.validateFormData(formData)) {
            this.clearPricing();
            return;
        }
        
        // Check cache first
        const cacheKey = this.getCacheKey(formData);
        if (this.cache.has(cacheKey)) {
            this.displayPricing(this.cache.get(cacheKey));
            return;
        }
        
        this.setLoading(true);
        
        try {
            const params = new URLSearchParams(formData);
            const response = await fetch(`/services/api/pricing/${this.productId}/?${params}`);
            const data = await response.json();
            
            if (data.success) {
                // Cache the result
                this.cache.set(cacheKey, data);
                this.displayPricing(data);
            } else {
                this.displayError(data.error || 'Pricing not available');
                
                // If requires quote, show quote button
                if (data.requires_quote) {
                    this.showQuoteRequired();
                }
            }
        } catch (error) {
            console.error('Pricing calculation error:', error);
            this.displayError('Failed to calculate pricing');
        } finally {
            this.setLoading(false);
        }
    }
    
    getFormData() {
        const formData = new FormData(this.form);
        return Object.fromEntries(formData);
    }
    
    validateFormData(data) {
        const required = ['size', 'paper_type', 'finish', 'quantity'];
        return required.every(field => data[field] && data[field].trim() !== '');
    }
    
    getCacheKey(data) {
        return `${data.size}_${data.paper_type}_${data.finish}_${data.colors}_${data.quantity}`;
    }
    
    displayPricing(data) {
        if (this.unitPriceDisplay) {
            this.unitPriceDisplay.textContent = `₹${data.unit_price.toFixed(2)}`;
        }
        
        if (this.totalPriceDisplay) {
            this.totalPriceDisplay.textContent = `₹${data.price.toLocaleString('en-IN', {minimumFractionDigits: 2})}`;
        }
        
        if (this.savingsDisplay && this.savingsAmount) {
            if (data.savings > 0) {
                this.savingsAmount.textContent = data.savings.toLocaleString('en-IN', {minimumFractionDigits: 2});
                this.savingsDisplay.style.display = 'block';
            } else {
                this.savingsDisplay.style.display = 'none';
            }
        }
        
        // Add volume discount info
        this.showVolumeDiscountInfo(data);
        
        // Update add to cart button
        this.updateAddToCartButton(true);
    }
    
    showVolumeDiscountInfo(data) {
        const existingInfo = document.getElementById('volume-discount-info');
        if (existingInfo) {
            existingInfo.remove();
        }
        
        if (data.volume_discount > 0) {
            const infoDiv = document.createElement('div');
            infoDiv.id = 'volume-discount-info';
            infoDiv.className = 'mt-2 p-2 bg-green-100 text-green-800 rounded text-sm';
            infoDiv.innerHTML = `🎉 Volume discount applied: ${data.volume_discount}% off!`;
            
            this.totalPriceDisplay.parentNode.appendChild(infoDiv);
        }
    }
    
    displayError(message) {
        if (this.unitPriceDisplay) {
            this.unitPriceDisplay.textContent = 'Quote';
        }
        
        if (this.totalPriceDisplay) {
            this.totalPriceDisplay.textContent = 'Required';
        }
        
        if (this.savingsDisplay) {
            this.savingsDisplay.style.display = 'none';
        }
        
        this.updateAddToCartButton(false);
        
        // Show error message
        this.showErrorMessage(message);
    }
    
    showErrorMessage(message) {
        const existingError = document.getElementById('pricing-error');
        if (existingError) {
            existingError.remove();
        }
        
        const errorDiv = document.createElement('div');
        errorDiv.id = 'pricing-error';
        errorDiv.className = 'mt-2 p-2 bg-red-100 text-red-800 rounded text-sm';
        errorDiv.textContent = message;
        
        this.form.appendChild(errorDiv);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.remove();
            }
        }, 5000);
    }
    
    showQuoteRequired() {
        const quoteBtn = document.getElementById('request-quote-btn');
        if (quoteBtn) {
            quoteBtn.classList.add('animate-pulse');
            quoteBtn.textContent = '📞 Get Custom Quote';
        }
    }
    
    clearPricing() {
        if (this.unitPriceDisplay) {
            this.unitPriceDisplay.textContent = '₹--';
        }
        
        if (this.totalPriceDisplay) {
            this.totalPriceDisplay.textContent = '₹--';
        }
        
        if (this.savingsDisplay) {
            this.savingsDisplay.style.display = 'none';
        }
        
        this.updateAddToCartButton(false);
    }
    
    setLoading(loading) {
        this.isLoading = loading;
        
        if (this.loadingIndicator) {
            this.loadingIndicator.style.display = loading ? 'block' : 'none';
        }
        
        // Disable form during loading
        const inputs = this.form.querySelectorAll('input, select, button');
        inputs.forEach(input => {
            input.disabled = loading;
        });
        
        if (loading) {
            if (this.unitPriceDisplay) this.unitPriceDisplay.textContent = '...';
            if (this.totalPriceDisplay) this.totalPriceDisplay.textContent = '...';
        }
    }
    
    updateAddToCartButton(enabled) {
        const addToCartBtn = document.getElementById('add-to-cart-btn');
        if (addToCartBtn) {
            addToCartBtn.disabled = !enabled;
            addToCartBtn.classList.toggle('opacity-50', !enabled);
            addToCartBtn.classList.toggle('cursor-not-allowed', !enabled);
        }
    }
    
    showPaperInfo(paperType) {
        // This could show a modal or tooltip with paper information
        console.log(`Show info for ${paperType}`);
    }
    
    // Utility function for debouncing
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
}

// Bulk pricing table functionality
class BulkPricingTable {
    constructor(productId, containerId = 'bulk-pricing-table') {
        this.productId = productId;
        this.container = document.getElementById(containerId);
        this.currentSpecs = {};
    }
    
    async loadBulkPricing(specifications) {
        if (!this.container) return;
        
        this.currentSpecs = specifications;
        
        try {
            const params = new URLSearchParams(specifications);
            const response = await fetch(`/services/api/bulk-pricing/${this.productId}/?${params}`);
            const data = await response.json();
            
            if (data.success) {
                this.renderTable(data.tiers);
            } else {
                this.showError(data.error);
            }
        } catch (error) {
            console.error('Failed to load bulk pricing:', error);
            this.showError('Failed to load pricing table');
        }
    }
    
    renderTable(tiers) {
        if (!tiers || tiers.length === 0) {
            this.container.innerHTML = '<p class="text-gray-500">No bulk pricing available for selected specifications.</p>';
            return;
        }
        
        let html = '<div class="overflow-x-auto">';
        html += '<table class="w-full border-collapse border border-gray-300">';
        html += '<thead><tr class="bg-gray-100">';
        html += '<th class="border border-gray-300 px-4 py-2">Quantity</th>';
        html += '<th class="border border-gray-300 px-4 py-2">Unit Price</th>';
        html += '<th class="border border-gray-300 px-4 py-2">Total Price</th>';
        html += '<th class="border border-gray-300 px-4 py-2">Savings</th>';
        html += '<th class="border border-gray-300 px-4 py-2">Turnaround</th>';
        html += '</tr></thead>';
        
        html += '<tbody>';
        tiers.forEach(tier => {
            tier.quantities.forEach((qty, index) => {
                const rowClass = index % 2 === 0 ? 'bg-white' : 'bg-gray-50';
                html += `<tr class="${rowClass}">`;
                html += `<td class="border border-gray-300 px-4 py-2 text-center font-medium">${qty.quantity.toLocaleString()}</td>`;
                html += `<td class="border border-gray-300 px-4 py-2 text-right">₹${qty.unit_price.toFixed(2)}</td>`;
                html += `<td class="border border-gray-300 px-4 py-2 text-right font-medium">₹${qty.total_price.toLocaleString('en-IN')}</td>`;
                
                if (qty.savings > 0) {
                    html += `<td class="border border-gray-300 px-4 py-2 text-right text-green-600">₹${qty.savings.toLocaleString('en-IN')}</td>`;
                } else {
                    html += `<td class="border border-gray-300 px-4 py-2 text-right text-gray-400">--</td>`;
                }
                
                html += `<td class="border border-gray-300 px-4 py-2 text-center">${tier.turnaround_days} days</td>`;
                html += '</tr>';
            });
        });
        
        html += '</tbody></table></div>';
        
        // Add specifications info
        html += '<div class="mt-4 text-sm text-gray-600">';
        html += `<p>• ${tiers[0].specifications.paper_type} with ${tiers[0].specifications.finish}</p>`;
        html += `<p>• ${tiers[0].specifications.colors} color printing</p>`;
        html += '<p>• All prices include setup costs</p>';
        html += '<p>• Shipping costs not included</p>';
        html += '</div>';
        
        this.container.innerHTML = html;
    }
    
    showError(message) {
        this.container.innerHTML = `<div class="text-red-600 text-center p-4">${message}</div>`;
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Get product ID from the page
    const productElement = document.querySelector('[data-product-id]');
    if (productElement) {
        const productId = productElement.dataset.productId;
        
        // Initialize pricing calculator
        window.pricingCalculator = new PricingCalculator(productId);
        
        // Initialize bulk pricing table if container exists
        const bulkTableContainer = document.getElementById('bulk-pricing-table');
        if (bulkTableContainer) {
            window.bulkPricingTable = new BulkPricingTable(productId);
        }
    }
});