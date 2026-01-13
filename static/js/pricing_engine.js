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
        '.dynamic-fields-wrapper input[type="checkbox"]'
    );

    inputs.forEach(input => {
        input.addEventListener('change', calculateTotal);
    });

    // Initial calculation
    calculateTotal();
}

function calculateTotal() {
    // Get base price from a data attribute or global variable
    // We expect the template to set a variable or data attribute
    const priceElement = document.getElementById('stickyTotal');
    if (!priceElement) return;

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
    priceElement.style.transform = 'scale(1.1)';
    priceElement.style.color = '#059669'; // Success green
    setTimeout(() => {
        priceElement.style.transform = 'scale(1)';
        priceElement.style.color = ''; // Revert
    }, 200);
}
