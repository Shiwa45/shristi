"""Custom, non-technical friendly Pricing Manager.

Two entry points from one landing page:
  1. Book Printing pricing  -> edit the BookPrintingPricing singleton
  2. Other products pricing -> edit ProductFieldOption prices per product

All views are staff-only.
"""
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .models import (
    ServiceCategory,
    StaticProduct,
    ProductFormField,
    ProductFieldOption,
    BookPrintingPricing,
)

# Categories handled by the option-row system (everything except book printing)
OTHER_CATEGORY_SLUGS = ['stationery', 'marketing-material', 'paper-boxes']


@staff_member_required
def pricing_home(request):
    """Landing page with the two choices."""
    book_count = StaticProduct.objects.filter(category__slug='book-printing').count()
    other_count = StaticProduct.objects.filter(category__slug__in=OTHER_CATEGORY_SLUGS).count()
    return render(request, 'pricing_manager/home.html', {
        'book_count': book_count,
        'other_count': other_count,
    })


@staff_member_required
def pricing_products(request):
    """List option-based products (grouped by category) to pick one to edit."""
    categories = []
    for cat in ServiceCategory.objects.filter(slug__in=OTHER_CATEGORY_SLUGS).order_by('name'):
        products = StaticProduct.objects.filter(category=cat).order_by('name')
        categories.append({'category': cat, 'products': products})
    return render(request, 'pricing_manager/product_list.html', {
        'categories': categories,
    })


@staff_member_required
def pricing_product_edit(request, product_id):
    """Edit every option price for one product, grouped by field."""
    product = get_object_or_404(StaticProduct, id=product_id)

    fields = (
        product.form_fields.filter(is_active=True)
        .order_by('section_order', 'order')
        .prefetch_related('field_options')
    )

    if request.method == 'POST':
        updated = 0
        for field in fields:
            for opt in field.field_options.all():
                key = f'price_{opt.id}'
                if key in request.POST:
                    raw = request.POST.get(key, '').strip() or '0'
                    try:
                        new_val = Decimal(raw)
                    except (InvalidOperation, ValueError):
                        continue
                    if new_val != opt.price_modifier:
                        opt.price_modifier = new_val
                        opt.save(update_fields=['price_modifier'])
                        updated += 1
        messages.success(request, f'Saved. {updated} price(s) updated for {product.name}.')
        return redirect('services:pricing_product_edit', product_id=product.id)

    # Build a render-friendly structure
    field_rows = []
    for field in fields:
        opts = list(field.field_options.all().order_by('order', 'id'))
        if not opts:
            continue
        field_rows.append({'field': field, 'options': opts})

    return render(request, 'pricing_manager/product_edit.html', {
        'product': product,
        'field_rows': field_rows,
    })


# Grouping used to render the book pricing form in neat sections
BOOK_PRICE_GROUPS = [
    ('Interior Colour — charged per page', [
        ('color_bw_standard_per_page', 'B&W Standard'),
        ('color_bw_premium_per_page', 'B&W Premium'),
        ('color_standard_per_page', 'Colour Standard'),
        ('color_premium_per_page', 'Colour Premium'),
        ('combine_bw_per_page', 'Combined: B&W pages'),
        ('combine_color_per_page', 'Combined: Colour pages'),
    ]),
    ('Book Size — flat add-on', [
        ('size_a4', 'A4'),
        ('size_letter', 'Letter'),
        ('size_executive', 'Executive'),
        ('size_a5', 'A5'),
    ]),
    ('Paper Type — flat add-on', [
        ('paper_75gsm', '75 GSM'),
        ('paper_100gsm', '100 GSM'),
        ('paper_100gsm_art', '100 GSM Art'),
        ('paper_130gsm_art', '130 GSM Art'),
    ]),
    ('Binding — flat add-on', [
        ('binding_saddle_stitch', 'Saddle Stitch'),
        ('binding_spiral', 'Spiral Binding'),
        ('binding_paperback_perfect', 'Paperback / Perfect'),
        ('binding_hardcover', 'Hardcover'),
    ]),
    ('Cover Finish — flat add-on', [
        ('cover_matte', 'Matte'),
        ('cover_glossy', 'Glossy'),
    ]),
    ('Extra Services', [
        ('cover_design_price', 'Cover page design (flat)'),
        ('inner_page_design_per_page', 'Inner page design (per page)'),
        ('isbn_price', 'ISBN allocation (flat)'),
    ]),
]


@staff_member_required
def pricing_book(request):
    """Edit the Book Printing price sheet (singleton)."""
    pricing = BookPrintingPricing.load()

    if request.method == 'POST':
        updated = 0
        for _group_name, rows in BOOK_PRICE_GROUPS:
            for attr, _label in rows:
                if attr in request.POST:
                    raw = request.POST.get(attr, '').strip() or '0'
                    try:
                        new_val = Decimal(raw)
                    except (InvalidOperation, ValueError):
                        continue
                    if getattr(pricing, attr) != new_val:
                        setattr(pricing, attr, new_val)
                        updated += 1
        pricing.save()
        messages.success(request, f'Book printing prices saved. {updated} value(s) updated.')
        return redirect('services:pricing_book')

    groups = []
    for group_name, rows in BOOK_PRICE_GROUPS:
        groups.append({
            'name': group_name,
            'rows': [{'attr': attr, 'label': label, 'value': getattr(pricing, attr)} for attr, label in rows],
        })

    return render(request, 'pricing_manager/book_edit.html', {
        'pricing': pricing,
        'groups': groups,
    })
