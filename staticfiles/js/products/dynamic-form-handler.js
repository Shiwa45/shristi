/**
 * Dynamic Form Handler for Product Forms
 * Handles conditional field display, pricing updates, and form validation
 */
class DynamicFormHandler {
    constructor(productData, pricingCalculator) {
        this.productData = productData;
        this.pricingCalculator = pricingCalculator;
        this.conditionalFields = {};
        this.formData = {};

        this.init();
    }

    init() {
        this.loadConditionalFieldsData();
        this.bindFormEvents();
        this.initializeFormState();
        this.setupFieldTriggers();

        // Make global functions available
        window.handleFieldTriggers = this.handleFieldTriggers.bind(this);
        window.updatePricing = this.updatePricing.bind(this);
    }

    loadConditionalFieldsData() {
        const conditionalDataElement = document.getElementById('conditional-fields-data');
        if (conditionalDataElement) {
            try {
                this.conditionalFields = JSON.parse(conditionalDataElement.textContent);
            } catch (e) {
                console.error('Failed to parse conditional fields data:', e);
            }
        }
    }

    bindFormEvents() {
        const formContainer = document.querySelector('.dynamic-form-container');
        if (!formContainer) return;

        // Bind change events to all form inputs
        formContainer.addEventListener('change', (e) => {
            if (e.target.matches('input, select, textarea')) {
                this.handleFieldChange(e.target);
            }
        });

        // Bind input events for real-time updates (for number inputs)
        formContainer.addEventListener('input', (e) => {
            if (e.target.type === 'number') {
                this.handleFieldChange(e.target);
            }
        });
    }

    initializeFormState() {
        // Collect initial form data
        this.collectFormData();

        // Apply initial conditional logic
        this.applyConditionalLogic();

        // Update initial pricing
        this.updatePricing();
    }

    collectFormData() {
        const formContainer = document.querySelector('.dynamic-form-container');
        if (!formContainer) return;

        const inputs = formContainer.querySelectorAll('input, select, textarea');
        this.formData = {};

        inputs.forEach(input => {
            if (input.type === 'radio') {
                if (input.checked) {
                    this.formData[input.name] = input.value;
                }
            } else if (input.type === 'checkbox') {
                if (!this.formData[input.name]) {
                    this.formData[input.name] = [];
                }
                if (input.checked) {
                    this.formData[input.name].push(input.value);
                }
            } else {
                this.formData[input.name] = input.value;
            }
        });
    }

    handleFieldChange(field) {
        // Update form data
        this.updateFormDataForField(field);

        // Apply conditional logic
        this.applyConditionalLogic();

        // Update pricing if field affects price
        if (field.dataset.priceAffecting === 'true') {
            this.updatePricing();
        }

        // Handle field-specific triggers
        if (field.dataset.triggers) {
            try {
                const triggers = JSON.parse(field.dataset.triggers);
                this.handleFieldTriggers(field.name, field.value, triggers);
            } catch (e) {
                console.error('Failed to parse field triggers:', e);
            }
        }
    }

    updateFormDataForField(field) {
        if (field.type === 'radio') {
            if (field.checked) {
                this.formData[field.name] = field.value;
            }
        } else if (field.type === 'checkbox') {
            if (!this.formData[field.name]) {
                this.formData[field.name] = [];
            }
            if (field.checked) {
                if (!this.formData[field.name].includes(field.value)) {
                    this.formData[field.name].push(field.value);
                }
            } else {
                this.formData[field.name] = this.formData[field.name].filter(val => val !== field.value);
            }
        } else {
            this.formData[field.name] = field.value;
        }
    }

    applyConditionalLogic() {
        Object.keys(this.conditionalFields).forEach(fieldName => {
            const fieldConfig = this.conditionalFields[fieldName];
            const condition = fieldConfig.condition;

            if (condition) {
                const shouldShow = this.evaluateCondition(condition);
                this.toggleFieldVisibility(fieldName, shouldShow);
            }
        });
    }

    evaluateCondition(condition) {
        const { field, value, operator } = condition;
        const actualValue = this.formData[field];

        switch (operator) {
            case 'equals':
                return String(actualValue) === String(value);
            case 'not_equals':
                return String(actualValue) !== String(value);
            case 'in':
                return Array.isArray(value) ? value.includes(actualValue) : false;
            case 'not_in':
                return Array.isArray(value) ? !value.includes(actualValue) : true;
            default:
                return true;
        }
    }

