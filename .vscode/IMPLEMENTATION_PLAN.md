# Phase 1: Static Product Models Implementation Plan for Claude Codebase

## Overview
Implement static product models alongside existing dynamic system to avoid breaking dependencies. This creates 28 individual product pages with predefined pricing tiers based on Creative Print Arts structure.

## Project Context
- **Django Project**: Shirsti Printing Company Website
- **Current Issue**: Complex dynamic pricing system with conflicting parameters
- **Goal**: Replace with static models having individual product pages
- **Inspiration**: Pricing from creativeprintarts.com, Design from qinprinting.com

## Files to Create/Modify

### 1. Update Models (apps/services/models.py)
**Action**: Add StaticProduct model alongside existing Product model (don't remove Product)

**Add these new models**:
```python
class StaticProduct(models.Model):
    # Basic fields
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    category = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE, related_name='static_products')
    description = models.TextField()
    short_description = models.TextField(max_length=300)
    
    # Design tool integration
    design_tool_enabled = models.BooleanField(default=False)
    canvas_width = models.IntegerField(null=True, blank=True)
    canvas_height = models.IntegerField(null=True, blank=True)
    
    # Pricing
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    price_unit = models.CharField(max_length=50, default="per piece")
    
    # JSON fields for static options
    available_sizes = models.JSONField(default=list)
    available_papers = models.JSONField(default=list)
    available_finishes = models.JSONField(default=list)
    available_bindings = models.JSONField(default=list)
    color_options = models.JSONField(default=list)
    quantity_tiers = models.JSONField(default=list)
    
    # Additional services
    rush_order_available = models.BooleanField(default=True)
    rush_order_percentage = models.IntegerField(default=50)
    design_service_available = models.BooleanField(default=True)
    design_service_price = models.DecimalField(max_digits=8, decimal_places=2, default=999.00)
    
    # Features and specs
    key_features = models.JSONField(default=list)
    specifications = models.JSONField(default=dict)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def calculate_price(self, quantity=100, size=None, paper=None, finish=None, binding=None, color=None, rush_order=False, design_service=False):
        # Implementation details in the actual file
        pass

class ProductFAQ(models.Model):
    static_product = models.ForeignKey(StaticProduct, on_delete=models.CASCADE, related_name='faqs')
    question = models.CharField(max_length=255)
    answer = models.TextField()
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

class ProductSample(models.Model):
    static_product = models.ForeignKey(StaticProduct, on_delete=models.CASCADE, related_name='samples')
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='products/samples/')
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

class ProductTestimonial(models.Model):
    static_product = models.ForeignKey(StaticProduct, on_delete=models.CASCADE, related_name='testimonials')
    customer_name = models.CharField(max_length=100)
    customer_company = models.CharField(max_length=100, blank=True)
    content = models.TextField()
    rating = models.IntegerField(default=5)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

### 2. Create Management Command (apps/services/management/commands/create_static_products.py)
**Action**: Create new file

**Purpose**: Populate database with 28 static products across 5 categories

**Categories to create**:
1. **Book Printing** (8 products): Children's Books, Comic Books, Coffee Table Books, Coloring Books, Art Books, Annual Reports, Yearbooks, On-Demand Books
2. **Paper Boxes** (6 products): Medical, Cosmetic, Retail, Folding Carton, Corrugated, Kraft Boxes  
3. **Marketing Materials** (7 products): Brochures ⭐, Catalogues, Posters, Flyers ⭐, Danglers, Standees, Pen Drives
4. **Stationery** (6 products): Business Cards ⭐, Letterheads ⭐, Envelopes, Bill Books ⭐, ID Cards, Stickers ⭐
5. **Documents** (1 product): Document Printing

**Key pricing examples to implement**:
- **Business Cards**: ₹599/100, with tiers: 250 (8% off), 500 (17% off), 1000 (25% off), 2500 (33% off)
- **Flyers**: ₹225/piece, A4 size, with quantity discounts up to 50%
- **Brochures**: ₹450/piece, tri-fold, with lamination options

### 3. Create Migration (apps/services/migrations/0008_add_static_products.py)
**Action**: Create migration file that adds StaticProduct without breaking existing Product model

**Important**: Keep existing Product model intact to avoid import errors

### 4. Update Admin (apps/services/admin.py)
**Action**: Add admin classes for new models

```python
@admin.register(StaticProduct)
class StaticProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'base_price', 'design_tool_enabled', 'is_active')
    list_filter = ('category', 'design_tool_enabled', 'is_active')
    prepopulated_fields = {'slug': ('name',)}
    
    fieldsets = (
        ('Basic Information', {'fields': ('name', 'slug', 'category', 'description')}),
        ('Design Tool', {'fields': ('design_tool_enabled', 'canvas_width', 'canvas_height')}),
        ('Pricing', {'fields': ('base_price', 'available_sizes', 'available_papers', 'quantity_tiers')}),
        ('Additional Services', {'fields': ('rush_order_available', 'design_service_price')}),
    )
