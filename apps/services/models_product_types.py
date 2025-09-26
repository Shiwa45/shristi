# apps/services/models_product_types.py
from django.db import models
from decimal import Decimal


class BookPrintingQuote(models.Model):
    """Static model for book printing quotes"""
    # Basic Info
    quantity = models.IntegerField(choices=[
        (25, '25 Books'),
        (50, '50 Books'),
        (100, '100 Books'),
        (250, '250 Books'),
        (500, '500 Books'),
        (1000, '1000 Books'),
        (2500, '2500 Books'),
        (5000, '5000 Books'),
    ], default=100)
    
    book_size = models.CharField(max_length=20, choices=[
        ('A5', 'A5 (148 x 210 mm)'),
        ('A4', 'A4 (210 x 297 mm)'),
        ('6x9', '6" x 9" (152 x 229 mm)'),
        ('8.5x11', '8.5" x 11" (216 x 279 mm)'),
        ('custom', 'Custom Size'),
    ], default='A5')
    
    page_count = models.IntegerField(choices=[
        (24, '24 Pages'),
        (32, '32 Pages'),
        (48, '48 Pages'),
        (64, '64 Pages'),
        (80, '80 Pages'),
        (100, '100 Pages'),
        (128, '128 Pages'),
        (150, '150 Pages'),
        (200, '200 Pages'),
        (250, '250 Pages'),
        (300, '300 Pages'),
    ], default=100)
    
    inner_paper = models.CharField(max_length=20, choices=[
        ('70gsm_offset', '70 GSM Offset Paper'),
        ('80gsm_offset', '80 GSM Offset Paper'),
        ('90gsm_offset', '90 GSM Offset Paper'),
        ('100gsm_art', '100 GSM Art Paper'),
        ('130gsm_art', '130 GSM Art Paper'),
    ], default='70gsm_offset')
    
    inner_printing = models.CharField(max_length=10, choices=[
        ('bw', 'Black & White'),
        ('color', 'Full Color (4+4)'),
        ('mixed', 'Mixed (Some B&W, Some Color)'),
    ], default='bw')
    
    cover_paper = models.CharField(max_length=20, choices=[
        ('250gsm_art', '250 GSM Art Card'),
        ('300gsm_art', '300 GSM Art Card'),
        ('350gsm_art', '350 GSM Art Card'),
        ('250gsm_duplex', '250 GSM Duplex Board'),
        ('300gsm_duplex', '300 GSM Duplex Board'),
    ], default='250gsm_art')
    
    cover_printing = models.CharField(max_length=10, choices=[
        ('color_4_0', 'Full Color Front Only (4+0)'),
        ('color_4_4', 'Full Color Both Sides (4+4)'),
        ('color_4_1', 'Color Front + Black Back (4+1)'),
    ], default='color_4_0')
    
    binding_type = models.CharField(max_length=20, choices=[
        ('saddle_stitch', 'Saddle Stitching'),
        ('perfect_binding', 'Perfect Binding'),
        ('spiral_binding', 'Spiral Binding'),
        ('case_binding', 'Case Binding (Hardcover)'),
        ('thread_sewing', 'Thread Sewing + Perfect Binding'),
    ], default='perfect_binding')
    
    cover_finish = models.CharField(max_length=15, choices=[
        ('matte', 'Matte Finish'),
        ('gloss', 'Gloss Lamination'),
        ('matte_lam', 'Matte Lamination'),
        ('spot_uv', 'Spot UV'),
        ('foiling', 'Gold/Silver Foiling'),
        ('embossing', 'Embossing'),
    ], default='matte_lam')
    
    # Add-on Services
    design_service = models.CharField(max_length=10, choices=[
        ('none', 'No Design Service'),
        ('basic', 'Basic Design Service (+₹2,500)'),
        ('premium', 'Premium Design Service (+₹5,000)'),
        ('formatting', 'Text Formatting Only (+₹1,500)'),
    ], default='none')
    
    isbn_service = models.BooleanField(default=False, verbose_name='ISBN Allocation (+₹500)')
    barcode_service = models.BooleanField(default=False, verbose_name='Barcode Generation (+₹200)')
    copyright_service = models.BooleanField(default=False, verbose_name='Copyright Registration (+₹2,000)')
    
    # Customer Info
    customer_name = models.CharField(max_length=100, blank=True)
    customer_email = models.EmailField(blank=True)
    customer_phone = models.CharField(max_length=15, blank=True)
    
    # Calculated Fields
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def calculate_price(self):
        """Calculate the total price based on selections"""
        base_price = Decimal('150.00')  # Base price per book
        
        # Quantity discounts
        quantity_discounts = {
            25: 0, 50: 0, 100: 0.05, 250: 0.10, 500: 0.15, 
            1000: 0.20, 2500: 0.25, 5000: 0.30
        }
        
        # Size modifiers
        size_modifiers = {
            'A5': Decimal('0'), 'A4': Decimal('50'), '6x9': Decimal('25'), 
            '8.5x11': Decimal('75'), 'custom': Decimal('100')
        }
        
        # Page count modifiers (₹2.5 per page above 24)
        page_modifier = Decimal(str(max(0, (self.page_count - 24) * 2.5)))
        
        # Paper modifiers
        inner_paper_modifiers = {
            '70gsm_offset': Decimal('0'), '80gsm_offset': Decimal('25'), '90gsm_offset': Decimal('50'),
            '100gsm_art': Decimal('100'), '130gsm_art': Decimal('150')
        }
        
        cover_paper_modifiers = {
            '250gsm_art': Decimal('0'), '300gsm_art': Decimal('50'), '350gsm_art': Decimal('100'),
            '250gsm_duplex': Decimal('25'), '300gsm_duplex': Decimal('75')
        }
        
        # Printing modifiers
        inner_printing_modifiers = {'bw': Decimal('0'), 'color': Decimal('200'), 'mixed': Decimal('100')}
        cover_printing_modifiers = {'color_4_0': Decimal('0'), 'color_4_4': Decimal('100'), 'color_4_1': Decimal('50')}
        
        # Binding modifiers
        binding_modifiers = {
            'saddle_stitch': Decimal('0'), 'perfect_binding': Decimal('150'), 'spiral_binding': Decimal('100'),
            'case_binding': Decimal('500'), 'thread_sewing': Decimal('250')
        }
        
        # Finish modifiers
        finish_modifiers = {
            'matte': Decimal('0'), 'gloss': Decimal('75'), 'matte_lam': Decimal('75'), 'spot_uv': Decimal('200'),
            'foiling': Decimal('300'), 'embossing': Decimal('250')
        }
        
        # Calculate unit price
        unit_price = base_price
        unit_price += size_modifiers.get(self.book_size, Decimal('0'))
        unit_price += page_modifier
        unit_price += inner_paper_modifiers.get(self.inner_paper, Decimal('0'))
        unit_price += cover_paper_modifiers.get(self.cover_paper, Decimal('0'))
        unit_price += inner_printing_modifiers.get(self.inner_printing, Decimal('0'))
        unit_price += cover_printing_modifiers.get(self.cover_printing, Decimal('0'))
        unit_price += binding_modifiers.get(self.binding_type, Decimal('0'))
        unit_price += finish_modifiers.get(self.cover_finish, Decimal('0'))
        
        # Apply quantity discount
        discount = Decimal(str(quantity_discounts.get(self.quantity, 0)))
        unit_price = unit_price * (Decimal('1') - discount)
        
        # Calculate total before add-ons
        total_price = unit_price * self.quantity
        
        # Add-on services
        design_costs = {'none': Decimal('0'), 'basic': Decimal('2500'), 'premium': Decimal('5000'), 'formatting': Decimal('1500')}
        total_price += design_costs.get(self.design_service, Decimal('0'))
        
        if self.isbn_service:
            total_price += Decimal('500')
        if self.barcode_service:
            total_price += Decimal('200')
        if self.copyright_service:
            total_price += Decimal('2000')
        
        self.unit_price = unit_price
        self.total_price = total_price
        
        return {
            'unit_price': float(unit_price),
            'total_price': float(total_price),
            'quantity': self.quantity,
            'discount_percent': discount * 100
        }
    
    def save(self, *args, **kwargs):
        self.calculate_price()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Book Quote - {self.quantity} books - ₹{self.total_price}"