    toggleFieldVisibility(fieldName, shouldShow) {
        const fieldElement = document.querySelector(`[data-field="${fieldName}"]`);
        if (fieldElement) {
            if (shouldShow) {
                fieldElement.style.display = '';
                fieldElement.classList.remove('hidden');

                // Re-enable form elements
                const inputs = fieldElement.querySelectorAll('input, select, textarea');
                inputs.forEach(input => {
                    input.disabled = false;
                });
            } else {
                fieldElement.style.display = 'none';
                fieldElement.classList.add('hidden');

                // Disable and clear form elements
                const inputs = fieldElement.querySelectorAll('input, select, textarea');
                inputs.forEach(input => {
                    input.disabled = true;
                    if (input.type === 'checkbox' || input.type === 'radio') {
                        input.checked = false;
                    } else {
                        input.value = '';
                    }
                });

                // Remove from form data
                delete this.formData[fieldName];
            }
        }
    }

    handleFieldTriggers(fieldName, fieldValue, triggers) {
        // Handle specific field logic based on triggers
        if (fieldName === 'interior_color') {
            this.handleInteriorColorChange(fieldValue, triggers);
        }

        // Re-apply conditional logic after triggers
        this.applyConditionalLogic();
    }

    handleInteriorColorChange(colorValue, triggers) {
        const isCombined = colorValue === 'combine_color';

        // Show/hide conditional page count fields
        triggers.forEach(triggerField => {
            if (triggerField === 'bw_page_count' || triggerField === 'color_page_count') {
                const field = document.querySelector(`[data-field="${triggerField}"]`);
                if (field) {
                    if (isCombined) {
                        field.style.display = '';
                        field.classList.remove('hidden');

                        // Make required if combined
                        const input = field.querySelector('input');
                        if (input) {
                            input.required = true;
                        }
                    } else {
                        field.style.display = 'none';
                        field.classList.add('hidden');

                        // Remove required and clear value
                        const input = field.querySelector('input');
                        if (input) {
                            input.required = false;
                            input.value = '';
                        }
                    }
                }
            }
        });

        // Hide/show regular page count field
        const pageCountField = document.querySelector('[data-field="page_count"]');
        if (pageCountField) {
            if (isCombined) {
                pageCountField.style.display = 'none';
                pageCountField.classList.add('hidden');
                const input = pageCountField.querySelector('input');
                if (input) {
                    input.required = false;
                    input.value = '';
                }
            } else {
                pageCountField.style.display = '';
                pageCountField.classList.remove('hidden');
                const input = pageCountField.querySelector('input');
                if (input) {
                    input.required = true;
                }
            }
        }
    }

    updatePricing() {
        if (!this.pricingCalculator) return;

        // Collect current form values for pricing calculation
        const pricingData = this.collectPricingData();

        // Calculate new price
        const calculatedPrice = this.calculateTotalPrice(pricingData);

        // Update price display
        this.updatePriceDisplay(calculatedPrice);
    }

    collectPricingData() {
        this.collectFormData();

        return {
            quantity: parseInt(this.formData.copies || this.formData.quantity || 100),
            interiorColor: this.formData.interior_color,
            pageCount: parseInt(this.formData.page_count || 0),
            bwPageCount: parseInt(this.formData.bw_page_count || 0),
            colorPageCount: parseInt(this.formData.color_page_count || 0),
            bookSize: this.formData.book_size,
            paperType: this.formData.paper_type,
            bindingType: this.formData.binding_type,
            coverFinish: this.formData.cover_finish,
            designService: this.formData.design_service,
            isbnAllocation: this.formData.isbn_allocation,
            printingSide: this.formData.printing_side,
            lamination: this.formData.lamination,
            deliveryTime: this.formData.delivery_time,
            customQuantity: parseInt(this.formData.custom_quantity || 0)
        };
    }

