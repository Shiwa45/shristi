# Phase 3: Design Tool Integration & Shopping Cart Implementation Plan for Claude Codebase

## Overview
Integrate the existing design tool with static products, implement shopping cart functionality, and add advanced user features like save/load designs, cart management, and quote generation. This phase transforms the website into a fully functional e-commerce platform.

## Project Context
- **Phase 1 Status**: ✅ COMPLETE - 28 static products with pricing API
- **Phase 2 Status**: ✅ COMPLETE - Professional product pages with pricing calculators
- **Current Goal**: Full design tool integration + shopping cart + user workflow
- **Existing Asset**: HTML-based design tool (Fabric.js canvas interface)

## Phase 3 Objectives

### 1. Design Tool Integration (9 Products)
- Convert existing HTML design tool to Django templates
- Integrate with static products that have `design_tool_enabled=True`
- Product-specific canvas dimensions and templates
- Save/load user designs to database
- Export designs for production

### 2. Shopping Cart System
- Add to cart from product pages
- Cart management (add, remove, update quantities)
- Persistent cart (logged-in users)
- Session-based cart (anonymous users)
- Cart summary with pricing calculations

### 3. User Design Management
- User accounts for design storage
- Design library with thumbnails
- Template gallery per product type
- Design versioning and history
- Share designs functionality

### 4. Quote & Order System
- Generate professional quotes from cart
- PDF quote generation
- Email quote to customer
- Convert quotes to orders
- Order tracking basics

## Files to Create/Modify

### 1. Design Tool Templates
**Convert existing HTML tool to Django templates**:

```
templates/design_tool/
├── design_editor.html              # Main design interface
├── partials/
│   ├── canvas_area.html           # Fabric.js canvas container
│   ├── toolbar.html               # Design tools toolbar
│   ├── layers_panel.html          # Layer management
│   ├── templates_gallery.html     # Product templates
│   ├── text_editor.html           # Text editing controls
│   ├── image_upload.html          # Image upload interface
│   ├── shapes_panel.html          # Shape tools
│   └── color_picker.html          # Color selection
├── design_gallery.html            # User's saved designs
└── templates_library.html         # Browse all templates
```

### 2. Shopping Cart Templates
**Create cart management interface**:

```
templates/cart/
├── cart_detail.html               # Full cart page
├── cart_sidebar.html              # Mini cart widget
├── partials/
│   ├── cart_item.html            # Individual cart item
│   ├── cart_summary.html         # Price summary
│   ├── shipping_calculator.html  # Shipping estimation
│   └── cart_actions.html         # Checkout buttons
└── ajax/
    ├── add_to_cart_response.html  # AJAX response templates
    └── cart_update_response.html
```

### 3. User Account Templates
**Enhanced user experience**:

```
templates/accounts/
├── dashboard.html                 # User dashboard
├── design_library.html           # Saved designs
├── order_history.html            # Past orders
└── profile_settings.html         # Account settings
```

### 4. Quote System Templates
**Professional quote generation**:

```
templates/quotes/
├── quote_detail.html             # Quote review page
├── quote_pdf.html               # PDF template
├── quote_email.html             # Email template
└── quote_list.html              # Quote history
```

### 5. Enhanced Models
**Extend existing models in apps/orders/models.py**:

```python
class UserDesign(models.Model):
    """User's saved designs"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    static_product = models.ForeignKey(StaticProduct, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    design_data = models.JSONField()  # Fabric.js canvas state
    thumbnail = models.ImageField(upload_to='design_thumbnails/')
    is_template = models.BooleanField(default=False)
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Cart(models.Model):
    """Shopping cart for users"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class CartItem(models.Model):
    """Items in shopping cart"""
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    static_product = models.ForeignKey(StaticProduct, on_delete=models.CASCADE)
    user_design = models.ForeignKey(UserDesign, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    selected_options = models.JSONField(default=dict)  # size, paper, finish, etc.
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    rush_order = models.BooleanField(default=False)
    design_service = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

class Quote(models.Model):
    """Generated quotes from cart"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    quote_number = models.CharField(max_length=20, unique=True)
    cart_snapshot = models.JSONField()  # Cart state at quote time
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, default='draft')
    valid_until = models.DateTimeField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class DesignTemplate(models.Model):
    """Product-specific design templates"""
    static_product = models.ForeignKey(StaticProduct, on_delete=models.CASCADE, related_name='design_templates')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    template_data = models.JSONField()  # Fabric.js template
    thumbnail = models.ImageField(upload_to='template_thumbnails/')
    category = models.CharField(max_length=100, blank=True)
    is_premium = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
```

### 6. Design Tool Views
**Create/update apps/design_tool/views.py**:

```python
class DesignEditorView(LoginRequiredMixin, DetailView):
    """Main design tool interface"""
    model = StaticProduct
    template_name = 'design_tool/design_editor.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_object()
        
        # Ensure product has design tool enabled
        if not product.design_tool_enabled:
            raise Http404("Design tool not available for this product")
        
        context.update({
            'canvas_width': product.canvas_width,
            'canvas_height': product.canvas_height,
            'design_templates': product.design_templates.filter(is_active=True),
            'user_designs': UserDesign.objects.filter(user=self.request.user, static_product=product),
            'product_options': {
                'sizes': product.available_sizes,
                'papers': product.available_papers,
                'colors': product.color_options,
            }
        })
        return context

def save_design(request):
    """AJAX endpoint to save user design"""
    if request.method == 'POST':
        design_data = json.loads(request.body)
        
        design = UserDesign.objects.create(
            user=request.user,
            static_product_id=design_data['product_id'],
            name=design_data['name'],
            design_data=design_data['canvas_state'],
            # Generate thumbnail from canvas
        )
        
        return JsonResponse({
            'success': True,
            'design_id': design.id,
            'thumbnail_url': design.thumbnail.url
        })

def load_design(request, design_id):
    """AJAX endpoint to load user design"""
    design = get_object_or_404(UserDesign, id=design_id, user=request.user)
    return JsonResponse({
        'success': True,
        'design_data': design.design_data,
        'product_id': design.static_product.id
    })

def design_to_cart(request):
    """Add design to cart"""
    if request.method == 'POST':
        data = json.loads(request.body)
        
        # Get or create cart
        cart = get_or_create_cart(request)
        
        # Create cart item with design
        cart_item = CartItem.objects.create(
            cart=cart,
            static_product_id=data['product_id'],
            user_design_id=data.get('design_id'),
            quantity=data['quantity'],
            selected_options=data['options'],
            unit_price=calculate_unit_price(data),
            rush_order=data.get('rush_order', False),
            design_service=data.get('design_service', False)
        )
        
        return JsonResponse({
            'success': True,
            'cart_item_id': cart_item.id,
            'cart_total': cart.get_total()
        })
```

### 7. Shopping Cart Views
**Create/update apps/orders/views.py**:

```python
def add_to_cart(request):
    """Add product to cart via AJAX"""
    if request.method == 'POST':
        data = json.loads(request.body)
        
        cart = get_or_create_cart(request)
        
        # Check if item already exists
        existing_item = CartItem.objects.filter(
            cart=cart,
            static_product_id=data['product_id'],
            selected_options=data['options']
        ).first()
        
        if existing_item:
            existing_item.quantity += data['quantity']
            existing_item.save()
        else:
            CartItem.objects.create(
                cart=cart,
                static_product_id=data['product_id'],
                quantity=data['quantity'],
                selected_options=data['options'],
                unit_price=data['unit_price']
            )
        
        return JsonResponse({
            'success': True,
            'cart_count': cart.items.count(),
            'cart_total': cart.get_total()
        })

class CartDetailView(TemplateView):
    """Full cart page with all items"""
    template_name = 'cart/cart_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart = get_or_create_cart(self.request)
        
        context.update({
            'cart': cart,
            'cart_items': cart.items.select_related('static_product'),
            'cart_total': cart.get_total(),
            'shipping_estimate': calculate_shipping(cart),
        })
        return context

def update_cart_item(request, item_id):
    """Update cart item quantity or options"""
    if request.method == 'POST':
        cart_item = get_object_or_404(CartItem, id=item_id)
        data = json.loads(request.body)
        
        cart_item.quantity = data['quantity']
        cart_item.save()
        
        return JsonResponse({
            'success': True,
            'item_total': cart_item.get_total(),
            'cart_total': cart_item.cart.get_total()
        })

def remove_cart_item(request, item_id):
    """Remove item from cart"""
    cart_item = get_object_or_404(CartItem, id=item_id)
    cart_item.delete()
    
    return JsonResponse({
        'success': True,
        'cart_total': cart_item.cart.get_total()
    })
```

### 8. Design Tool JavaScript Integration
**Update static/js/design_tool/design_editor.js**:

