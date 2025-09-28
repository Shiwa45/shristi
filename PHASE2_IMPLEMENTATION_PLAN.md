# Phase 2: Product Page Design & Frontend Implementation Plan for Claude Codebase

## Overview
Create professional product pages inspired by QinPrinting design with interactive pricing calculators, responsive design, and seamless user experience. Build individual product pages for all 28 static products with real-time pricing and design tool integration.

## Project Context
- **Phase 1 Status**: ✅ COMPLETE - 28 static products with pricing API created
- **Current Goal**: Build QinPrinting-inspired frontend with pricing calculators
- **Design Inspiration**: https://www.qinprinting.com/ (clean, professional layout)
- **Pricing Inspiration**: Creative Print Arts (already implemented in backend)

## Design Principles (QinPrinting Style)

### Layout Structure
- **Hero Section**: Product showcase with key benefits and call-to-action
- **Product Gallery**: High-quality images with thumbnail navigation
- **Options Panel**: Left sidebar with product customization options
- **Pricing Calculator**: Right sidebar with real-time price updates
- **Product Details**: Tabbed sections for specifications, samples, FAQ
- **Related Products**: Horizontal scroll of similar products

### Visual Design
- **Clean & Professional**: Minimal design with lots of white space
- **Modern Typography**: Clear headings and readable body text
- **Color Scheme**: Professional blues and grays with accent colors
- **Responsive Design**: Mobile-first approach with smooth transitions
- **Interactive Elements**: Hover effects, smooth animations, loading states

## Files to Create/Modify

### 1. Templates Structure
**Create new template files**:

```
templates/services/
├── static_products/
│   ├── product_detail.html           # Main product page template
│   ├── partials/
│   │   ├── hero_section.html         # Product hero with CTA
│   │   ├── product_gallery.html     # Image gallery with lightbox
│   │   ├── options_panel.html       # Customization options
│   │   ├── pricing_calculator.html  # Real-time pricing widget
│   │   ├── product_tabs.html        # Specifications/FAQ/Samples tabs
│   │   ├── related_products.html    # Similar products carousel
│   │   └── design_tool_section.html # Design tool integration
│   ├── category_list.html            # Enhanced category page
│   └── product_search.html           # Search results page
```

### 2. Static Assets
**Create CSS and JavaScript files**:

```
static/
├── css/
│   ├── products/
│   │   ├── product-detail.css        # Product page specific styles
│   │   ├── pricing-calculator.css   # Pricing widget styles
│   │   ├── product-gallery.css      # Image gallery styles
│   │   └── responsive-products.css  # Mobile responsive styles
├── js/
│   ├── products/
│   │   ├── pricing-calculator.js    # Real-time pricing logic
│   │   ├── product-gallery.js       # Image gallery interactions
│   │   ├── product-options.js       # Option selection handling
│   │   └── design-tool-integration.js # Design tool launch
└── images/
    ├── placeholders/
    │   ├── product-hero-*.jpg        # Hero section placeholders
    │   ├── product-gallery-*.jpg     # Gallery placeholders
    │   └── product-samples-*.jpg     # Sample placeholders
```

### 3. Enhanced Views
**Update existing views in apps/services/views.py**:

```python
def static_product_detail(request, category_slug, product_slug):
    """Enhanced product detail view with all data for frontend"""
    # Fetch product with all related data
    # Prepare pricing options for JavaScript
    # Add breadcrumbs and SEO data
    # Include related products

def enhanced_category_view(request, slug):
    """Enhanced category view with filtering and sorting"""
    # Add product filtering options
    # Implement sorting (price, popularity, newest)
    # Add pagination with AJAX loading

def product_pricing_api_v2(request, product_id):
    """Enhanced pricing API with detailed breakdown"""
    # Return comprehensive pricing data
    # Include all modifiers and explanations
    # Add quantity tier information
```

### 4. Interactive Components
**Create JavaScript modules**:

#### Pricing Calculator (static/js/products/pricing-calculator.js)
```javascript
class PricingCalculator {
    constructor(productId, options) {
        this.productId = productId;
        this.currentSelections = {};
        this.init();
    }
    
    // Real-time price updates
    updatePrice() {
        // Fetch from API
        // Update UI with breakdown
        // Show quantity discounts
        // Handle rush orders
    }
    
    // Option change handlers
    handleOptionChange(option, value) {
        // Update selections
        // Trigger price recalculation
        // Update UI feedback
    }
}
```