    calculateTotalPrice(pricingData) {
        let basePrice = parseFloat(this.productData.basePrice || 100);
        let totalPrice = basePrice;
        let modifiers = [];

        // Get all price-affecting fields
        const priceFields = document.querySelectorAll('[data-price-affecting="true"]');

        priceFields.forEach(field => {
            const fieldValue = this.getFieldValue(field);
            if (fieldValue) {
                const modifier = this.getFieldPriceModifier(field, fieldValue, pricingData.quantity);
                if (modifier !== 0) {
                    totalPrice += modifier;
                    modifiers.push({
                        field: field.name,
                        value: fieldValue,
                        modifier: modifier
                    });
                }
            }
        });

        // Apply quantity-based pricing for specific products
        if (pricingData.quantity) {
            totalPrice *= pricingData.quantity;
        }

        // Apply design service pricing
        if (pricingData.designService === 'yes_required') {
            const designCost = 1500; // Cover cost
            const pageCost = (pricingData.pageCount || pricingData.bwPageCount + pricingData.colorPageCount || 0) * 50;
            totalPrice += designCost + pageCost;
        }

        return {
            basePrice: basePrice,
            modifiers: modifiers,
            subtotal: totalPrice,
            totalPrice: totalPrice,
            quantity: pricingData.quantity
        };
    }

    getFieldValue(field) {
        if (field.type === 'radio') {
            const checkedRadio = document.querySelector(`input[name="${field.name}"]:checked`);
            return checkedRadio ? checkedRadio.value : null;
        } else if (field.type === 'checkbox') {
            const checkedBoxes = document.querySelectorAll(`input[name="${field.name}"]:checked`);
            return Array.from(checkedBoxes).map(cb => cb.value);
        } else {
            return field.value;
        }
    }

    getFieldPriceModifier(field, value, quantity = 1) {
        if (field.tagName === 'SELECT') {
            const selectedOption = field.querySelector(`option[value="${value}"]`);
            return selectedOption ? parseFloat(selectedOption.dataset.priceModifier || 0) : 0;
        } else if (field.type === 'radio') {
            const radioOption = document.querySelector(`input[name="${field.name}"][value="${value}"]`);
            return radioOption ? parseFloat(radioOption.dataset.priceModifier || 0) : 0;
        }

        return 0;
    }

    updatePriceDisplay(calculatedPrice) {
        // Update main price display
        const priceElement = document.querySelector('.price-amount');
        if (priceElement) {
            priceElement.textContent = calculatedPrice.totalPrice.toLocaleString('en-IN');
        }

        // Update unit price if applicable
        const unitPriceElement = document.querySelector('.unit-price');
        if (unitPriceElement && calculatedPrice.quantity > 1) {
            const unitPrice = calculatedPrice.totalPrice / calculatedPrice.quantity;
            unitPriceElement.textContent = `₹${unitPrice.toFixed(2)} per unit`;
        }

        // Update price breakdown if container exists
        const breakdownElement = document.querySelector('.price-breakdown');
        if (breakdownElement) {
            this.updatePriceBreakdown(breakdownElement, calculatedPrice);
        }
    }

    updatePriceBreakdown(container, calculatedPrice) {
        let html = `
            <div class="price-breakdown-item">
                <span>Base Price:</span>
                <span>₹${calculatedPrice.basePrice.toLocaleString('en-IN')}</span>
            </div>
        `;

        calculatedPrice.modifiers.forEach(modifier => {
            const sign = modifier.modifier >= 0 ? '+' : '';
            html += `
                <div class="price-breakdown-item">
                    <span>${modifier.field}:</span>
                    <span>${sign}₹${modifier.modifier.toLocaleString('en-IN')}</span>
                </div>
            `;
        });

        if (calculatedPrice.quantity > 1) {
            html += `
                <div class="price-breakdown-item">
                    <span>Quantity (${calculatedPrice.quantity}):</span>
                    <span>×${calculatedPrice.quantity}</span>
                </div>
            `;
        }

        html += `
            <div class="price-breakdown-total">
                <span><strong>Total:</strong></span>
                <span><strong>₹${calculatedPrice.totalPrice.toLocaleString('en-IN')}</strong></span>
            </div>
        `;

        container.innerHTML = html;
    }

    setupFieldTriggers() {
        // Additional setup for any global field triggers
        console.log('Dynamic form handler initialized with', Object.keys(this.conditionalFields).length, 'conditional fields');
    }

    // Public method to manually trigger form updates
    refreshForm() {
        this.collectFormData();
        this.applyConditionalLogic();
        this.updatePricing();
    }

    // Get current form data (useful for debugging or external access)
    getFormData() {
        this.collectFormData();
        return { ...this.formData };
    }
}