```javascript
class ShirstiDesignEditor {
    constructor(productId, canvasWidth, canvasHeight) {
        this.productId = productId;
        this.canvas = new fabric.Canvas('design-canvas', {
            width: canvasWidth,
            height: canvasHeight,
            backgroundColor: 'white'
        });
        this.currentDesign = null;
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.loadTemplates();
        this.setupAutoSave();
        this.setupToolbar();
    }
    
    // Template Management
    loadTemplate(templateId) {
        fetch(`/design-tool/template/${templateId}/`)
            .then(response => response.json())
            .then(data => {
                this.canvas.loadFromJSON(data.template_data, () => {
                    this.canvas.renderAll();
                    this.showNotification('Template loaded successfully');
                });
            });
    }
    
    // Design Saving/Loading
    saveDesign(name) {
        const designData = {
            product_id: this.productId,
            name: name,
            canvas_state: JSON.stringify(this.canvas.toJSON())
        };
        
        fetch('/design-tool/save/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(designData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.currentDesign = data.design_id;
                this.showNotification('Design saved successfully');
                this.updateDesignsList();
            }
        });
    }
    
    loadDesign(designId) {
        fetch(`/design-tool/load/${designId}/`)
            .then(response => response.json())
            .then(data => {
                this.canvas.loadFromJSON(data.design_data, () => {
                    this.canvas.renderAll();
                    this.currentDesign = designId;
                });
            });
    }
    
    // Export and Add to Cart
    addToCart() {
        // First save current design
        const designName = `Design_${Date.now()}`;
        this.saveDesign(designName);
        
        // Get selected product options
        const options = this.getSelectedOptions();
        const quantity = parseInt(document.getElementById('quantity').value) || 1;
        
        const cartData = {
            product_id: this.productId,
            design_id: this.currentDesign,
            quantity: quantity,
            options: options,
            unit_price: this.calculatePrice(options, quantity)
        };
        
        fetch('/cart/add-design/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(cartData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.showNotification('Added to cart successfully');
                this.updateCartCount();
                // Optionally redirect to cart
                if (confirm('Design added to cart! View cart now?')) {
                    window.location.href = '/cart/';
                }
            }
        });
    }
    
    // Text Tools
    addText(text = 'Click to edit') {
        const textObj = new fabric.Text(text, {
            left: 100,
            top: 100,
            fontFamily: 'Arial',
            fontSize: 20,
            fill: '#000000'
        });
        
        this.canvas.add(textObj);
        this.canvas.setActiveObject(textObj);
    }
    
    // Image Upload
    uploadImage(file) {
        const formData = new FormData();
        formData.append('image', file);
        formData.append('product_id', this.productId);
        
        fetch('/design-tool/upload-image/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                fabric.Image.fromURL(data.image_url, (img) => {
                    img.scale(0.5);
                    this.canvas.add(img);
                });
            }
        });
    }
    
    // Shape Tools
    addRectangle() {
        const rect = new fabric.Rect({
            left: 100,
            top: 100,
            width: 100,
            height: 100,
            fill: '#ff0000',
            stroke: '#000000',
            strokeWidth: 2
        });
        
        this.canvas.add(rect);
    }
    
    addCircle() {
        const circle = new fabric.Circle({
            left: 100,
            top: 100,
            radius: 50,
            fill: '#00ff00',
            stroke: '#000000',
            strokeWidth: 2
        });
        
        this.canvas.add(circle);
    }
    
    // Layer Management
    moveLayerUp() {
        const activeObj = this.canvas.getActiveObject();
        if (activeObj) {
            this.canvas.bringForward(activeObj);
            this.updateLayersList();
        }
    }
    
    moveLayerDown() {
        const activeObj = this.canvas.getActiveObject();
        if (activeObj) {
            this.canvas.sendBackwards(activeObj);
            this.updateLayersList();
        }
    }
    
    deleteSelected() {
        const activeObj = this.canvas.getActiveObject();
        if (activeObj) {
            this.canvas.remove(activeObj);
            this.updateLayersList();
        }
    }
    
    // Utility Functions
    getSelectedOptions() {
        return {
            size: document.querySelector('input[name="size"]:checked')?.value,
            paper: document.getElementById('paper-select').value,
            finish: document.querySelector('input[name="finish"]:checked')?.value,
            color: document.querySelector('input[name="color"]:checked')?.value
        };
    }
    
    calculatePrice(options, quantity) {
        // Use the existing pricing API
        const params = new URLSearchParams({
            quantity: quantity,
            ...options
        });
        
        return fetch(`/services/api/static-pricing/${this.productId}/?${params}`)
            .then(response => response.json())
            .then(data => data.pricing.total_price);
    }
    
    setupAutoSave() {
        setInterval(() => {
            if (this.currentDesign) {
                this.autoSave();
            }
        }, 60000); // Auto-save every minute
    }
    
    autoSave() {
        const designData = {
            design_id: this.currentDesign,
            canvas_state: JSON.stringify(this.canvas.toJSON())
        };
        
        fetch('/design-tool/auto-save/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(designData)
        });
    }
}

// Initialize design editor when page loads
document.addEventListener('DOMContentLoaded', function() {
    if (window.designEditorConfig) {
        window.designEditor = new ShirstiDesignEditor(
            window.designEditorConfig.productId,
            window.designEditorConfig.canvasWidth,
            window.designEditorConfig.canvasHeight
        );
    }
});
```

### 9. Shopping Cart JavaScript
**Create static/js/cart/cart_manager.js**:

```javascript
class CartManager {
    constructor() {
        this.init();
    }
    
    init() {
        this.updateCartCount();
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        // Add to cart buttons
        document.querySelectorAll('.add-to-cart-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                this.addToCart(btn.dataset.productId);
            });
        });
        
        // Quantity update buttons
        document.querySelectorAll('.quantity-update').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                this.updateQuantity(btn.dataset.itemId, btn.dataset.action);
            });
        });
        
        // Remove item buttons
        document.querySelectorAll('.remove-item').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                this.removeItem(btn.dataset.itemId);
            });
        });
    }
    
    addToCart(productId) {
        const options = this.getProductOptions();
        const quantity = parseInt(document.getElementById('quantity').value) || 1;
        
        const data = {
            product_id: productId,
            quantity: quantity,
            options: options,
            unit_price: this.getCurrentPrice()
        };
        
        fetch('/cart/add/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.showNotification('Added to cart!');
                this.updateCartCount();
                this.showMiniCart();
            }
        })
        .catch(error => {
            console.error('Error adding to cart:', error);
            this.showNotification('Error adding to cart', 'error');
        });
    }
    
    updateQuantity(itemId, action) {
        const currentQty = parseInt(document.querySelector(`[data-item="${itemId}"] .quantity-display`).textContent);
        let newQty = currentQty;
        
        if (action === 'increase') {
            newQty = currentQty + 1;
        } else if (action === 'decrease' && currentQty > 1) {
            newQty = currentQty - 1;
        }
        
        if (newQty !== currentQty) {
            fetch(`/cart/update/${itemId}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({ quantity: newQty })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.updateCartDisplay(itemId, data);
                }
            });
        }
    }
    
    removeItem(itemId) {
        if (confirm('Remove this item from cart?')) {
            fetch(`/cart/remove/${itemId}/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    document.querySelector(`[data-item="${itemId}"]`).remove();
                    this.updateCartTotals(data.cart_total);
                    this.updateCartCount();
                }
            });
        }
    }
    
    updateCartCount() {
        fetch('/cart/count/')
            .then(response => response.json())
            .then(data => {
                document.querySelectorAll('.cart-count').forEach(el => {
                    el.textContent = data.count;
                    el.style.display = data.count > 0 ? 'block' : 'none';
                });
            });
    }
    
    showMiniCart() {
        // Show mini cart widget
        const miniCart = document.getElementById('mini-cart');
        if (miniCart) {
            miniCart.classList.add('show');
            setTimeout(() => {
                miniCart.classList.remove('show');
            }, 3000);
        }
    }
    
    getProductOptions() {
        return {
            size: document.querySelector('input[name="size"]:checked')?.value,
            paper: document.getElementById('paper-select')?.value,
            finish: document.querySelector('input[name="finish"]:checked')?.value,
            color: document.querySelector('input[name="color"]:checked')?.value,
            binding: document.querySelector('input[name="binding"]:checked')?.value
        };
    }
    
    getCurrentPrice() {
        return parseFloat(document.getElementById('total-price').textContent.replace('₹', '').replace(',', ''));
    }
    
    showNotification(message, type = 'success') {
        // Create and show notification
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.classList.add('show');
        }, 100);
        
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
}

// Initialize cart manager
document.addEventListener('DOMContentLoaded', function() {
    window.cartManager = new CartManager();
});
```

### 10. Quote Generation System
**Create apps/quotes/views.py**:

```python
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
import uuid
from datetime import datetime, timedelta

@login_required
def generate_quote(request):
    """Generate quote from current cart"""
    cart = get_or_create_cart(request)
    
    if not cart.items.exists():
        messages.error(request, 'Your cart is empty')
        return redirect('cart:detail')
    
    # Create quote
    quote = Quote.objects.create(
        user=request.user,
        quote_number=f"QT{datetime.now().strftime('%Y%m%d')}{str(uuid.uuid4())[:6].upper()}",
        cart_snapshot=serialize_cart(cart),
        total_amount=cart.get_total(),
        valid_until=datetime.now() + timedelta(days=30)
    )
    
    return redirect('quotes:detail', quote_id=quote.id)

@login_required
def quote_detail(request, quote_id):
    """Display quote details"""
    quote = get_object_or_404(Quote, id=quote_id, user=request.user)
    
    context = {
        'quote': quote,
        'cart_items': deserialize_cart_items(quote.cart_snapshot),
        'company_info': get_company_info(),
    }
    
    return render(request, 'quotes/quote_detail.html', context)

@login_required
def quote_pdf(request, quote_id):
    """Generate PDF quote"""
    quote = get_object_or_404(Quote, id=quote_id, user=request.user)
    
    html_string = render_to_string('quotes/quote_pdf.html', {
        'quote': quote,
        'cart_items': deserialize_cart_items(quote.cart_snapshot),
        'company_info': get_company_info(),
    })
    
    html = HTML(string=html_string)
    pdf = html.write_pdf()
    
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Quote_{quote.quote_number}.pdf"'
    return response

@login_required
def email_quote(request, quote_id):
    """Email quote to customer"""
    quote = get_object_or_404(Quote, id=quote_id, user=request.user)
    
    # Generate PDF
    pdf_content = generate_quote_pdf(quote)
    
    # Send email with PDF attachment
    send_quote_email(quote, pdf_content)
    
    return JsonResponse({
        'success': True,
        'message': 'Quote emailed successfully'
    })
```

## Implementation Steps

### Step 1: Design Tool Integration
```bash
# Convert existing HTML design tool to Django templates
# Set up Fabric.js canvas with product-specific dimensions
# Implement save/load functionality for user designs
# Create template gallery for each product type
```

### Step 2: Shopping Cart System
```bash
# Create cart models and migrations
# Implement add to cart functionality
# Build cart management interface
# Add AJAX cart updates
```

### Step 3: User Design Management
```bash
# Create user design library
# Implement design versioning
# Add template management system
# Create design sharing functionality
```

### Step 4: Quote System
```bash
# Implement quote generation from cart
# Create PDF quote templates
# Add email quote functionality
# Build quote management interface
```

### Step 5: Integration & Testing
```bash
# Test complete workflow: design → cart → quote
# Verify all 9 design-enabled products work
# Test mobile responsiveness
# Performance optimization
```

## Key Features to Implement

### 1. Design Tool Features
- **Product-Specific Canvas**: Correct dimensions for each product type
- **Template Gallery**: Pre-made designs for each product
- **Text Tools**: Font selection, sizing, colors, effects
- **Image Upload**: User image upload with resizing
- **Shape Tools**: Rectangles, circles, polygons
- **Layer Management**: Object ordering and grouping
- **Auto-Save**: Automatic design saving every minute
- **Export Ready**: High-resolution export for production

### 2. Shopping Cart Features
- **Persistent Cart**: Saved cart for logged-in users
- **Session Cart**: Anonymous user cart management
- **Real-Time Updates**: AJAX quantity and option changes
- **Price Calculations**: Live pricing with all modifiers
- **Mini Cart Widget**: Slide-out cart summary
- **Checkout Preparation**: Ready for payment integration

### 3. User Experience Features
- **Design Library**: Browse and organize saved designs
- **Template Browse**: Explore all available templates
- **Quick Actions**: Duplicate, edit, share designs
- **Mobile Optimization**: Touch-friendly design tools
- **Keyboard Shortcuts**: Power user shortcuts
- **Undo/Redo**: Design history navigation

### 4. Quote & Order Features
- **Professional Quotes**: Branded PDF quotes
- **Email Integration**: Automated quote delivery
- **Quote Management**: Track quote status and history
- **Order Conversion**: Convert quotes to orders
- **Customer Communication**: Quote notes and messages

## Design Tool Product Configuration

### Canvas Dimensions (from Phase 1)
- **Business Cards**: 1050x600px (3.5"x2" at 300 DPI)
- **Brochures**: 2550x3300px (8.5"x11" tri-fold at 300 DPI)
- **Flyers**: 2550x3300px (A4 at 300 DPI)
- **Letterheads**: 2550x3300px (A4 at 300 DPI)
- **Bill Books**: 1275x1755px (A5 at 300 DPI)
- **Stickers**: 600x600px (2"x2" at 300 DPI)
- **Catalogues**: 2550x3300px (A4 at 300 DPI)
- **Danglers**: 900x1500px (3"x5" at 300 DPI)
- **Standees**: 1800x5400px (6"x18" at 300 DPI)

### Template Categories per Product
```json
{
    "business_cards": ["Corporate", "Creative", "Minimalist", "Modern", "Classic"],
    "brochures": ["Tri-fold Corporate", "Bi-fold Marketing", "Product Showcase", "Service Brochures"],
    "flyers": ["Event", "Promotion", "Sale", "Announcement", "Product Launch"],
    "letterheads": ["Corporate", "Professional", "Creative", "Medical", "Legal"],
    "stickers": ["Round", "Square", "Custom Shape", "Logo", "Promotional"],
    "bill_books": ["Standard Invoice", "Service Bill", "Product Bill", "Tax Invoice"],
    "catalogues": ["Product Catalog", "Service Catalog", "Corporate Brochure"],
    "danglers": ["Sale Tags", "Product Tags", "Promotional Tags"],
    "standees": ["Event Standee", "Product Display", "Promotional Banner"]
}
```

## URL Structure

### Design Tool URLs
```python
# apps/design_tool/urls.py
urlpatterns = [
    path('editor/<slug:category_slug>/<slug:product_slug>/', views.DesignEditorView.as_view(), name='editor'),
    path('save/', views.save_design, name='save_design'),
    path('load/<int:design_id>/', views.load_design, name='load_design'),
    path('template/<int:template_id>/', views.load_template, name='load_template'),
    path('upload-image/', views.upload_image, name='upload_image'),
    path('auto-save/', views.auto_save_design, name='auto_save'),
    path('export/<int:design_id>/', views.export_design, name='export_design'),
    path('library/', views.DesignLibraryView.as_view(), name='library'),
    path('templates/', views.TemplateLibraryView.as_view(), name='templates'),
]
```

### Cart URLs
```python
# apps/orders/urls.py
urlpatterns = [
    path('cart/', views.CartDetailView.as_view(), name='cart_detail'),
    path('cart/add/', views.add_to_cart, name='add_to_cart'),
    path('cart/add-design/', views.add_design_to_cart, name='add_design_to_cart'),
    path('cart/update/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('cart/remove/<int:item_id>/', views.remove_cart_item, name='remove_cart_item'),
    path('cart/count/', views.cart_count, name='cart_count'),
    path('cart/clear/', views.clear_cart, name='clear_cart'),
]
```

### Quote URLs
```python
# apps/quotes/urls.py
urlpatterns = [
    path('generate/', views.generate_quote, name='generate_quote'),
    path('<int:quote_id>/', views.quote_detail, name='quote_detail'),
    path('<int:quote_id>/pdf/', views.quote_pdf, name='quote_pdf'),
    path('<int:quote_id>/email/', views.email_quote, name='email_quote'),
    path('list/', views.QuoteListView.as_view(), name='quote_list'),
]
```

## Database Migration Strategy

### Migration Files to Create
```python
# apps/orders/migrations/0003_add_cart_system.py
# - Add Cart, CartItem models
# - Update existing Order model relationships

# apps/design_tool/migrations/0001_initial.py  
# - Add UserDesign, DesignTemplate models
# - Add design storage fields

# apps/quotes/migrations/0001_initial.py
# - Add Quote model
# - Add quote generation fields
```

## Template Examples

### Design Editor Main Template
```html
<!-- templates/design_tool/design_editor.html -->
{% extends 'base.html' %}
{% load static %}

{% block title %}Design {{ product.name }} - Shirsti Printing{% endblock %}

{% block extra_css %}
<link rel="stylesheet" href="{% static 'css/design_tool/editor.css' %}">
<link rel="stylesheet" href="{% static 'css/design_tool/fabric-customizations.css' %}">
{% endblock %}

{% block content %}
<div class="design-editor-container">
    <!-- Header with product info and actions -->
    <header class="editor-header bg-white shadow-sm border-b">
        <div class="container mx-auto px-4 py-3">
            <div class="flex justify-between items-center">
                <div class="flex items-center space-x-4">
                    <h1 class="text-xl font-semibold">Design {{ product.name }}</h1>
                    <span class="text-gray-500">{{ product.canvas_width }}x{{ product.canvas_height }}px</span>
                </div>
                <div class="flex items-center space-x-3">
                    <button id="save-design-btn" class="btn-secondary">Save Design</button>
                    <button id="add-to-cart-btn" class="btn-primary">Add to Cart</button>
                </div>
            </div>
        </div>
    </header>

    <!-- Main editor layout -->
    <div class="editor-main flex h-screen">
        <!-- Left Sidebar - Tools & Templates -->
        <aside class="editor-sidebar w-80 bg-gray-50 border-r overflow-y-auto">
            <div class="p-4 space-y-6">
                <!-- Templates Tab -->
                <div class="templates-section">
                    <h3 class="font-semibold mb-3">Templates</h3>
                    <div class="grid grid-cols-2 gap-3">
                        {% for template in design_templates %}
                        <div class="template-item cursor-pointer border rounded-lg overflow-hidden hover:border-blue-500"
                             onclick="loadTemplate({{ template.id }})">
                            <img src="{{ template.thumbnail.url }}" alt="{{ template.name }}" class="w-full h-20 object-cover">
                            <div class="p-2">
                                <div class="text-sm font-medium">{{ template.name }}</div>
                                {% if template.is_premium %}
                                <span class="text-xs text-yellow-600">Premium</span>
                                {% endif %}
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                </div>

                <!-- Tools Section -->
                <div class="tools-section">
                    <h3 class="font-semibold mb-3">Tools</h3>
                    <div class="grid grid-cols-2 gap-2">
                        <button class="tool-btn" onclick="designEditor.addText()">
                            <i class="fas fa-font"></i> Text
                        </button>
                        <button class="tool-btn" onclick="designEditor.addRectangle()">
                            <i class="fas fa-square"></i> Rectangle
                        </button>
                        <button class="tool-btn" onclick="designEditor.addCircle()">
                            <i class="fas fa-circle"></i> Circle
                        </button>
                        <button class="tool-btn" onclick="document.getElementById('image-upload').click()">
                            <i class="fas fa-image"></i> Upload
                        </button>
                    </div>
                </div>

                <!-- Saved Designs -->
                <div class="saved-designs-section">
                    <h3 class="font-semibold mb-3">Your Designs</h3>
                    <div class="space-y-2" id="saved-designs-list">
                        {% for design in user_designs %}
                        <div class="design-item flex items-center space-x-3 p-2 border rounded cursor-pointer hover:bg-gray-100"
                             onclick="loadDesign({{ design.id }})">
                            <img src="{{ design.thumbnail.url }}" alt="{{ design.name }}" class="w-12 h-12 object-cover rounded">
                            <div class="flex-1 min-w-0">
                                <div class="text-sm font-medium truncate">{{ design.name }}</div>
                                <div class="text-xs text-gray-500">{{ design.updated_at|date:"M d, Y" }}</div>
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                </div>
            </div>
        </aside>

        <!-- Center - Canvas Area -->
        <main class="editor-canvas-area flex-1 flex flex-col">
            <!-- Canvas Toolbar -->
            <div class="canvas-toolbar bg-white border-b p-3">
                <div class="flex items-center justify-between">
                    <div class="flex items-center space-x-3">
                        <!-- Zoom Controls -->
                        <div class="flex items-center space-x-1">
                            <button onclick="designEditor.zoomOut()" class="p-1 text-gray-600 hover:text-gray-900">
                                <i class="fas fa-search-minus"></i>
                            </button>
                            <span id="zoom-level" class="text-sm px-2">100%</span>
                            <button onclick="designEditor.zoomIn()" class="p-1 text-gray-600 hover:text-gray-900">
                                <i class="fas fa-search-plus"></i>
                            </button>
                        </div>

                        <!-- Alignment Tools -->
                        <div class="flex items-center space-x-1 border-l pl-3">
                            <button onclick="designEditor.alignLeft()" class="p-1 text-gray-600 hover:text-gray-900" title="Align Left">
                                <i class="fas fa-align-left"></i>
                            </button>
                            <button onclick="designEditor.alignCenter()" class="p-1 text-gray-600 hover:text-gray-900" title="Align Center">
                                <i class="fas fa-align-center"></i>
                            </button>
                            <button onclick="designEditor.alignRight()" class="p-1 text-gray-600 hover:text-gray-900" title="Align Right">
                                <i class="fas fa-align-right"></i>
                            </button>
                        </div>
                    </div>

                    <div class="flex items-center space-x-3">
                        <!-- Undo/Redo -->
                        <button onclick="designEditor.undo()" class="p-1 text-gray-600 hover:text-gray-900" title="Undo">
                            <i class="fas fa-undo"></i>
                        </button>
                        <button onclick="designEditor.redo()" class="p-1 text-gray-600 hover:text-gray-900" title="Redo">
                            <i class="fas fa-redo"></i>
                        </button>

                        <!-- Delete -->
                        <button onclick="designEditor.deleteSelected()" class="p-1 text-red-600 hover:text-red-900" title="Delete">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            </div>

            <!-- Canvas Container -->
            <div class="canvas-container flex-1 bg-gray-100 p-8 overflow-auto">
                <div class="canvas-wrapper mx-auto" style="width: {{ product.canvas_width }}px;">
                    <canvas id="design-canvas"></canvas>
                </div>
            </div>
        </main>

        <!-- Right Sidebar - Properties & Layers -->
        <aside class="editor-properties w-80 bg-gray-50 border-l overflow-y-auto">
            <div class="p-4 space-y-6">
                <!-- Object Properties -->
                <div class="properties-section">
                    <h3 class="font-semibold mb-3">Properties</h3>
                    <div id="object-properties" class="space-y-3">
                        <!-- Dynamic properties based on selected object -->
                        <div class="text-sm text-gray-500">Select an object to edit properties</div>
                    </div>
                </div>

                <!-- Layers Panel -->
                <div class="layers-section">
                    <h3 class="font-semibold mb-3">Layers</h3>
                    <div id="layers-list" class="space-y-1">
                        <!-- Dynamic layer list -->
                    </div>
                </div>

                <!-- Product Options -->
                <div class="product-options-section">
                    <h3 class="font-semibold mb-3">Product Options</h3>
                    <div class="space-y-4">
                        <!-- Size Selection -->
                        {% if product.available_sizes %}
                        <div>
                            <label class="block text-sm font-medium mb-2">Size</label>
                            <select id="size-select" class="form-select w-full text-sm">
                                {% for size in product.available_sizes %}
                                <option value="{{ size.name }}" data-modifier="{{ size.price_modifier }}">
                                    {{ size.name }}
                                    {% if size.price_modifier != 0 %}(+₹{{ size.price_modifier }}){% endif %}
                                </option>
                                {% endfor %}
                            </select>
                        </div>
                        {% endif %}

                        <!-- Paper Selection -->
                        {% if product.available_papers %}
                        <div>
                            <label class="block text-sm font-medium mb-2">Paper</label>
                            <select id="paper-select" class="form-select w-full text-sm">
                                {% for paper in product.available_papers %}
                                <option value="{{ paper.name }}" data-modifier="{{ paper.price_modifier }}">
                                    {{ paper.name }}
                                    {% if paper.price_modifier != 0 %}(+₹{{ paper.price_modifier }}){% endif %}
                                </option>
                                {% endfor %}
                            </select>
                        </div>
                        {% endif %}

                        <!-- Quantity -->
                        <div>
                            <label class="block text-sm font-medium mb-2">Quantity</label>
                            <input type="number" id="quantity" value="100" min="1" class="form-input w-full text-sm">
                        </div>

                        <!-- Price Display -->
                        <div class="bg-white p-3 rounded border">
                            <div class="text-sm font-medium mb-1">Estimated Price</div>
                            <div id="estimated-price" class="text-lg font-bold text-blue-600">₹{{ product.base_price }}</div>
                            <div class="text-xs text-gray-500">Includes design and printing</div>
                        </div>
                    </div>
                </div>
            </div>
        </aside>
    </div>
</div>

<!-- Hidden file input for image upload -->
<input type="file" id="image-upload" accept="image/*" style="display: none;" onchange="designEditor.uploadImage(this.files[0])">

<!-- Design Save Modal -->
<div id="save-modal" class="modal hidden">
    <div class="modal-content">
        <h3 class="text-lg font-semibold mb-4">Save Design</h3>
        <input type="text" id="design-name" placeholder="Enter design name" class="form-input w-full mb-4">
        <div class="flex justify-end space-x-3">
            <button onclick="closeSaveModal()" class="btn-secondary">Cancel</button>
            <button onclick="saveDesignWithName()" class="btn-primary">Save</button>
        </div>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script src="{% static 'js/fabric.min.js' %}"></script>
<script src="{% static 'js/design_tool/design_editor.js' %}"></script>
<script>
// Initialize design editor with product configuration
window.designEditorConfig = {
    productId: {{ product.id }},
    canvasWidth: {{ product.canvas_width }},
    canvasHeight: {{ product.canvas_height }},
    basePrice: {{ product.base_price }},
    pricingApiUrl: '{% url "services:static_pricing_api" product.id %}'
};
</script>
{% endblock %}
```

### Shopping Cart Detail Template
```html
<!-- templates/cart/cart_detail.html -->
{% extends 'base.html' %}
{% load static %}

{% block title %}Shopping Cart - Shirsti Printing{% endblock %}

{% block content %}
<div class="cart-page py-8">
    <div class="container mx-auto px-4">
        <h1 class="text-3xl font-bold mb-8">Shopping Cart</h1>

        {% if cart.items.exists %}
        <div class="grid lg:grid-cols-3 gap-8">
            <!-- Cart Items -->
            <div class="lg:col-span-2">
                <div class="space-y-4">
                    {% for item in cart.items.all %}
                    <div class="cart-item bg-white rounded-lg shadow-sm border p-6" data-item="{{ item.id }}">
                        <div class="flex items-start space-x-4">
                            <!-- Product Image -->
                            <div class="flex-shrink-0">
                                <img src="{{ item.static_product.featured_image.url }}" 
                                     alt="{{ item.static_product.name }}"
                                     class="w-20 h-20 object-cover rounded">
                            </div>

                            <!-- Item Details -->
                            <div class="flex-1 min-w-0">
                                <h3 class="text-lg font-semibold">{{ item.static_product.name }}</h3>
                                <p class="text-gray-600">{{ item.static_product.category.name }}</p>

                                <!-- Selected Options -->
                                <div class="mt-2 text-sm text-gray-500">
                                    {% for key, value in item.selected_options.items %}
                                        {% if value %}
                                        <span class="inline-block mr-3">{{ key|title }}: {{ value }}</span>
                                        {% endif %}
                                    {% endfor %}
                                </div>

                                {% if item.user_design %}
                                <div class="mt-2">
                                    <span class="inline-flex items-center px-2 py-1 rounded-full text-xs bg-blue-100 text-blue-800">
                                        <i class="fas fa-palette mr-1"></i> Custom Design
                                    </span>
                                </div>
                                {% endif %}

                                <!-- Quantity Controls -->
                                <div class="flex items-center mt-4 space-x-3">
                                    <label class="text-sm font-medium">Quantity:</label>
                                    <div class="flex items-center border rounded">
                                        <button class="quantity-update px-3 py-1 hover:bg-gray-100" 
                                                data-item-id="{{ item.id }}" data-action="decrease">-</button>
                                        <span class="quantity-display px-3 py-1 min-w-[3rem] text-center">{{ item.quantity }}</span>
                                        <button class="quantity-update px-3 py-1 hover:bg-gray-100" 
                                                data-item-id="{{ item.id }}" data-action="increase">+</button>
                                    </div>
                                </div>
                            </div>

                            <!-- Price & Actions -->
                            <div class="flex-shrink-0 text-right">
                                <div class="text-lg font-semibold">₹<span class="item-total">{{ item.get_total }}</span></div>
                                <div class="text-sm text-gray-500">₹{{ item.unit_price }} each</div>
                                
                                <button class="remove-item mt-3 text-red-600 hover:text-red-800 text-sm"
                                        data-item-id="{{ item.id }}">
                                    <i class="fas fa-trash mr-1"></i> Remove
                                </button>
                            </div>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>

            <!-- Cart Summary -->
            <div class="lg:col-span-1">
                <div class="bg-white rounded-lg shadow-sm border p-6 sticky top-6">
                    <h3 class="text-xl font-semibold mb-4">Order Summary</h3>
                    
                    <div class="space-y-3 mb-6">
                        <div class="flex justify-between">
                            <span>Subtotal</span>
                            <span>₹<span id="cart-subtotal">{{ cart.get_subtotal }}</span></span>
                        </div>
                        <div class="flex justify-between">
                            <span>Estimated Shipping</span>
                            <span>₹<span id="shipping-cost">{{ shipping_estimate }}</span></span>
                        </div>
                        <div class="flex justify-between">
                            <span>Tax (18% GST)</span>
                            <span>₹<span id="tax-amount">{{ cart.get_tax }}</span></span>
                        </div>
                        <hr>
                        <div class="flex justify-between text-lg font-semibold">
                            <span>Total</span>
                            <span>₹<span id="cart-total">{{ cart.get_total }}</span></span>
                        </div>
                    </div>

                    <!-- Action Buttons -->
                    <div class="space-y-3">
                        <a href="{% url 'quotes:generate_quote' %}" class="btn-primary w-full text-center block">
                            Get Quote
                        </a>
                        <button class="btn-secondary w-full" onclick="proceedToCheckout()">
                            Proceed to Checkout
                        </button>
                    </div>

                    <!-- Additional Info -->
                    <div class="mt-6 text-sm text-gray-600">
                        <p class="mb-2"><i class="fas fa-truck mr-2"></i> Free shipping on orders over ₹2,000</p>
                        <p class="mb-2"><i class="fas fa-clock mr-2"></i> Standard delivery: 5-7 business days</p>
                        <p><i class="fas fa-shield-alt mr-2"></i> 100% quality guarantee</p>
                    </div>
                </div>
            </div>
        </div>

        {% else %}
        <!-- Empty Cart -->
        <div class="text-center py-16">
            <div class="max-w-md mx-auto">
                <i class="fas fa-shopping-cart text-6xl text-gray-300 mb-4"></i>
                <h2 class="text-2xl font-semibold text-gray-600 mb-2">Your cart is empty</h2>
                <p class="text-gray-500 mb-6">Add some products to get started with your order.</p>
                <a href="{% url 'services:home' %}" class="btn-primary">Browse Products</a>
            </div>
        </div>
        {% endif %}
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script src="{% static 'js/cart/cart_manager.js' %}"></script>
{% endblock %}
```

## Success Criteria

✅ **Design Tool Integration**: 9 products with working design editor  
✅ **Shopping Cart System**: Full cart management with AJAX updates  
✅ **User Design Management**: Save, load, organize designs  
✅ **Template Library**: Product-specific design templates  
✅ **Quote Generation**: Professional PDF quotes from cart  
✅ **Mobile Optimization**: Touch-friendly design tools  
✅ **Performance**: Fast canvas rendering and interactions  
✅ **User Experience**: Intuitive workflow from design to quote

## Testing Checklist

### Design Tool Testing
- [ ] Canvas loads with correct dimensions for each product
- [ ] Templates load and apply correctly
- [ ] Text tools work (add, edit, format)
- [ ] Image upload and manipulation
- [ ] Shape tools function properly
- [ ] Save/load designs works
- [ ] Auto-save functionality
- [ ] Export for production ready

### Cart System Testing
- [ ] Add to cart from product pages
- [ ] Add design to cart from editor
- [ ] Update quantities via AJAX
- [ ] Remove items from cart
- [ ] Cart persistence for logged-in users
- [ ] Session cart for anonymous users
- [ ] Price calculations accurate
- [ ] Mobile cart functionality

### Quote System Testing
- [ ] Generate quote from cart
- [ ] PDF quote generation
- [ ] Email quote delivery
- [ ] Quote management interface
- [ ] Quote to order conversion

## Performance Considerations

### Frontend Optimization
- **Fabric.js Optimization**: Limit canvas object count, use object caching
- **Image Optimization**: Compress uploaded images, use WebP format
- **AJAX Efficiency**: Debounce API calls, use loading states
- **Mobile Performance**: Touch gestures, reduced canvas complexity

### Backend Optimization
- **Database Queries**: Use select_related, prefetch_related for cart items
- **File Storage**: Optimize image storage and delivery
- **Caching**: Cache design templates and product options
- **API Response**: Minimize JSON payload size

## Next Phase Preview

After Phase 3 completion:
- **Phase 4**: Payment integration and order processing
- **Phase 5**: Order fulfillment and tracking system
- **Phase 6**: Analytics and reporting dashboard

## Notes for Claude Codebase

- **Fabric.js Integration**: Use the existing design tool HTML as reference
- **Mobile Considerations**: Ensure touch-friendly design tools
- **File Management**: Proper handling of design files and images
- **Security**: Validate all user inputs and design data
- **Performance**: Optimize for large canvas operations
- **Error Handling**: Graceful handling of design tool errors
- **User Experience**: Smooth transitions between design and cart
- **Testing**: Comprehensive testing of all 9 design-enabled products