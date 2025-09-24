# apps/design_tool/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
import json
import uuid

User = get_user_model()

class DesignSession(models.Model):
    """Track design sessions for analytics"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.UUIDField(default=uuid.uuid4, unique=True)
    product = models.ForeignKey('services.Product', on_delete=models.CASCADE, null=True, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.IntegerField(default=0)
    actions_count = models.IntegerField(default=0)
    design_saved = models.BooleanField(default=False)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f"Session {self.session_id} - {self.user or 'Anonymous'}"


class DesignAction(models.Model):
    """Log design actions for analytics and undo/redo"""
    ACTION_TYPES = [
        ('add_text', 'Add Text'),
        ('add_image', 'Add Image'),
        ('add_shape', 'Add Shape'),
        ('add_clipart', 'Add Clipart'),
        ('modify_object', 'Modify Object'),
        ('delete_object', 'Delete Object'),
        ('move_object', 'Move Object'),
        ('resize_object', 'Resize Object'),
        ('rotate_object', 'Rotate Object'),
        ('change_color', 'Change Color'),
        ('change_font', 'Change Font'),
        ('apply_template', 'Apply Template'),
        ('save_design', 'Save Design'),
        ('export_design', 'Export Design'),
    ]

    session = models.ForeignKey(DesignSession, on_delete=models.CASCADE, related_name='actions')
    action_type = models.CharField(max_length=50, choices=ACTION_TYPES)
    canvas_state_before = models.JSONField(null=True, blank=True)
    canvas_state_after = models.JSONField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, blank=True)  # Additional action data

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.action_type} - {self.timestamp}"


class DesignAsset(models.Model):
    """Store uploaded assets (images, fonts, etc.)"""
    ASSET_TYPES = [
        ('image', 'Image'),
        ('font', 'Font'),
        ('svg', 'SVG'),
        ('template', 'Template'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='design_assets')
    name = models.CharField(max_length=200)
    asset_type = models.CharField(max_length=20, choices=ASSET_TYPES)
    file = models.FileField(upload_to='design_assets/')
    thumbnail = models.ImageField(upload_to='design_assets/thumbnails/', blank=True)
    file_size = models.PositiveIntegerField(help_text="File size in bytes")
    mime_type = models.CharField(max_length=100)
    metadata = models.JSONField(default=dict, blank=True)  # Width, height, etc.
    
    # Usage tracking
    usage_count = models.PositiveIntegerField(default=0)
    last_used = models.DateTimeField(null=True, blank=True)
    
    # Settings
    is_public = models.BooleanField(default=False)
    tags = models.CharField(max_length=500, blank=True, help_text="Comma-separated tags")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.asset_type})"

    def get_tags_list(self):
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]

    def increment_usage(self):
        from django.utils import timezone
        self.usage_count += 1
        self.last_used = timezone.now()
        self.save(update_fields=['usage_count', 'last_used'])


class DesignCollaboration(models.Model):
    """Handle design sharing and collaboration"""
    PERMISSION_TYPES = [
        ('view', 'View Only'),
        ('comment', 'View & Comment'),
        ('edit', 'Full Edit Access'),
    ]

    design = models.ForeignKey('templates_mgmt.UserDesign', on_delete=models.CASCADE, related_name='collaborations')
    shared_with = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shared_designs')
    permission = models.CharField(max_length=20, choices=PERMISSION_TYPES, default='view')
    shared_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shared_by_me')
    shared_at = models.DateTimeField(auto_now_add=True)
    accessed_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('design', 'shared_with')
        ordering = ['-shared_at']

    def __str__(self):
        return f"{self.design.name} shared with {self.shared_with.get_full_name() or self.shared_with.username}"


class DesignComment(models.Model):
    """Comments on shared designs"""
    design = models.ForeignKey('templates_mgmt.UserDesign', on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.TextField()
    position_x = models.FloatField(null=True, blank=True)  # Comment position on canvas
    position_y = models.FloatField(null=True, blank=True)
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Comment by {self.user.get_full_name() or self.user.username} on {self.design.name}"


class DesignVersion(models.Model):
    """Version control for designs"""
    design = models.ForeignKey('templates_mgmt.UserDesign', on_delete=models.CASCADE, related_name='versions')
    version_number = models.PositiveIntegerField()
    canvas_data = models.JSONField()
    preview_image = models.ImageField(upload_to='design_versions/', blank=True)
    changes_description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    file_size = models.PositiveIntegerField(default=0)  # Canvas data size in bytes

    class Meta:
        unique_together = ('design', 'version_number')
        ordering = ['-version_number']

    def __str__(self):
        return f"{self.design.name} v{self.version_number}"

    def save(self, *args, **kwargs):
        if not self.version_number:
            # Auto-increment version number
            last_version = DesignVersion.objects.filter(design=self.design).first()
            self.version_number = (last_version.version_number if last_version else 0) + 1
        
        # Calculate file size
        if self.canvas_data:
            self.file_size = len(json.dumps(self.canvas_data).encode('utf-8'))
        
        super().save(*args, **kwargs)


class FontLibrary(models.Model):
    """Custom font library for design tool"""
    name = models.CharField(max_length=200)
    display_name = models.CharField(max_length=200)
    font_family = models.CharField(max_length=200)  # CSS font-family value
    font_file = models.FileField(upload_to='fonts/')  # .woff2, .woff, .ttf
    font_weight = models.CharField(max_length=20, default='400')
    font_style = models.CharField(max_length=20, default='normal')
    category = models.CharField(max_length=50, choices=[
        ('serif', 'Serif'),
        ('sans-serif', 'Sans Serif'),
        ('monospace', 'Monospace'),
        ('cursive', 'Cursive'),
        ('fantasy', 'Fantasy'),
        ('display', 'Display'),
    ], default='sans-serif')
    
    # Settings
    is_active = models.BooleanField(default=True)
    is_premium = models.BooleanField(default=False)
    usage_count = models.PositiveIntegerField(default=0)
    
    # Metadata
    file_size = models.PositiveIntegerField()
    preview_text = models.CharField(max_length=100, default="The quick brown fox jumps over the lazy dog")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['category', 'display_name']

    def __str__(self):
        return self.display_name

    def get_css_import(self):
        """Generate CSS @font-face rule"""
        return f"""
        @font-face {{
            font-family: '{self.font_family}';
            src: url('{self.font_file.url}') format('woff2');
            font-weight: {self.font_weight};
            font-style: {self.font_style};
            font-display: swap;
        }}
        """

    def increment_usage(self):
        self.usage_count += 1
        self.save(update_fields=['usage_count'])


class ClipartLibrary(models.Model):
    """Clipart/icon library for design tool"""
    name = models.CharField(max_length=200)
    svg_content = models.TextField()  # Actual SVG content
    thumbnail = models.ImageField(upload_to='clipart/thumbnails/')
    category = models.CharField(max_length=100)
    tags = models.CharField(max_length=500, help_text="Comma-separated tags")
    
    # Colors (for filtering)
    primary_color = models.CharField(max_length=7, default='#000000')  # Hex color
    has_multiple_colors = models.BooleanField(default=False)
    
    # Settings
    is_active = models.BooleanField(default=True)
    is_premium = models.BooleanField(default=False)
    usage_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['category', 'name']

    def __str__(self):
        return self.name

    def get_tags_list(self):
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]

    def increment_usage(self):
        self.usage_count += 1
        self.save(update_fields=['usage_count'])