#### Product Gallery (static/js/products/product-gallery.js)
```javascript
class ProductGallery {
    constructor(container) {
        this.container = container;
        this.currentImage = 0;
        this.init();
    }
    
    // Image navigation
    // Lightbox functionality
    // Zoom capabilities
    // Thumbnail interactions
}
```

### 5. Product Page Template (templates/services/static_products/product_detail.html)

**Main sections to implement**:

```html
<!-- Hero Section -->
<section class="hero-section bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
    <div class="container mx-auto px-4 py-16">
        <div class="grid lg:grid-cols-2 gap-12 items-center">
            <!-- Hero Content -->
            <div class="space-y-6">
                <div class="flex items-center space-x-2 text-sm text-gray-600">
                    <!-- Breadcrumbs -->
                </div>
                <h1 class="text-4xl lg:text-5xl font-bold text-gray-900">
                    {{ product.name }}
                </h1>
                <p class="text-xl text-gray-600">
                    {{ product.short_description }}
                </p>
                <div class="flex flex-wrap gap-4">
                    <!-- Key features badges -->
                </div>
                <div class="flex space-x-4">
                    <button class="btn-primary">Get Quote</button>
                    <button class="btn-secondary">View Samples</button>
                </div>
            </div>
            <!-- Hero Image -->
            <div class="relative">
                <!-- Product showcase image placeholder -->
            </div>
        </div>
    </div>
</section>

<!-- Main Product Section -->
<section class="py-16">
    <div class="container mx-auto px-4">
        <div class="grid lg:grid-cols-12 gap-8">
            <!-- Product Gallery (cols 1-4) -->
            <div class="lg:col-span-4">
                {% include 'services/static_products/partials/product_gallery.html' %}
            </div>
            
            <!-- Options Panel (cols 5-8) -->
            <div class="lg:col-span-5">
                {% include 'services/static_products/partials/options_panel.html' %}
                
                {% if product.design_tool_enabled %}
                    {% include 'services/static_products/partials/design_tool_section.html' %}
                {% endif %}
            </div>
            
            <!-- Pricing Calculator (cols 9-12) -->
            <div class="lg:col-span-3">
                {% include 'services/static_products/partials/pricing_calculator.html' %}
            </div>
        </div>
    </div>
</section>

<!-- Product Details Tabs -->
<section class="py-16 bg-gray-50">
    {% include 'services/static_products/partials/product_tabs.html' %}
</section>

<!-- Related Products -->
<section class="py-16">
    {% include 'services/static_products/partials/related_products.html' %}
</section>
```

### 6. Pricing Calculator Widget

**Real-time pricing display**:

```html
<!-- pricing_calculator.html -->
<div class="pricing-calculator bg-white rounded-lg shadow-lg p-6 sticky top-6">
    <h3 class="text-xl font-semibold mb-4">Price Calculator</h3>
    
    <!-- Price Breakdown -->
    <div class="space-y-3 mb-6">
        <div class="flex justify-between">
            <span>Base Price</span>
            <span id="base-price">₹{{ product.base_price }}</span>
        </div>
        <div class="flex justify-between">
            <span>Size Upgrade</span>
            <span id="size-cost">₹0</span>
        </div>
        <div class="flex justify-between">
            <span>Paper Upgrade</span>
            <span id="paper-cost">₹0</span>
        </div>
        <div class="flex justify-between">
            <span>Finish</span>
            <span id="finish-cost">₹0</span>
        </div>
        <div class="flex justify-between text-green-600">
            <span>Quantity Discount</span>
            <span id="quantity-discount">-₹0</span>
        </div>
        <hr>
        <div class="flex justify-between text-lg font-semibold">
            <span>Total</span>
            <span id="total-price">₹{{ product.base_price }}</span>
        </div>
        <div class="text-sm text-gray-600">
            <span id="price-per-unit">₹{{ product.base_price }}</span> {{ product.price_unit }}
        </div>
    </div>
    
    <!-- Quantity Tiers Display -->
    <div class="mb-6">
        <h4 class="font-medium mb-2">Quantity Discounts</h4>
        <div class="grid grid-cols-2 gap-2 text-sm">
            {% for tier in product.quantity_tiers %}
            <div class="bg-gray-50 p-2 rounded">
                <div class="font-medium">{{ tier.min_qty }}+ pieces</div>
                <div class="text-green-600">{{ tier.discount_percent }}% off</div>
            </div>
            {% endfor %}
        </div>
    </div>
    
    <!-- Action Buttons -->
    <div class="space-y-3">
        <button class="btn-primary w-full" onclick="addToCart()">
            Add to Cart
        </button>
        <button class="btn-secondary w-full" onclick="getQuote()">
            Get Custom Quote
        </button>
    </div>
    
    <!-- Additional Services -->
    <div class="mt-6 pt-6 border-t">
        <h4 class="font-medium mb-3">Additional Services</h4>
        <label class="flex items-center space-x-2 mb-2">
            <input type="checkbox" id="rush-order" onchange="updatePricing()">
            <span>Rush Order (+{{ product.rush_order_percentage }}%)</span>
        </label>
        {% if product.design_service_available %}
        <label class="flex items-center space-x-2">
            <input type="checkbox" id="design-service" onchange="updatePricing()">
            <span>Professional Design (+₹{{ product.design_service_price }})</span>
        </label>
        {% endif %}
    </div>
</div>
```