```

### 5. Update Views (apps/services/views.py)
**Action**: Add new views for static products while keeping existing ones

**New views to add**:
- `static_product_detail(request, category_slug, product_slug)`
- `static_product_pricing_api(request, product_id)`
- Update `services_home` to show both old and new products

### 6. Update URLs (apps/services/urls.py)
**Action**: Add new URL patterns

```python
urlpatterns = [
    # Existing URLs (keep as is)
    path('', views.services_home, name='home'),
    
    # New static product URLs
    path('static/<slug:category_slug>/<slug:product_slug>/', views.static_product_detail, name='static_product_detail'),
    path('api/static-pricing/<int:product_id>/', views.static_product_pricing_api, name='static_pricing_api'),
]
```

## Implementation Steps

### Step 1: Run the Implementation
```bash
# Navigate to project directory
cd /path/to/shirsti_printing

# Run migrations
python manage.py makemigrations services
python manage.py migrate

# Create static products
python manage.py create_static_products

# Create superuser if needed
python manage.py createsuperuser
```

### Step 2: Verify Implementation
```bash
# Check admin panel
# Visit http://localhost:8000/admin/
# Navigate to Services > Static Products

# Test the new products
# Visit http://localhost:8000/services/
```

## Product Data Structure Examples

### Business Cards Example
```json
{
    "available_sizes": [
        {"name": "3.5x2 inches (Standard)", "price_modifier": 0},
        {"name": "3.5x2.5 inches", "price_modifier": 50}
    ],
    "available_papers": [
        {"name": "300 GSM Art Card", "price_modifier": 0},
        {"name": "350 GSM Art Card", "price_modifier": 100},
        {"name": "Premium Plastic (PVC)", "price_modifier": 500}
    ],
    "quantity_tiers": [
        {"min_qty": 100, "max_qty": 249, "discount_percent": 0},
        {"min_qty": 250, "max_qty": 499, "discount_percent": 8},
        {"min_qty": 500, "max_qty": 999, "discount_percent": 17},
        {"min_qty": 1000, "max_qty": 2499, "discount_percent": 25}
    ]
}
```

### Design Tool Integration
**Products with design tool enabled (canvas dimensions)**:
- Business Cards: 1050x600px (3.5"x2" at 300 DPI)
- Letterheads: 2480x3508px (A4 at 300 DPI)  
- Flyers: 2480x3508px (A4 at 300 DPI)
- Brochures: 2480x3508px (A4 at 300 DPI)
- Bill Books: 1240x1754px (A5 at 300 DPI)
- Stickers: 600x600px (2"x2" at 300 DPI)

## Expected Results

### Database Structure
- 5 service categories created
- 28 static products with individual pricing
- Quantity-based discount tiers
- Design tool integration for 11 products
- JSON-based option configurations

### Admin Interface
- Easy product management
- Visual pricing configuration
- Bulk editing capabilities
- Image upload support

### API Endpoints
- Real-time pricing calculation
- Detailed price breakdown
- Support for all product options

## Testing Instructions

1. **Admin Testing**:
   ```bash
   # Access admin at /admin/
   # Go to Services > Static Products
   # Edit any product to see pricing options
   ```

2. **Pricing API Testing**:
   ```bash
   # Test pricing calculation
   curl "http://localhost:8000/services/api/static-pricing/1/?quantity=500&paper=350%20GSM%20Art%20Card"
   ```

3. **Product Pages**:
   ```bash
   # Visit individual product pages
   # Check /services/static/stationery/business-cards/
   ```

## Success Criteria

✅ **Migration runs without errors**  
✅ **28 products created successfully**  
✅ **Admin interface fully functional**  
✅ **Pricing API returns correct calculations**  
✅ **No existing functionality broken**  
✅ **Design tool integration configured**

## Next Phase Preview

After Phase 1 completion:
- **Phase 2**: Create QinPrinting-inspired product page templates
- **Phase 3**: Frontend pricing calculator with JavaScript
- **Phase 4**: Design tool integration for marked products
- **Phase 5**: Complete migration from old to new system

## Notes for Claude Codebase

- **Preserve existing functionality**: Don't delete or modify existing Product model
- **Use exact pricing**: Follow Creative Print Arts structure precisely  
- **JSON validation**: Ensure JSON fields have proper structure
- **Error handling**: Add proper validation and error messages
- **Performance**: Use select_related and prefetch_related for queries