class BusinessCardQuote(models.Model):
    """Static model for business card quotes"""
    quantity = models.IntegerField(choices=[
        (100, '100 Cards'),
        (250, '250 Cards'),
        (500, '500 Cards'),
        (1000, '1000 Cards'),
        (2500, '2500 Cards'),
        (5000, '5000 Cards'),
    ], default=500)
    
    card_size = models.CharField(max_length=15, choices=[
        ('standard', 'Standard (90 x 54 mm)'),
        ('mini', 'Mini (85 x 50 mm)'),
        ('square', 'Square (70 x 70 mm)'),
        ('folded', 'Folded (180 x 54 mm)'),
    ], default='standard')
    
    paper_type = models.CharField(max_length=20, choices=[
        ('300gsm_art', '300 GSM Art Card'),
        ('350gsm_art', '350 GSM Art Card'),
        ('400gsm_art', '400 GSM Art Card'),
        ('300gsm_duplex', '300 GSM Duplex Board'),
        ('textured', 'Textured Paper'),
        ('linen', 'Linen Finish'),
    ], default='300gsm_art')
    
    printing_sides = models.CharField(max_length=10, choices=[
        ('single', 'Single Side (4+0)'),
        ('double', 'Double Side (4+4)'),
    ], default='double')
    
    finishing = models.CharField(max_length=15, choices=[
        ('matte', 'Matte Finish'),
        ('gloss_lam', 'Gloss Lamination'),
        ('matte_lam', 'Matte Lamination'),
        ('spot_uv', 'Spot UV'),
        ('foiling', 'Gold/Silver Foiling'),
        ('embossing', 'Embossing'),
    ], default='matte_lam')
    
    design_service = models.CharField(max_length=10, choices=[
        ('none', 'No Design Service'),
        ('basic', 'Basic Design (+₹500)'),
        ('premium', 'Premium Design (+₹1,500)'),
    ], default='none')
    
    # Customer Info
    customer_name = models.CharField(max_length=100, blank=True)
    customer_email = models.EmailField(blank=True)
    customer_phone = models.CharField(max_length=15, blank=True)
    
    # Calculated Fields
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def calculate_price(self):
        """Calculate the total price based on selections"""
        base_price = Decimal('8.00')  # Base price per card
        
        # Quantity discounts
        quantity_discounts = {
            100: 0, 250: 0.10, 500: 0.20, 1000: 0.30, 2500: 0.35, 5000: 0.40
        }
        
        # Size modifiers
        size_modifiers = {'standard': Decimal('0'), 'mini': Decimal('-2'), 'square': Decimal('2'), 'folded': Decimal('4')}
        
        # Paper modifiers
        paper_modifiers = {
            '300gsm_art': Decimal('0'), '350gsm_art': Decimal('1'), '400gsm_art': Decimal('2'),
            '300gsm_duplex': Decimal('0.5'), 'textured': Decimal('3'), 'linen': Decimal('4')
        }
        
        # Printing modifiers
        printing_modifiers = {'single': Decimal('0'), 'double': Decimal('2')}
        
        # Finishing modifiers
        finishing_modifiers = {
            'matte': Decimal('0'), 'gloss_lam': Decimal('3'), 'matte_lam': Decimal('3'), 'spot_uv': Decimal('6'),
            'foiling': Decimal('10'), 'embossing': Decimal('8')
        }
        
        # Calculate unit price
        unit_price = base_price
        unit_price += size_modifiers.get(self.card_size, Decimal('0'))
        unit_price += paper_modifiers.get(self.paper_type, Decimal('0'))
        unit_price += printing_modifiers.get(self.printing_sides, Decimal('0'))
        unit_price += finishing_modifiers.get(self.finishing, Decimal('0'))
        
        # Apply quantity discount
        discount = Decimal(str(quantity_discounts.get(self.quantity, 0)))
        unit_price = unit_price * (Decimal('1') - discount)
        
        # Calculate total
        total_price = unit_price * self.quantity
        
        # Add design service
        design_costs = {'none': Decimal('0'), 'basic': Decimal('500'), 'premium': Decimal('1500')}
        total_price += design_costs.get(self.design_service, Decimal('0'))
        
        self.unit_price = unit_price
        self.total_price = total_price
        
        return {
            'unit_price': float(unit_price),
            'total_price': float(total_price),
            'quantity': self.quantity,
            'discount_percent': discount * 100
        }
    
    def save(self, *args, **kwargs):
        self.calculate_price()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Business Card Quote - {self.quantity} cards - ₹{self.total_price}"


