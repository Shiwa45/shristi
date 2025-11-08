// Sequential Form Engine for Category-Specific Pages
class SequentialFormEngine {
    constructor(categoryConfig) {
        this.category = categoryConfig.category;
        this.sections = [];
        this.currentSection = 0;
        this.formData = {};
        this.validationRules = {};
        
        this.init();
    }
    
    init() {
        console.log('🔄 Sequential Form Engine Initialized for:', this.category);
        
        // Get all form sections
        this.sections = Array.from(document.querySelectorAll('.form-section'));
        
        // Initialize first section as enabled
        if (this.sections.length > 0) {
            this.enableSection(0);
        }
        
        // Attach event listeners
        this.attachFieldListeners();
        this.attachSectionListeners();
        
        console.log('✅ Form engine ready with', this.sections.length, 'sections');
    }
    
    attachFieldListeners() {
        // Listen to all form inputs
        const inputs = document.querySelectorAll('input, select, textarea');
        
        inputs.forEach(input => {
            const eventType = input.type === 'radio' || input.type === 'checkbox' ? 'change' : 'input';
            
            input.addEventListener(eventType, (e) => {
                this.handleFieldChange(e);
            });
        });
    }
    
    attachSectionListeners() {
        // Add click handlers for option elements
        document.querySelectorAll('.option-item, .color-option, .size-option, .paper-option, .binding-option, .finish-option, .toggle-option, .isbn-option').forEach(option => {
            option.addEventListener('click', (e) => {
                const input = option.querySelector('input');
                if (input && !input.disabled) {
                    input.checked = true;
                    this.handleFieldChange({ target: input });
                    this.updateOptionSelection(option);
                }
            });
        });
    }
    
    handleFieldChange(event) {
        const field = event.target;
        const fieldName = field.name;
        const fieldValue = field.value;
        const sectionElement = field.closest('.form-section');
        
        if (!sectionElement) return;
        
        console.log(`📝 Field changed: ${fieldName} = ${fieldValue}`);
        
        // Update form data
        this.formData[fieldName] = fieldValue;
        
        // Handle conditional fields
        this.handleConditionalFields(fieldName, fieldValue);
        
        // Validate current section
        const sectionIndex = this.sections.indexOf(sectionElement);
        const isValid = this.validateSection(sectionIndex);
        
        if (isValid) {
            this.markSectionComplete(sectionIndex);
            this.enableNextSection(sectionIndex);
        }
        
        // Trigger pricing update
        if (window.categoryPricingCalculator) {
            window.categoryPricingCalculator.updatePricing(this.formData);
        }
        
        // Update specifications summary
        this.updateSpecificationsSummary();
    }
    
    handleConditionalFields(triggerField, value) {
        // Handle book printing specific conditional logic
        if (this.category === 'book-printing') {
            this.handleBookPrintingConditionals(triggerField, value);
        }
    }
    
    handleBookPrintingConditionals(triggerField, value) {
        // Handle interior color conditional fields
        if (triggerField === 'interior_color') {
            const standardPageCount = document.getElementById('standard-page-count');
            const combinePageCounts = document.getElementById('combine-page-counts');
            
            if (value === 'combine_color') {
                standardPageCount.style.display = 'none';
                combinePageCounts.classList.add('show');
                document.getElementById('page_count').required = false;
                document.getElementById('bw_page_count').required = true;
                document.getElementById('color_page_count').required = true;
            } else {
                standardPageCount.style.display = 'block';
                combinePageCounts.classList.remove('show');
                document.getElementById('page_count').required = true;
                document.getElementById('bw_page_count').required = false;
                document.getElementById('color_page_count').required = false;
            }
        }
        
        // Handle page count changes for binding restrictions
        if (triggerField === 'page_count' || triggerField === 'bw_page_count' || triggerField === 'color_page_count') {
            this.updateBindingOptions();
        }
        
        // Handle design service file uploads
        if (triggerField === 'design_service') {
            const fileUploadSection = document.getElementById('design-file-uploads');
            if (value === 'yes_design') {
                fileUploadSection.classList.add('show');
            } else {
                fileUploadSection.classList.remove('show');
            }
        }
    }
    
