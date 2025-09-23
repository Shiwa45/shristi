# apps/templates_mgmt/models.py
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class TemplateCategory(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Template Categories"

    def __str__(self):
        return self.name


class DesignTemplate(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.ForeignKey(TemplateCategory, on_delete=models.CASCADE, related_name='templates')
    
    # File storage
    thumbnail = models.ImageField(upload_to='templates/thumbnails/')
    preview_image = models.ImageField(upload_to='templates/previews/', blank=True)
    svg_file = models.FileField(upload_to='templates/svg/', blank=True, help_text="SVG template file")
    json_data = models.JSONField(blank=True, null=True, help_text="Fabric.js JSON data")
    
    # Specifications
    width_mm = models.FloatField()
    height_mm = models.FloatField()
    bleed_mm = models.FloatField(default=3.0)
    safe_zone_mm = models.FloatField(default=5.0)
    
    # Meta
    is_active = models.BooleanField(default=True)
    is_premium = models.BooleanField(default=False)
    download_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class UserDesign(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='designs')
    name = models.CharField(max_length=200)
    product = models.ForeignKey('services.Product', on_delete=models.CASCADE)
    
    # Design data
    canvas_data = models.JSONField(help_text="Fabric.js canvas JSON")
    preview_image = models.ImageField(upload_to='designs/previews/', blank=True)
    
    # Specifications
    width_mm = models.FloatField()
    height_mm = models.FloatField()
    bleed_mm = models.FloatField(default=3.0)
    safe_zone_mm = models.FloatField(default=5.0)
    
    # Meta
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.name} by {self.user.email}"


