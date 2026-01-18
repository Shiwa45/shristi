from django.db import migrations, models
import django.db.models.deletion


def create_default_site_settings(apps, schema_editor):
    SiteSetting = apps.get_model('core', 'SiteSetting')
    SiteNavLink = apps.get_model('core', 'SiteNavLink')
    FooterLinkGroup = apps.get_model('core', 'FooterLinkGroup')
    FooterLink = apps.get_model('core', 'FooterLink')
    SocialLink = apps.get_model('core', 'SocialLink')

    settings = SiteSetting.objects.create(
        site_name="Shirsti Printing Company",
        logo_static_path="images/logo.png",
        logo_alt_text="Shirsti Printing",
        contact_phone="+91 123 456 7890",
        contact_email="info@shirstiprinting.com",
        contact_address="123 Print Street\nNew Delhi, India",
        footer_about_title="Shirsti Printing Company",
        footer_about_text=(
            "Your trusted partner for professional printing services. From business cards to large format "
            "printing, we deliver quality results that make an impression."
        ),
        contact_heading="Contact Info",
        business_hours_heading="Business Hours:",
        business_hours="Monday - Friday: 9:00 AM - 6:00 PM\nSaturday: 9:00 AM - 2:00 PM\nSunday: Closed",
        copyright_text="&copy; 2024 Shrishti Printing Company. All rights reserved.",
        is_active=True,
    )

    nav_links = [
        {"label": "Home", "url": "/", "position": "before_services", "order": 0},
        {"label": "All Products", "url": "/services/all-products/", "position": "before_services", "order": 1},
        {"label": "About", "url": "/about/", "position": "after_services", "order": 0},
        {"label": "Contact", "url": "/contact/", "position": "after_services", "order": 1},
    ]
    for link in nav_links:
        SiteNavLink.objects.create(site_settings=settings, **link)

    quick_links = FooterLinkGroup.objects.create(
        site_settings=settings,
        title="Quick Links",
        is_active=True,
        order=0,
    )
    legal_links = FooterLinkGroup.objects.create(
        site_settings=settings,
        title="Legal",
        is_active=True,
        order=1,
    )

    quick_links_items = [
        {"label": "Home", "url": "/"},
        {"label": "About Us", "url": "/about/"},
        {"label": "Contact", "url": "/contact/"},
        {"label": "FAQ", "url": "/faq/"},
        {"label": "Services", "url": "/services/categories/"},
    ]
    for index, item in enumerate(quick_links_items):
        FooterLink.objects.create(group=quick_links, order=index, is_active=True, **item)

    legal_links_items = [
        {"label": "Privacy Policy", "url": "/privacy-policy/"},
        {"label": "Terms & Conditions", "url": "/terms-conditions/"},
        {"label": "Refund Policy", "url": "/refund-policy/"},
        {"label": "Cancellation Policy", "url": "/cancellation-policy/"},
    ]
    for index, item in enumerate(legal_links_items):
        FooterLink.objects.create(group=legal_links, order=index, is_active=True, **item)

    social_links = [
        {
            "label": "Twitter",
            "url": "#",
            "order": 0,
            "icon_svg": (
                '<svg class="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">'
                '<path d="M24 4.557c-.883.392-1.832.656-2.828.775 '
                '1.017-.609 1.798-1.574 2.165-2.724-.951.564-2.005.974-3.127 1.195-'
                '.897-.957-2.178-1.555-3.594-1.555-3.179 0-5.515 2.966-4.797 6.045-'
                '4.091-.205-7.719-2.165-10.148-5.144-1.29 2.213-.669 5.108 1.523 6.574-'
                '.806-.026-1.566-.247-2.229-.616-.054 2.281 1.581 4.415 3.949 4.89-'
                '.693.188-1.452.232-2.224.084.626 1.956 2.444 3.379 4.6 3.419-'
                '2.07 1.623-4.678 2.348-7.29 2.04 2.179 1.397 4.768 2.212 7.548 2.212 '
                '9.142 0 14.307-7.721 13.995-14.646.962-.695 1.797-1.562 2.457-2.549z"/>'
                '</svg>'
            ),
        },
        {
            "label": "Twitter Alt",
            "url": "#",
            "order": 1,
            "icon_svg": (
                '<svg class="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">'
                '<path d="M22.46 6c-.77.35-1.6.58-2.46.69.88-.53 1.56-1.37 1.88-2.38-'
                '.83.5-1.75.85-2.72 1.05C18.37 4.5 17.26 4 16 4c-2.35 0-4.27 1.92-4.27 4.29 '
                '0 .34.04.67.11.98C8.28 9.09 5.11 7.38 3 4.79c-.37.63-.58 1.37-.58 2.15 '
                '0 1.49.75 2.81 1.91 3.56-.71 0-1.37-.2-1.95-.5v.03c0 2.08 1.48 3.82 '
                '3.44 4.21a4.22 4.22 0 0 1-1.93.07 4.28 4.28 0 0 0 4 2.98 8.521 8.521 0 0 1-'
                '5.33 1.84c-.34 0-.68-.02-1.02-.06C3.44 20.29 5.7 21 8.12 21 16 21 20.33 '
                '14.46 20.33 8.79c0-.19 0-.37-.01-.56.84-.6 1.56-1.36 2.14-2.23z"/>'
                '</svg>'
            ),
        },
        {
            "label": "LinkedIn",
            "url": "#",
            "order": 2,
            "icon_svg": (
                '<svg class="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">'
                '<path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-'
                '1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-'
                '.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 '
                '7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 '
                '1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 '
                '13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542'
                'C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 '
                '.774 23.2 0 22.222 0h.003z"/>'
                '</svg>'
            ),
        },
    ]
    for item in social_links:
        SocialLink.objects.create(site_settings=settings, is_active=True, **item)