    updateBindingOptions() {
        const pageCountInput = document.getElementById('page_count');
        const bwPageCountInput = document.getElementById('bw_page_count');
        const colorPageCountInput = document.getElementById('color_page_count');
        
        let totalPages = 0;
        
        if (pageCountInput.style.display !== 'none' && pageCountInput.value) {
            totalPages = parseInt(pageCountInput.value) || 0;
        } else {
            const bwPages = parseInt(bwPageCountInput.value) || 0;
            const colorPages = parseInt(colorPageCountInput.value) || 0;
            totalPages = bwPages + colorPages;
        }
        
        const bindingOptions = document.querySelectorAll('.binding-option[data-min-pages="30"]');
        bindingOptions.forEach(option => {
            const input = option.querySelector('input');
            if (totalPages < 30) {
                option.classList.add('disabled');
                input.disabled = true;
                if (input.checked) {
                    input.checked = false;
                    delete this.formData[input.name];
                }
            } else {
                option.classList.remove('disabled');
                input.disabled = false;
            }
        });
    }
    
    validateSection(sectionIndex) {
        const section = this.sections[sectionIndex];
        const requiredFields = section.querySelectorAll('input[required], select[required], textarea[required]');
        
        let isValid = true;
        
        requiredFields.forEach(field => {
            if (!field.disabled && !this.isFieldValid(field)) {
                isValid = false;
            }
        });
        
        return isValid;
    }
    
    isFieldValid(field) {
        if (field.type === 'radio') {
            const radioGroup = document.querySelectorAll(`input[name="${field.name}"]`);
            return Array.from(radioGroup).some(radio => radio.checked);
        } else if (field.type === 'checkbox' && field.required) {
            return field.checked;
        } else {
            return field.value.trim() !== '';
        }
    }
    
    markSectionComplete(sectionIndex) {
        const section = this.sections[sectionIndex];
        section.classList.add('completed');
        section.classList.remove('enabled');
        
        // Update section number styling
        const sectionNumber = section.querySelector('.section-number');
        if (sectionNumber) {
            sectionNumber.innerHTML = '<i class="fas fa-check"></i>';
        }
    }
    
    enableNextSection(currentIndex) {
        const nextIndex = currentIndex + 1;
        if (nextIndex < this.sections.length) {
            this.enableSection(nextIndex);
        } else {
            // All sections completed
            this.onAllSectionsComplete();
        }
    }
    
    enableSection(sectionIndex) {
        if (sectionIndex >= this.sections.length) return;
        
        const section = this.sections[sectionIndex];
        section.classList.remove('disabled');
        section.classList.add('enabled', 'newly-enabled');
        
        // Remove animation class after animation completes
        setTimeout(() => {
            section.classList.remove('newly-enabled');
        }, 500);
        
        // Scroll to section
        section.scrollIntoView({ 
            behavior: 'smooth', 
            block: 'start',
            inline: 'nearest'
        });
        
        this.currentSection = sectionIndex;
        
        console.log(`✅ Section ${sectionIndex + 1} enabled`);
    }
    
    resetDependentSections(fromIndex) {
        for (let i = fromIndex + 1; i < this.sections.length; i++) {
            const section = this.sections[i];
            section.classList.remove('enabled', 'completed');
            section.classList.add('disabled');
            
            // Reset section number
            const sectionNumber = section.querySelector('.section-number');
            if (sectionNumber) {
                sectionNumber.textContent = i + 1;
            }
            
            // Clear form data for this section
            const inputs = section.querySelectorAll('input, select, textarea');
            inputs.forEach(input => {
                if (input.name && this.formData[input.name]) {
                    delete this.formData[input.name];
                }
                
                if (input.type === 'radio' || input.type === 'checkbox') {
                    input.checked = false;
                } else {
                    input.value = '';
                }
            });
        }
        
        this.currentSection = fromIndex;
    }
    
    updateOptionSelection(selectedOption) {
        // Remove selected class from siblings
        const parent = selectedOption.parentElement;
        const siblings = parent.querySelectorAll('.option-item, .color-option, .size-option, .paper-option, .binding-option, .finish-option, .toggle-option, .isbn-option');
        
        siblings.forEach(sibling => {
            sibling.classList.remove('selected');
        });
        
        // Add selected class to current option
        selectedOption.classList.add('selected');
    }
    
