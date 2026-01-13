document.addEventListener('DOMContentLoaded', function () {
    // Initial setup
    initJsonEditors();

    // Re-initialize when new inline forms are added
    if (typeof django !== 'undefined' && django.jQuery) {
        django.jQuery(document).on('formset:added', function (event, $row, formsetName) {
            initJsonEditors();
        });
    }
});

function initJsonEditors() {
    // Target all textareas that are likely JSON fields for options
    // Specifically targeting the 'options' field in ProductFormField
    const textareas = document.querySelectorAll('textarea[name$="options"]');

    textareas.forEach(function (textarea) {
        // Skip if already initialized
        if (textarea.getAttribute('data-json-editor-initialized') === 'true') {
            return;
        }

        // Hide the original textarea
        // textarea.style.display = 'none'; // Commented out to allow fallback/debugging if needed
        textarea.style.height = '60px'; // Minimized but visible for safety
        textarea.style.opacity = '0.5';

        // Create editor container
        const container = document.createElement('div');
        container.className = 'json-editor-container';
        container.style.marginBottom = '20px';
        container.style.marginTop = '10px';

        // Build the table
        const table = document.createElement('table');
        table.className = 'json-editor-table';
        table.style.width = '100%';
        table.style.borderCollapse = 'collapse';
        table.style.border = '1px solid #ccc';

        // Table Header
        const thead = document.createElement('thead');
        thead.innerHTML = `
            <tr style="background: #f8f8f8; border-bottom: 2px solid #ddd;">
                <th style="padding: 10px; text-align: left; width: 25%;">Label (Visible)</th>
                <th style="padding: 10px; text-align: left; width: 20%;">Value (Internal)</th>
                <th style="padding: 10px; text-align: left; width: 15%;">Price (+/-)</th>
                <th style="padding: 10px; text-align: left; width: 30%;">Image URL</th>
                <th style="padding: 10px; text-align: center; width: 10%;">Actions</th>
            </tr>
        `;
        table.appendChild(thead);

        // Table Body
        const tbody = document.createElement('tbody');
        table.appendChild(tbody);

        container.appendChild(table);

        // Add Row Button
        const addButton = document.createElement('button');
        addButton.type = 'button';
        addButton.innerText = '+ Add Option';
        addButton.className = 'button'; // Django admin button style
        addButton.style.marginTop = '10px';
        addButton.onclick = function (e) {
            e.preventDefault();
            addOptionRow(tbody, { label: '', value: '', price_modifier: 0, image_url: '' }, textarea);
        };
        container.appendChild(addButton);

        // Insert before the textarea
        textarea.parentNode.insertBefore(container, textarea);

        // Load initial data
        try {
            const initialData = JSON.parse(textarea.value || '[]');
            if (Array.isArray(initialData)) {
                initialData.forEach(item => addOptionRow(tbody, item, textarea));
            }
        } catch (e) {
            console.error('Invalid JSON in textarea:', e);
            // If invalid, maybe show an error or just let the user see the raw textarea
        }

        // Mark as initialized
        textarea.setAttribute('data-json-editor-initialized', 'true');

        // Add label to original textarea
        const rawLabel = document.createElement('div');
        rawLabel.innerText = 'Raw JSON (Update automatically):';
        rawLabel.style.fontSize = '10px';
        rawLabel.style.color = '#999';
        textarea.parentNode.insertBefore(rawLabel, textarea);
    });
}

function addOptionRow(tbody, data, sourceTextarea) {
    const tr = document.createElement('tr');
    tr.style.borderBottom = '1px solid #eee';

    // Label Input
    const tdLabel = document.createElement('td');
    tdLabel.style.padding = '8px';
    const inputLabel = document.createElement('input');
    inputLabel.type = 'text';
    inputLabel.value = data.label || '';
    inputLabel.className = 'vTextField';
    inputLabel.style.width = '100%';
    inputLabel.placeholder = 'e.g. A4 Size';
    tdLabel.appendChild(inputLabel);
    tr.appendChild(tdLabel);

    // Value Input
    const tdValue = document.createElement('td');
    tdValue.style.padding = '8px';
    const inputValue = document.createElement('input');
    inputValue.type = 'text';
    inputValue.value = data.value || '';
    inputValue.className = 'vTextField';
    inputValue.style.width = '100%';
    inputValue.placeholder = 'e.g. a4';
    // Auto-fill value from label if empty
    inputLabel.addEventListener('blur', function () {
        if (!inputValue.value) {
            inputValue.value = inputLabel.value.toLowerCase().replace(/[^a-z0-9]/g, '_');
            updateJson(tbody, sourceTextarea);
        }
    });
    tdValue.appendChild(inputValue);
    tr.appendChild(tdValue);

    // Price Input
    const tdPrice = document.createElement('td');
    tdPrice.style.padding = '8px';
    const inputPrice = document.createElement('input');
    inputPrice.type = 'number';
    inputPrice.value = data.price_modifier || 0;
    inputPrice.className = 'vIntegerField';
    inputPrice.style.width = '100%';
    inputPrice.step = '0.01';
    tdPrice.appendChild(inputPrice);
    tr.appendChild(tdPrice);

    // Image URL Input
    const tdImage = document.createElement('td');
    tdImage.style.padding = '8px';
    const inputImage = document.createElement('input');
    inputImage.type = 'text';
    inputImage.value = data.image_url || '';
    inputImage.className = 'vTextField';
    inputImage.style.width = '100%';
    inputImage.placeholder = '/static/...';
    tdImage.appendChild(inputImage);
    tr.appendChild(tdImage);

    // Actions
    const tdActions = document.createElement('td');
    tdActions.style.padding = '8px';
    tdActions.style.textAlign = 'center';
    const deleteBtn = document.createElement('button');
    deleteBtn.innerText = 'X';
    deleteBtn.style.color = 'red';
    deleteBtn.style.fontWeight = 'bold';
    deleteBtn.style.cursor = 'pointer';
    deleteBtn.style.background = 'none';
    deleteBtn.style.border = 'none';
    deleteBtn.onclick = function (e) {
        e.preventDefault();
        tbody.removeChild(tr);
        updateJson(tbody, sourceTextarea);
    };
    tdActions.appendChild(deleteBtn);
    tr.appendChild(tdActions);

    tbody.appendChild(tr);

    // Attach event listeners to update JSON on change
    const inputs = [inputLabel, inputValue, inputPrice, inputImage];
    inputs.forEach(input => {
        input.addEventListener('input', () => updateJson(tbody, sourceTextarea));
        input.addEventListener('change', () => updateJson(tbody, sourceTextarea));
    });

    // Initial update if adding a new empty row handled by caller or bulk update
}

function updateJson(tbody, textarea) {
    const rows = tbody.querySelectorAll('tr');
    const data = [];

    rows.forEach(row => {
        const inputs = row.querySelectorAll('input');
        if (inputs.length >= 3) {
            const label = inputs[0].value.trim();
            const value = inputs[1].value.trim();
            const price = parseFloat(inputs[2].value) || 0;
            const imageUrl = inputs[3].value.trim();

            if (label || value) { // Only add if at least label or value exists
                const item = {
                    value: value || label.toLowerCase(), // Fallback to label as value
                    label: label || value, // Fallback to value as label
                    price_modifier: price
                };
                if (imageUrl) {
                    item.image_url = imageUrl;
                }
                data.push(item);
            }
        }
    });

    textarea.value = JSON.stringify(data, null, 2);
}
