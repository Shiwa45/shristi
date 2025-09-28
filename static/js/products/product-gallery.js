// Product Gallery JavaScript

let currentImageIndex = 0;
let galleryImages = [];

// Initialize gallery
document.addEventListener('DOMContentLoaded', function() {
    initializeGallery();
    initializeTabs();
});

function initializeGallery() {
    // Get all gallery images
    const imageElements = document.querySelectorAll('.thumbnail-nav img');
    galleryImages = Array.from(imageElements).map(img => img.src);

    // Add click handlers to thumbnails
    document.querySelectorAll('.thumbnail-item').forEach((thumb, index) => {
        thumb.addEventListener('click', () => {
            changeMainImage(galleryImages[index], index);
        });
    });
}

function changeMainImage(imageSrc, index) {
    const mainImage = document.getElementById('main-product-image');
    if (mainImage) {
        mainImage.src = imageSrc;
    }

    currentImageIndex = index;

    // Update active thumbnail
    document.querySelectorAll('.thumbnail-item').forEach((thumb, i) => {
        if (i === index) {
            thumb.classList.add('active');
        } else {
            thumb.classList.remove('active');
        }
    });
}

function openLightbox(index) {
    const modal = document.getElementById('lightbox-modal');
    const lightboxImage = document.getElementById('lightbox-image');
    const imageCounter = document.getElementById('image-counter');

    if (modal && lightboxImage) {
        currentImageIndex = index;
        lightboxImage.src = galleryImages[currentImageIndex];

        if (imageCounter) {
            imageCounter.textContent = `${currentImageIndex + 1} / ${galleryImages.length}`;
        }

        modal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    }
}

function closeLightbox() {
    const modal = document.getElementById('lightbox-modal');
    if (modal) {
        modal.classList.add('hidden');
        document.body.style.overflow = '';
    }
}

function previousImage() {
    if (galleryImages.length === 0) return;

    currentImageIndex = currentImageIndex > 0 ? currentImageIndex - 1 : galleryImages.length - 1;
    updateLightboxImage();
}

function nextImage() {
    if (galleryImages.length === 0) return;

    currentImageIndex = currentImageIndex < galleryImages.length - 1 ? currentImageIndex + 1 : 0;
    updateLightboxImage();
}

function updateLightboxImage() {
    const lightboxImage = document.getElementById('lightbox-image');
    const imageCounter = document.getElementById('image-counter');

    if (lightboxImage && galleryImages[currentImageIndex]) {
        lightboxImage.src = galleryImages[currentImageIndex];
    }

    if (imageCounter) {
        imageCounter.textContent = `${currentImageIndex + 1} / ${galleryImages.length}`;
    }
}

// Tab functionality
function switchTab(tabName) {
    // Hide all tab panels
    document.querySelectorAll('.tab-panel').forEach(panel => {
        panel.classList.add('hidden');
    });

    // Remove active class from all tab buttons
    document.querySelectorAll('.tab-button').forEach(button => {
        button.classList.remove('active', 'bg-white', 'shadow', 'text-blue-700');
        button.classList.add('text-blue-100');
    });

    // Show selected tab panel
    const selectedPanel = document.getElementById(`content-${tabName}`);
    if (selectedPanel) {
        selectedPanel.classList.remove('hidden');
    }

    // Add active class to selected tab button
    const selectedButton = document.getElementById(`tab-${tabName}`);
    if (selectedButton) {
        selectedButton.classList.add('active', 'bg-white', 'shadow', 'text-blue-700');
        selectedButton.classList.remove('text-blue-100');
    }
}

function initializeTabs() {
    // Set first tab as active by default
    switchTab('specifications');
}

// FAQ functionality
function toggleFAQ(button) {
    const faqItem = button.closest('.faq-item');
    const answer = faqItem.querySelector('.faq-answer');
    const icon = button.querySelector('svg');

    if (answer && icon) {
        const isHidden = answer.classList.contains('hidden');

        if (isHidden) {
            answer.classList.remove('hidden');
            icon.style.transform = 'rotate(180deg)';
        } else {
            answer.classList.add('hidden');
            icon.style.transform = 'rotate(0deg)';
        }
    }
}

// Keyboard navigation for lightbox
document.addEventListener('keydown', function(e) {
    const modal = document.getElementById('lightbox-modal');
    if (modal && !modal.classList.contains('hidden')) {
        switch(e.key) {
            case 'Escape':
                closeLightbox();
                break;
            case 'ArrowLeft':
                previousImage();
                break;
            case 'ArrowRight':
                nextImage();
                break;
        }
    }
});

// Close lightbox when clicking outside image
document.addEventListener('click', function(e) {
    const modal = document.getElementById('lightbox-modal');
    if (modal && e.target === modal) {
        closeLightbox();
    }
});