    updateSpecificationsSummary() {
        const summaryList = document.getElementById('specifications-list');
        if (!summaryList) return;
        
        // Keep the category item and clear others
        const categoryItem = summaryList.querySelector('.summary-item');
        summaryList.innerHTML = '';
        if (categoryItem) {
            summaryList.appendChild(categoryItem);
        }
        
        // Add current form data to summary
        Object.entries(this.formData).forEach(([key, value]) => {
            if (value && value !== '') {
                const item = document.createElement('div');
                item.className = 'summary-item';
                
                const label = this.getFieldLabel(key);
                const displayValue = this.getDisplayValue(key, value);
                
                item.innerHTML = `
                    <span class="summary-label">${label}:</span>
                    <span class="summary-value">${displayValue}</span>
                `;
                
                summaryList.appendChild(item);
            }
        });
    }
    
    getFieldLabel(fieldName) {
        const fieldLabels = {
            'interior_color': 'Interior Color',
            'book_size': 'Book Size',
            'page_count': 'Page Count',
            'bw_page_count': 'B&W Pages',
            'color_page_count': 'Color Pages',
            'paper_type': 'Paper Type',
            'binding_type': 'Binding Type',
            'cover_finish': 'Cover Finish',
            'design_service': 'Design Service',
            'isbn_allocation': 'ISBN Allocation'
        };
        
        return fieldLabels[fieldName] || fieldName.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
    }
    
    getDisplayValue(fieldName, value) {
        const displayValues = {
            'interior_color': {
                'bw_premium': 'Black & White Premium',
                'bw_standard': 'Black & White Standard',
                'color_premium': 'Color Premium',
                'color_standard': 'Color Standard',
                'combine_color': 'Combine Color'
            },
            'book_size': {
                'a4': 'A4 (8.27 x 11.69 in)',
                'letter': 'Letter (8.5 x 11 in)',
                'executive': 'Executive (7 x 10 in)',
                'a5': 'A5 (5.83 x 8.27 in)'
            },
            'paper_type': {
                '75gsm': '75 GSM Standard',
                '100gsm': '100 GSM Premium',
                '100gsm_art': '100 GSM Art Paper',
                '130gsm_art': '130 GSM Art Paper'
            },
            'binding_type': {
                'saddle_stitch': 'Saddle Stitch',
                'spiral_binding': 'Spiral Binding',
                'paperback_perfect': 'Paperback (Perfect)',
                'hardcover': 'Hardcover'
            },
            'cover_finish': {
                'glossy': 'Glossy',
                'matte': 'Matte'
            },
            'design_service': {
                'not_required': 'Not Required',
                'yes_design': 'Yes, Design Service'
            },
            'isbn_allocation': {
                'not_apply': 'Not Required',
                'assign_isbn': 'Yes, Assign ISBN'
            }
        };
        
        if (displayValues[fieldName] && displayValues[fieldName][value]) {
            return displayValues[fieldName][value];
        }
        
        return value;
    }
    
    onAllSectionsComplete() {
        console.log('🎉 All sections completed!');
        
        // Enable order button
        const orderButton = document.getElementById('order-button');
        if (orderButton) {
            orderButton.disabled = false;
            orderButton.classList.add('pulse');
        }
        
        // Show completion message
        this.showCompletionMessage();
    }
    
    showCompletionMessage() {
        // You can add a completion message or animation here
        console.log('✅ Form ready for submission');
    }
    
    getFormData() {
        return { ...this.formData };
    }
    
    isFormComplete() {
        return this.currentSection >= this.sections.length - 1;
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    if (window.categoryConfig) {
        console.log('🚀 Starting Sequential Form Engine...');
        window.sequentialFormEngine = new SequentialFormEngine(window.categoryConfig);
    } else {
        console.warn('⚠️ Category config not found');
    }
});

// Add CSS for pulse animation
const style = document.createElement('style');
style.textContent = `
    .pulse {
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% {
            box-shadow: 0 0 0 0 rgba(102, 126, 234, 0.7);
        }
        70% {
            box-shadow: 0 0 0 10px rgba(102, 126, 234, 0);
        }
        100% {
            box-shadow: 0 0 0 0 rgba(102, 126, 234, 0);
        }
    }
`;
document.head.appendChild(style);