class ChildrenBookQuote(models.Model):
    """Static model for children's book quotes with special features"""
    # Basic Info
    quantity = models.IntegerField(choices=[
        (25, '25 Books'),
        (50, '50 Books'),
        (100, '100 Books'),
        (250, '250 Books'),
        (500, '500 Books'),
        (1000, '1000 Books'),
    ], default=100)
    
    book_size = models.CharField(max_length=20, choices=[
        ('A5', 'A5 (148 x 210 mm) - Perfect for little hands'),
        ('A4', 'A4 (210 x 297 mm) - Large format'),
        ('square', 'Square (200 x 200 mm) - Fun square format'),
        ('custom', 'Custom Size'),
    ], default='A5')
    
    page_count = models.IntegerField(choices=[
        (16, '16 Pages - Short story'),
        (24, '24 Pages - Standard'),
        (32, '32 Pages - Extended story'),
        (48, '48 Pages - Chapter book'),
    ], default=24)
    
    age_group = models.CharField(max_length=20, choices=[
        ('toddler', '0-3 Years - Toddlers'),
        ('preschool', '3-6 Years - Preschool'),
        ('early_reader', '6-9 Years - Early Readers'),
        ('middle_grade', '9-12 Years - Middle Grade'),
    ], default='preschool')
    
    # Paper & Printing
    inner_paper = models.CharField(max_length=20, choices=[
        ('80gsm_offset', '80 GSM Offset - Standard quality'),
        ('100gsm_art', '100 GSM Art Paper - Premium quality'),
        ('130gsm_art', '130 GSM Art Paper - Luxury quality'),
    ], default='80gsm_offset')
    
    inner_printing = models.CharField(max_length=15, choices=[
        ('full_color', 'Full Color - Vibrant illustrations'),
        ('mixed', 'Mixed - Some color, some B&W'),
        ('bw', 'Black & White - Text-based'),
    ], default='full_color')
    
    cover_paper = models.CharField(max_length=20, choices=[
        ('300gsm_art', '300 GSM Art Card - Durable'),
        ('350gsm_art', '350 GSM Art Card - Premium'),
        ('board_book', 'Board Book - Extra thick for toddlers'),
    ], default='300gsm_art')
    
    binding_type = models.CharField(max_length=25, choices=[
        ('saddle_stitch', 'Saddle Stitching - Standard'),
        ('perfect_binding', 'Perfect Binding - Professional'),
        ('spiral_binding', 'Spiral Binding - Easy to flip'),
        ('board_book_binding', 'Board Book Binding - Toddler-safe'),
    ], default='saddle_stitch')
    
    cover_finish = models.CharField(max_length=15, choices=[
        ('matte_lam', 'Matte Lamination - Smooth finish'),
        ('gloss_lam', 'Gloss Lamination - Shiny finish'),
        ('spot_uv', 'Spot UV - Special effects'),
        ('soft_touch', 'Soft Touch - Velvety feel'),
    ], default='matte_lam')
    
    # Special Features for Children's Books
    rounded_corners = models.BooleanField(default=False, verbose_name='Rounded Corners (+₹200)')
    scratch_sniff = models.BooleanField(default=False, verbose_name='Scratch & Sniff Pages (+₹500)')
    pop_up_elements = models.BooleanField(default=False, verbose_name='Pop-up Elements (+₹800)')
    texture_pages = models.BooleanField(default=False, verbose_name='Textured Pages (+₹300)')
    glow_in_dark = models.BooleanField(default=False, verbose_name='Glow-in-Dark Ink (+₹600)')
    sound_module = models.BooleanField(default=False, verbose_name='Sound Module (+₹1200)')
    
    # Services
    design_service = models.CharField(max_length=15, choices=[
        ('none', 'I have my own illustrations'),
        ('basic', 'Basic Illustration Service (+₹5,000)'),
        ('premium', 'Premium Illustration Service (+₹10,000)'),
        ('custom', 'Custom Character Design (+₹15,000)'),
    ], default='none')
    
    writing_service = models.CharField(max_length=15, choices=[
        ('none', 'I have my own story'),
        ('editing', 'Story Editing & Proofreading (+₹2,000)'),
        ('ghostwriting', 'Professional Story Writing (+₹8,000)'),
    ], default='none')
    
    publishing_service = models.CharField(max_length=15, choices=[
        ('none', 'Print only'),
        ('isbn', 'ISBN Allocation (+₹500)'),
        ('full_publishing', 'Full Publishing Package (+₹3,000)'),
    ], default='none')
    
    # Customer Info
    customer_name = models.CharField(max_length=100)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=15)
    book_title = models.CharField(max_length=200, blank=True, verbose_name='Book Title (Optional)')
    
    # Calculated Fields
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def calculate_price(self):
        """Calculate the total price based on selections"""
        base_price = Decimal('200.00')  # Higher base price for children's books
        
        # Quantity discounts
        quantity_discounts = {
            25: 0, 50: 0.05, 100: 0.10, 250: 0.15, 500: 0.20, 1000: 0.25
        }
        
        # Size modifiers
        size_modifiers = {
            'A5': Decimal('0'), 'A4': Decimal('50'), 'square': Decimal('30'), 'custom': Decimal('100')
        }
        
        # Page count modifiers (₹5 per page above 16)
        page_modifier = Decimal(str(max(0, (self.page_count - 16) * 5)))
        
        # Age group modifiers (toddler books cost more due to durability requirements)
        age_modifiers = {
            'toddler': Decimal('100'), 'preschool': Decimal('50'), 
            'early_reader': Decimal('0'), 'middle_grade': Decimal('0')
        }
        
        # Paper modifiers
        inner_paper_modifiers = {
            '80gsm_offset': Decimal('0'), '100gsm_art': Decimal('50'), '130gsm_art': Decimal('100')
        }
        
        cover_paper_modifiers = {
            '300gsm_art': Decimal('0'), '350gsm_art': Decimal('50'), 'board_book': Decimal('200')
        }
        
        # Printing modifiers (children's books often need full color)
        inner_printing_modifiers = {
            'full_color': Decimal('150'), 'mixed': Decimal('75'), 'bw': Decimal('0')
        }
        
        # Binding modifiers
        binding_modifiers = {
            'saddle_stitch': Decimal('0'), 'perfect_binding': Decimal('100'), 
            'spiral_binding': Decimal('75'), 'board_book_binding': Decimal('300')
        }
        
        # Finish modifiers
        finish_modifiers = {
            'matte_lam': Decimal('50'), 'gloss_lam': Decimal('75'), 
            'spot_uv': Decimal('150'), 'soft_touch': Decimal('200')
        }
        
        # Calculate unit price
        unit_price = base_price
        unit_price += size_modifiers.get(self.book_size, Decimal('0'))
        unit_price += page_modifier
        unit_price += age_modifiers.get(self.age_group, Decimal('0'))
        unit_price += inner_paper_modifiers.get(self.inner_paper, Decimal('0'))
        unit_price += cover_paper_modifiers.get(self.cover_paper, Decimal('0'))
        unit_price += inner_printing_modifiers.get(self.inner_printing, Decimal('0'))
        unit_price += binding_modifiers.get(self.binding_type, Decimal('0'))
        unit_price += finish_modifiers.get(self.cover_finish, Decimal('0'))
        
        # Special features (per book)
        if self.rounded_corners:
            unit_price += Decimal('2')  # ₹2 per book
        if self.scratch_sniff:
            unit_price += Decimal('5')  # ₹5 per book
        if self.pop_up_elements:
            unit_price += Decimal('8')  # ₹8 per book
        if self.texture_pages:
            unit_price += Decimal('3')  # ₹3 per book
        if self.glow_in_dark:
            unit_price += Decimal('6')  # ₹6 per book
        if self.sound_module:
            unit_price += Decimal('12')  # ₹12 per book
        
        # Apply quantity discount
        discount = Decimal(str(quantity_discounts.get(self.quantity, 0)))
        unit_price = unit_price * (Decimal('1') - discount)
        
        # Calculate total before services
        total_price = unit_price * self.quantity
        
        # Add services (one-time costs)
        design_costs = {
            'none': Decimal('0'), 'basic': Decimal('5000'), 
            'premium': Decimal('10000'), 'custom': Decimal('15000')
        }
        total_price += design_costs.get(self.design_service, Decimal('0'))
        
        writing_costs = {
            'none': Decimal('0'), 'editing': Decimal('2000'), 'ghostwriting': Decimal('8000')
        }
        total_price += writing_costs.get(self.writing_service, Decimal('0'))
        
        publishing_costs = {
            'none': Decimal('0'), 'isbn': Decimal('500'), 'full_publishing': Decimal('3000')
        }
        total_price += publishing_costs.get(self.publishing_service, Decimal('0'))
        
        self.unit_price = unit_price
        self.total_price = total_price
        
        return {
            'unit_price': float(unit_price),
            'total_price': float(total_price),
            'quantity': self.quantity,
            'discount_percent': discount * 100
        }
    
    def save(self, *args, **kwargs):
        self.calculate_price()
        super().save(*args, **kwargs)
    
    def __str__(self):
        title = f" - {self.book_title}" if self.book_title else ""
        return f"Children's Book Quote{title} - {self.quantity} books - ₹{self.total_price}"


