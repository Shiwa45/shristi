// Design Tool Integration

// Design tool functions
function startFromTemplate() {
    // Redirect to design editor with template mode
    if (window.productData && window.productData.designToolEnabled) {
        const categorySlug = getCategorySlugFromUrl();
        const productSlug = getProductSlugFromUrl();
        window.open(`/design-tool/editor/${categorySlug}/${productSlug}/?mode=template`, '_blank');
    } else {
        alert('Design tool is not available for this product');
    }
}

function uploadDesign() {
    // Trigger file upload for design files
    const fileInput = document.getElementById('file-upload');
    if (fileInput) {
        fileInput.click();
    } else {
        // Redirect to design editor for upload
        if (window.productData && window.productData.designToolEnabled) {
            const categorySlug = getCategorySlugFromUrl();
            const productSlug = getProductSlugFromUrl();
            window.open(`/design-tool/editor/${categorySlug}/${productSlug}/?mode=upload`, '_blank');
        }
    }
}

function startDesigning() {
    // Redirect to the design editor
    if (window.productData && window.productData.designToolEnabled) {
        const categorySlug = getCategorySlugFromUrl();
        const productSlug = getProductSlugFromUrl();
        window.open(`/design-tool/editor/${categorySlug}/${productSlug}/`, '_blank');
    } else {
        alert('Design tool is not available for this product');
    }
}

function requestDesignHelp() {
    // Open contact form or design service request
    alert('Our design team will contact you within 24 hours. Coming soon!');
}

function selectTemplate(templateId) {
    console.log(`Template ${templateId} selected`);
    // Redirect to design editor with specific template
    if (window.productData && window.productData.designToolEnabled) {
        const categorySlug = getCategorySlugFromUrl();
        const productSlug = getProductSlugFromUrl();
        window.open(`/design-tool/editor/${categorySlug}/${productSlug}/?template=${templateId}`, '_blank');
    } else {
        alert('Design tool is not available for this product');
    }
}

function viewAllTemplates() {
    // Redirect to design editor template gallery
    if (window.productData && window.productData.designToolEnabled) {
        const categorySlug = getCategorySlugFromUrl();
        const productSlug = getProductSlugFromUrl();
        window.open(`/design-tool/editor/${categorySlug}/${productSlug}/?mode=templates`, '_blank');
    } else {
        alert('Template gallery is not available for this product');
    }
}

// Helper functions to extract slugs from current URL
function getCategorySlugFromUrl() {
    const path = window.location.pathname;
    const parts = path.split('/');
    // URL format: /services/{category_slug}/{product_slug}/
    return parts[2] || 'unknown';
}

function getProductSlugFromUrl() {
    const path = window.location.pathname;
    const parts = path.split('/');
    // URL format: /services/{category_slug}/{product_slug}/
    return parts[3] || 'unknown';
}

// Related product functions
function quickView(productSlug) {
    alert(`Quick view for ${productSlug} will be implemented`);
}

// Review functions
function writeReview() {
    alert('Review system will be implemented in Phase 4');
}

function requestSamples() {
    alert('Sample request system will be implemented');
}