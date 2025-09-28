// Product Options Handler

// File upload handling
function handleFileUpload(files) {
    const uploadedFilesContainer = document.getElementById('uploaded-files');
    if (!uploadedFilesContainer) return;

    uploadedFilesContainer.classList.remove('hidden');

    Array.from(files).forEach(file => {
        const fileItem = createFileItem(file);
        uploadedFilesContainer.appendChild(fileItem);
    });
}

function createFileItem(file) {
    const fileItem = document.createElement('div');
    fileItem.className = 'uploaded-file flex items-center justify-between p-3 bg-white rounded-lg border';

    const fileSizeMB = (file.size / 1024 / 1024).toFixed(2);

    fileItem.innerHTML = `
        <div class="file-info">
            <div class="file-name font-medium text-gray-900">${file.name}</div>
            <div class="file-size text-sm text-gray-600">${fileSizeMB} MB</div>
        </div>
        <button type="button" class="remove-btn text-red-600 hover:bg-red-50 p-1 rounded" onclick="removeFile(this)">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
        </button>
    `;

    return fileItem;
}

function removeFile(button) {
    const fileItem = button.closest('.uploaded-file');
    if (fileItem) {
        fileItem.remove();

        // Hide container if no files left
        const container = document.getElementById('uploaded-files');
        if (container && container.children.length === 0) {
            container.classList.add('hidden');
        }
    }
}

// Special instructions handler
function updateSpecialInstructions(value) {
    // Store special instructions for later use
    window.specialInstructions = value;
}