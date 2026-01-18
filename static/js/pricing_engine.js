/**
 * Pricing Engine for Shristi Printing
 * Calculates total price based on base price and selected options.
 */

document.addEventListener('DOMContentLoaded', function () {
    initPricingCalculator();
});

function initPricingCalculator() {
    // Find all inputs that might affect price
    const inputs = document.querySelectorAll(
        '.dynamic-fields-wrapper select, ' +
        '.dynamic-fields-wrapper input[type="radio"], ' +
        '.dynamic-fields-wrapper input[type="checkbox"], ' +
        '.dynamic-fields-wrapper input[type="number"], ' +
        '.dynamic-fields-wrapper input[type="text"], ' +
        '.dynamic-fields-wrapper textarea'
    );

    inputs.forEach(input => {
        const eventType = (input.type === 'radio' || input.type === 'checkbox' || input.tagName === 'SELECT')
            ? 'change'
            : 'input';
        input.addEventListener(eventType, calculateTotal);
    });

    // Initial calculation
    calculateTotal();
}

function calculateTotal() {
    // Get base price from a data attribute or global variable
    // We expect the template to set a variable or data attribute
    const priceElement = document.getElementById('stickyTotal');
    if (!priceElement) return;

    const quantityInfo = getQuantityInfo();
    if (!areRequiredFieldsComplete(quantityInfo)) {
        updatePriceDisplay(priceElement, 0, false);
        return;
    }

    // Remove currency symbol and commas to parse
    let basePriceText = priceElement.getAttribute('data-base-price');
    if (!basePriceText) {
        // Fallback: try to parse from text content (risky but works if clean)
        basePriceText = priceElement.textContent.replace(/[^0-9.]/g, '');
        // Save it for future reference so we don't double add
        priceElement.setAttribute('data-base-price', basePriceText);
    }

    let totalPrice = parseFloat(basePriceText) || 0;

    // Iterate through all fields
    const wrappers = document.querySelectorAll('.form-field-container');

    wrappers.forEach(wrapper => {
        if (wrapper.dataset.fieldName === 'quantity') {
            return;
        }

        // Find selected option
        const select = wrapper.querySelector('select');
        const checkedRadio = wrapper.querySelector('input[type="radio"]:checked');
        const checkedCheckboxes = wrapper.querySelectorAll('input[type="checkbox"]:checked');

        let modifier = 0;

        if (select) {
            const selectedOption = select.options[select.selectedIndex];
            if (selectedOption) {
                modifier = parseFloat(selectedOption.getAttribute('data-price-modifier') || 0);
            }
        } else if (checkedRadio) {
            modifier = parseFloat(checkedRadio.getAttribute('data-price-modifier') || 0);
        } else if (checkedCheckboxes.length > 0) {
            checkedCheckboxes.forEach(cb => {
                modifier += parseFloat(cb.getAttribute('data-price-modifier') || 0);
            });
        }

        totalPrice += modifier;
    });

    if (quantityInfo && quantityInfo.value !== null) {
        totalPrice *= quantityInfo.value;
    }

    updatePriceDisplay(priceElement, totalPrice, true);
}

function areRequiredFieldsComplete(quantityInfo) {
    const wrapper = document.querySelector('.dynamic-fields-wrapper');
    if (!wrapper) {
        return false;
    }

    const fieldContainers = Array.from(wrapper.querySelectorAll('.form-field-container'));

    for (const container of fieldContainers) {
        if (!isElementVisible(container)) {
            continue;
        }

        const requiredInputs = Array.from(container.querySelectorAll('[required]'))
            .filter(field => !field.disabled);
        if (requiredInputs.length === 0) {
            continue;
        }

        const requiredRadios = requiredInputs.filter(field => field.type === 'radio');
        if (requiredRadios.length > 0) {
            const groupName = requiredRadios[0].name;
            const radios = Array.from(wrapper.querySelectorAll(`input[type="radio"][name="${groupName}"]`))
                .filter(field => !field.disabled);
            if (!radios.some(radio => radio.checked)) {
                return false;
            }
            continue;
        }

        for (const field of requiredInputs) {
            if (field.type === 'checkbox') {
                if (!field.checked) {
                    return false;
                }
                continue;
            }

            if (field.tagName === 'SELECT') {
                if (!field.value) {
                    return false;
                }
                continue;
            }

            if (!field.value || !field.checkValidity()) {
                return false;
            }
        }
    }

    if (quantityInfo && quantityInfo.isRequired && quantityInfo.value === null) {
        return false;
    }

    return true;
}

function getQuantityInfo() {
    const wrapper = document.querySelector('.dynamic-fields-wrapper');
    if (!wrapper) {
        return null;
    }

    const quantityField = findQuantityField(wrapper);
    if (!quantityField || !isElementVisible(quantityField)) {
        return null;
    }

    const rawValue = quantityField.value;
    if (!rawValue) {
        return { field: quantityField, value: null, isRequired: true };
    }

    const quantity = parseInt(rawValue, 10);
    if (Number.isNaN(quantity) || quantity <= 0) {
        return { field: quantityField, value: null, isRequired: true };
    }

    const minAttr = quantityField.getAttribute('min');
    if (minAttr) {
        const minValue = parseInt(minAttr, 10);
        if (!Number.isNaN(minValue) && quantity < minValue) {
            return { field: quantityField, value: null, isRequired: true };
        }
    }

    return { field: quantityField, value: quantity, isRequired: true };
}

function findQuantityField(wrapper) {
    const directMatch = wrapper.querySelector('[name="quantity"]');
    if (directMatch) {
        return directMatch;
    }

    const candidates = Array.from(wrapper.querySelectorAll('input[type="number"], input[type="text"], select'));
    const quantityRegex = /(qty|quantity|copies|pieces|units)/i;

    for (const field of candidates) {
        const name = field.getAttribute('name') || '';
        const id = field.getAttribute('id') || '';
        const container = field.closest('.form-field-container');
        const dataName = container ? container.dataset.fieldName || '' : '';
        if (quantityRegex.test(name) || quantityRegex.test(id) || quantityRegex.test(dataName)) {
            return field;
        }
    }

    for (const field of candidates) {
        if (field.tagName === 'SELECT' && isNumericOptionSelect(field)) {
            return field;
        }
    }

    return null;
}

function isNumericOptionSelect(select) {
    const options = Array.from(select.options || []);
    const values = options
        .map(option => option.value)
        .filter(value => value !== '');

    if (values.length === 0) {
        return false;
    }

    const numericValues = values
        .map(value => parseInt(value, 10))
        .filter(value => !Number.isNaN(value));

    if (numericValues.length !== values.length) {
        return false;
    }

    return Math.max(...numericValues) > 1;
}

function isElementVisible(element) {
    return !!(element && element.offsetParent !== null);
}

function updatePriceDisplay(priceElement, totalPrice, animate) {
    // Update display
    // Format as currency (Indian Rupee)
    const formattedPrice = new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        minimumFractionDigits: 0,
        maximumFractionDigits: 2
    }).format(totalPrice);

    priceElement.textContent = formattedPrice;

    // Add animation effect
    if (animate) {
        priceElement.style.transform = 'scale(1.1)';
        priceElement.style.color = '#059669'; // Success green
        setTimeout(() => {
            priceElement.style.transform = 'scale(1)';
            priceElement.style.color = ''; // Revert
        }, 200);
    } else {
        priceElement.style.transform = 'scale(1)';
        priceElement.style.color = '';
    }
}