### 7. Options Panel

**Interactive product customization**:

```html
<!-- options_panel.html -->
<div class="options-panel space-y-8">
    <h2 class="text-2xl font-semibold">Customize Your {{ product.name }}</h2>
    
    <!-- Quantity Selection -->
    <div class="option-group">
        <label class="block text-sm font-medium text-gray-700 mb-3">
            Quantity
        </label>
        <div class="grid grid-cols-3 gap-3">
            {% for tier in product.quantity_tiers %}
            <button class="quantity-option p-3 border rounded-lg text-center hover:border-blue-500 transition-colors"
                    data-quantity="{{ tier.min_qty }}"
                    onclick="selectQuantity({{ tier.min_qty }})">
                <div class="font-semibold">{{ tier.min_qty }}+</div>
                {% if tier.discount_percent > 0 %}
                <div class="text-sm text-green-600">{{ tier.discount_percent }}% off</div>
                {% endif %}
            </button>
            {% endfor %}
        </div>
        <div class="mt-3">
            <input type="number" id="custom-quantity" class="form-input" placeholder="Custom quantity" min="1">
        </div>
    </div>
    
    <!-- Size Options -->
    {% if product.available_sizes %}
    <div class="option-group">
        <label class="block text-sm font-medium text-gray-700 mb-3">
            Size Options
        </label>
        <div class="grid grid-cols-1 gap-3">
            {% for size in product.available_sizes %}
            <button class="size-option p-4 border rounded-lg text-left hover:border-blue-500 transition-colors"
                    data-size="{{ size.name }}"
                    data-modifier="{{ size.price_modifier }}"
                    onclick="selectSize('{{ size.name }}', {{ size.price_modifier }})">
                <div class="flex justify-between items-center">
                    <span class="font-medium">{{ size.name }}</span>
                    {% if size.price_modifier != 0 %}
                    <span class="text-sm text-gray-600">
                        {% if size.price_modifier > 0 %}+₹{{ size.price_modifier }}{% else %}₹{{ size.price_modifier }}{% endif %}
                    </span>
                    {% endif %}
                </div>
            </button>
            {% endfor %}
        </div>
    </div>
    {% endif %}
    
    <!-- Paper Options -->
    {% if product.available_papers %}
    <div class="option-group">
        <label class="block text-sm font-medium text-gray-700 mb-3">
            Paper Quality
        </label>
        <select id="paper-select" class="form-select w-full" onchange="selectPaper()">
            <option value="">Select paper type</option>
            {% for paper in product.available_papers %}
            <option value="{{ paper.name }}" data-modifier="{{ paper.price_modifier }}">
                {{ paper.name }}
                {% if paper.price_modifier != 0 %}
                    ({% if paper.price_modifier > 0 %}+₹{{ paper.price_modifier }}{% else %}₹{{ paper.price_modifier }}{% endif %})
                {% endif %}
            </option>
            {% endfor %}
        </select>
    </div>
    {% endif %}
    
    <!-- Color Options -->
    {% if product.color_options %}
    <div class="option-group">
        <label class="block text-sm font-medium text-gray-700 mb-3">
            Color Options
        </label>
        <div class="space-y-2">
            {% for color in product.color_options %}
            <label class="flex items-center space-x-3">
                <input type="radio" name="color" value="{{ color.name }}" 
                       data-modifier="{{ color.price_modifier }}"
                       onchange="selectColor('{{ color.name }}', {{ color.price_modifier }})">
                <span>{{ color.name }}</span>
                {% if color.price_modifier != 0 %}
                <span class="text-sm text-gray-600">
                    ({% if color.price_modifier > 0 %}+₹{{ color.price_modifier }}{% else %}₹{{ color.price_modifier }}{% endif %})
                </span>
                {% endif %}
            </label>
            {% endfor %}
        </div>
    </div>
    {% endif %}
    
    <!-- Finish Options -->
    {% if product.available_finishes %}
    <div class="option-group">
        <label class="block text-sm font-medium text-gray-700 mb-3">
            Finish Options
        </label>
        <div class="grid grid-cols-1 gap-3">
            {% for finish in product.available_finishes %}
            <button class="finish-option p-3 border rounded-lg text-left hover:border-blue-500 transition-colors"
                    data-finish="{{ finish.name }}"
                    data-modifier="{{ finish.price_modifier }}"
                    onclick="selectFinish('{{ finish.name }}', {{ finish.price_modifier }})">
                <div class="flex justify-between items-center">
                    <span>{{ finish.name }}</span>
                    {% if finish.price_modifier != 0 %}
                    <span class="text-sm text-gray-600">
                        +₹{{ finish.price_modifier }}
                    </span>
                    {% endif %}
                </div>
            </button>
            {% endfor %}
        </div>
    </div>
    {% endif %}
</div>
```