class BrochureQuote(models.Model):
    """Static model for brochure/flyer quotes"""
    quantity = models.IntegerField(choices=[
        (100, '100 Pieces'),
        (250, '250 Pieces'),
        (500, '500 Pieces'),
        (1000, '1000 Pieces'),
        (2500, '2500 Pieces'),
        (5000, '5000 Pieces'),
    ], default=500)
    
    size = models.CharField(max_length=10, choices=[
        ('A4', 'A4 (210 x 297 mm)'),
        ('A5', 'A5 (148 x 210 mm)'),
        ('A3', 'A3 (297 x 420 mm)'),
        ('dl', 'DL (99 x 210 mm)'),
        ('custom', 'Custom Size'),
    ], default='A4')
    
    paper_type = models.CharField(max_length=15, choices=[
        ('130gsm_art', '130 GSM Art Paper'),
        ('170gsm_art', '170 GSM Art Paper'),
        ('200gsm_art', '200 GSM Art Paper'),
        ('250gsm_art', '250 GSM Art Card'),
        ('300gsm_art', '300 GSM Art Card'),
    ], default='170gsm_art')
    
    folding = models.CharField(max_length=15, choices=[
        ('no_fold', 'No Folding (Flat)'),
        ('half_fold', 'Half Fold'),
        ('tri_fold', 'Tri-Fold'),
        ('z_fold', 'Z-Fold'),
        ('gate_fold', 'Gate Fold'),
    ], default='tri_fold')
    
    printing_sides = models.CharField(max_length=10, choices=[
        ('single', 'Single Side (4+0)'),
        ('double', 'Double Side (4+4)'),
    ], default='double')
    
    finishing = models.CharField(max_length=15, choices=[
        ('matte', 'Matte Finish'),
        ('gloss_lam', 'Gloss Lamination'),
        ('matte_lam', 'Matte Lamination'),
        ('spot_uv', 'Spot UV'),
    ], default='matte_lam')
    
    # Customer Info
    customer_name = models.CharField(max_length=100, blank=True)
    customer_email = models.EmailField(blank=True)
    customer_phone = models.CharField(max_length=15, blank=True)
    
    # Calculated Fields
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def calculate_price(self):
        """Calculate the total price based on selections"""
        base_price = Decimal('12.00')  # Base price per piece
        
        # Quantity discounts
        quantity_discounts = {
            100: 0, 250: 0.10, 500: 0.15, 1000: 0.20, 2500: 0.25, 5000: 0.30
        }
        
        # Size modifiers
        size_modifiers = {'A4': Decimal('0'), 'A5': Decimal('-2'), 'A3': Decimal('8'), 'dl': Decimal('-4'), 'custom': Decimal('6')}
        
        # Paper modifiers
        paper_modifiers = {
            '130gsm_art': Decimal('0'), '170gsm_art': Decimal('2'), '200gsm_art': Decimal('4'),
            '250gsm_art': Decimal('6'), '300gsm_art': Decimal('8')
        }
        
        # Folding modifiers
        folding_modifiers = {
            'no_fold': Decimal('0'), 'half_fold': Decimal('2'), 'tri_fold': Decimal('4'), 
            'z_fold': Decimal('4'), 'gate_fold': Decimal('6')
        }
        
        # Printing modifiers
        printing_modifiers = {'single': Decimal('0'), 'double': Decimal('6')}
        
        # Finishing modifiers
        finishing_modifiers = {'matte': Decimal('0'), 'gloss_lam': Decimal('4'), 'matte_lam': Decimal('4'), 'spot_uv': Decimal('8')}
        
        # Calculate unit price
        unit_price = base_price
        unit_price += size_modifiers.get(self.size, Decimal('0'))
        unit_price += paper_modifiers.get(self.paper_type, Decimal('0'))
        unit_price += folding_modifiers.get(self.folding, Decimal('0'))
        unit_price += printing_modifiers.get(self.printing_sides, Decimal('0'))
        unit_price += finishing_modifiers.get(self.finishing, Decimal('0'))
        
        # Apply quantity discount
        discount = Decimal(str(quantity_discounts.get(self.quantity, 0)))
        unit_price = unit_price * (Decimal('1') - discount)
        
        # Calculate total
        total_price = unit_price * self.quantity
        
        self.unit_price = unit_price
        self.total_price = total_price
        
        return {
            'unit_price': float(unit_price),
            'total_price': float(total_price),
            'quantity': self.quantity,
            'discount_percent': discount * 100
        }
    
    def save(self, *args, **kwargs):
        self.calculate_price()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Brochure Quote - {self.quantity} pieces - ₹{self.total_price}"