def remove_default_site_settings(apps, schema_editor):
    SiteSetting = apps.get_model('core', 'SiteSetting')
    SiteSetting.objects.filter(site_name="Shirsti Printing Company").delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_no_design_section'),
    ]

    operations = [
        migrations.CreateModel(
            name='SiteSetting',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('site_name', models.CharField(default='Shirsti Printing Company', max_length=200)),
                ('logo', models.ImageField(blank=True, null=True, upload_to='site/')),
                ('logo_static_path', models.CharField(default='images/logo.png', max_length=200)),
                ('logo_alt_text', models.CharField(default='Shirsti Printing', max_length=200)),
                ('contact_phone', models.CharField(default='+91 123 456 7890', max_length=50)),
                ('contact_email', models.EmailField(default='info@shirstiprinting.com', max_length=254)),
                ('contact_address', models.TextField(default='123 Print Street\nNew Delhi, India')),
                ('footer_about_title', models.CharField(default='Shirsti Printing Company', max_length=200)),
                ('footer_about_text', models.TextField(default='Your trusted partner for professional printing services. From business cards to large format printing, we deliver quality results that make an impression.')),
                ('contact_heading', models.CharField(default='Contact Info', max_length=100)),
                ('business_hours_heading', models.CharField(default='Business Hours:', max_length=100)),
                ('business_hours', models.TextField(default='Monday - Friday: 9:00 AM - 6:00 PM\nSaturday: 9:00 AM - 2:00 PM\nSunday: Closed')),
                ('copyright_text', models.CharField(default='&copy; 2024 Shrishti Printing Company. All rights reserved.', max_length=200)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Site Setting',
                'verbose_name_plural': 'Site Settings',
            },
        ),
        migrations.CreateModel(
            name='FooterLinkGroup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100)),
                ('is_active', models.BooleanField(default=True)),
                ('order', models.IntegerField(default=0)),
                ('site_settings', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='footer_link_groups', to='core.sitesetting')),
            ],
            options={
                'verbose_name': 'Footer Link Group',
                'verbose_name_plural': 'Footer Link Groups',
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='SiteNavLink',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(max_length=100)),
                ('url', models.CharField(max_length=200)),
                ('position', models.CharField(choices=[('before_services', 'Before Services'), ('after_services', 'After Services')], default='before_services', max_length=20)),
                ('is_active', models.BooleanField(default=True)),
                ('order', models.IntegerField(default=0)),
                ('site_settings', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='nav_links', to='core.sitesetting')),
            ],
            options={
                'verbose_name': 'Site Nav Link',
                'verbose_name_plural': 'Site Nav Links',
                'ordering': ['position', 'order'],
            },
        ),
        migrations.CreateModel(
            name='SocialLink',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(max_length=100)),
                ('url', models.CharField(default='#', max_length=200)),
                ('icon_svg', models.TextField()),
                ('is_active', models.BooleanField(default=True)),
                ('order', models.IntegerField(default=0)),
                ('site_settings', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='social_links', to='core.sitesetting')),
            ],
            options={
                'verbose_name': 'Social Link',
                'verbose_name_plural': 'Social Links',
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='FooterLink',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(max_length=100)),
                ('url', models.CharField(max_length=200)),
                ('is_active', models.BooleanField(default=True)),
                ('order', models.IntegerField(default=0)),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='links', to='core.footerlinkgroup')),
            ],
            options={
                'verbose_name': 'Footer Link',
                'verbose_name_plural': 'Footer Links',
                'ordering': ['order'],
            },
        ),
        migrations.RunPython(create_default_site_settings, remove_default_site_settings),
    ]