## Implementation Steps

### Step 1: Template Structure
```bash
# Create template directories and base files
# Set up CSS and JavaScript structure
# Create placeholder images
```

### Step 2: CSS Styling
```bash
# Implement QinPrinting-inspired design
# Create responsive breakpoints
# Add smooth animations and transitions
# Style interactive components
```

### Step 3: JavaScript Functionality
```bash
# Build pricing calculator logic
# Implement option selection handlers
# Add gallery interactions
# Create design tool integration points
```

### Step 4: Integration Testing
```bash
# Test all 28 product pages
# Verify pricing calculations
# Check mobile responsiveness
# Test design tool integration
```

## Key Features to Implement

### 1. Real-Time Pricing Calculator
- **Live Updates**: Price changes as options are selected
- **Breakdown Display**: Show individual cost components
- **Quantity Tiers**: Visual representation of bulk discounts
- **Additional Services**: Rush order and design service toggles

### 2. Interactive Product Gallery
- **High-Quality Placeholders**: Professional product images
- **Thumbnail Navigation**: Easy image switching
- **Lightbox View**: Full-screen image viewing
- **Zoom Functionality**: Detailed product examination

### 3. Design Tool Integration
- **Conditional Display**: Only for design-enabled products
- **Canvas Preparation**: Set up design tool with correct dimensions
- **Template Gallery**: Show available design templates
- **Custom Upload**: Allow user file uploads

### 4. Mobile-First Responsive Design
- **Mobile Navigation**: Touch-friendly interfaces
- **Collapsible Sections**: Accordion-style options on mobile
- **Swipe Gestures**: Gallery navigation on touch devices
- **Performance Optimization**: Fast loading on all devices

### 5. SEO and Accessibility
- **Structured Data**: Product schema markup
- **Meta Tags**: Dynamic SEO tags per product
- **Alt Text**: Proper image descriptions
- **Keyboard Navigation**: Full accessibility support

## Product Page Examples to Create

### High-Priority Pages (Design Tool Enabled)
1. **Business Cards** (`/services/static/stationery/business-cards-static/`)
2. **Brochures** (`/services/static/marketing-materials/brochures-static/`)
3. **Flyers** (`/services/static/marketing-materials/flyers-static/`)
4. **Letterheads** (`/services/static/stationery/letterheads-static/`)
5. **Stickers** (`/services/static/stationery/stickers-static/`)

### Standard Pages (All 28 Products)
- Complete product pages for all categories
- Consistent design and functionality
- Pricing calculator integration
- Related products suggestions

## Success Criteria

✅ **Professional Design**: QinPrinting-inspired visual quality  
✅ **Real-Time Pricing**: Working calculator with live updates  
✅ **Mobile Responsive**: Perfect experience on all devices  
✅ **Fast Performance**: Sub-2 second page loads  
✅ **Interactive Elements**: Smooth animations and transitions  
✅ **Design Tool Ready**: Integration points for 9 products  
✅ **SEO Optimized**: Proper meta tags and structured data  
✅ **Accessibility**: Full keyboard and screen reader support

## Next Phase Preview

After Phase 2 completion:
- **Phase 3**: Complete design tool integration with canvas
- **Phase 4**: Shopping cart and checkout functionality  
- **Phase 5**: Order management and tracking system

## Notes for Claude Codebase

- **Use Tailwind CSS**: Consistent with existing project setup
- **Image Placeholders**: Create professional placeholder images
- **Progressive Enhancement**: Work without JavaScript, enhance with it
- **Performance First**: Optimize for speed and user experience
- **Component-Based**: Reusable template partials
- **Error Handling**: Graceful degradation for API failures
- **Loading States**: Show loading indicators during price calculations