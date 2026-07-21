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
    QuantityTier,
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

        # Quantity discount tiers — update / delete existing rows
        for tier in list(product.qty_tiers.all()):
            if request.POST.get(f'tier_del_{tier.id}'):
                tier.delete()
                updated += 1
                continue
            q_raw = request.POST.get(f'tier_qty_{tier.id}')
            d_raw = request.POST.get(f'tier_disc_{tier.id}')
            if q_raw is None and d_raw is None:
                continue
            try:
                new_qty = max(int(float(q_raw or tier.min_quantity)), 1)
                new_disc = Decimal((d_raw or '0').strip() or '0')
            except (InvalidOperation, ValueError):
                continue
            if new_qty != tier.min_quantity or new_disc != tier.discount_percent:
                tier.min_quantity = new_qty
                tier.discount_percent = new_disc
                tier.save()
                updated += 1

        # New tier rows (blank inputs at the bottom of the card)
        for i in range(1, 4):
            q_raw = (request.POST.get(f'new_tier_qty_{i}') or '').strip()
            d_raw = (request.POST.get(f'new_tier_disc_{i}') or '').strip()
            if not q_raw:
                continue
            try:
                QuantityTier.objects.update_or_create(
                    product=product,
                    min_quantity=max(int(float(q_raw)), 1),
                    defaults={'discount_percent': Decimal(d_raw or '0'), 'is_active': True},
                )
                updated += 1
            except (InvalidOperation, ValueError):
                continue

        messages.success(request, f'Saved. {updated} change(s) applied for {product.name}.')
        return redirect('services:pricing_product_edit', product_id=product.id)

    # Build a render-friendly structure
    field_rows = []
    for field in fields:
        opts = list(field.field_options.all().order_by('order', 'id'))
        if not opts:
            continue
        field_rows.append({'field': field, 'options': opts})

    tiers = product.qty_tiers.all().order_by('min_quantity')

    return render(request, 'pricing_manager/product_edit.html', {
        'product': product,
        'field_rows': field_rows,
        'tiers': tiers,
    })


# Grouping used to render the book pricing form in neat sections
# Interior colour, book size and paper are now priced together by the
# per-page matrix (edited as a grid, see BOOK_MATRIX_* below), so they are no
# longer listed as flat scalar rows here.
BOOK_PRICE_GROUPS = [
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
    ('Bulk Discounts — % off the subtotal at these quantities', [
        ('bulk_qty_1', 'Tier 1 — minimum quantity'),
        ('bulk_disc_1', 'Tier 1 — discount (%)'),
        ('bulk_qty_2', 'Tier 2 — minimum quantity'),
        ('bulk_disc_2', 'Tier 2 — discount (%)'),
        ('bulk_qty_3', 'Tier 3 — minimum quantity'),
        ('bulk_disc_3', 'Tier 3 — discount (%)'),
    ]),
]


def _book_row_kind(attr):
    """Input adornment: rupee prefix for money, plain for qty, %-suffix for percent."""
    if attr.startswith('bulk_qty'):
        return 'qty'
    if attr.startswith('bulk_disc'):
        return 'pct'
    return 'money'


# Axis labels for the per-page price matrix (interior × size × paper).
# Codes must match the values used on the product page + in the JSON matrix.
BOOK_MATRIX_INTERIORS = [
    ('bw_premium', 'Black & White Premium'),
    ('bw_standard', 'Black & White Standard'),
    ('color_premium', 'Colour Premium'),
    ('color_standard', 'Colour Standard'),
]
BOOK_MATRIX_SIZES = [
    ('a4', 'A4'), ('letter', 'Letter'), ('executive', 'Executive'), ('a5', 'A5'),
]
BOOK_MATRIX_PAPERS = [
    ('75gsm', '75 GSM'), ('100gsm', '100 GSM'),
    ('100gsm_art', '100 GSM Art'), ('130gsm_art', '130 GSM Art'),
]


def _build_matrix_view(matrix):
    """Shape the stored matrix into interior→rows(size)→cells(paper) for the UI."""
    tables = []
    for icode, ilabel in BOOK_MATRIX_INTERIORS:
        rows = []
        for scode, slabel in BOOK_MATRIX_SIZES:
            cells = []
            for pcode, _plabel in BOOK_MATRIX_PAPERS:
                val = (matrix.get(icode, {}).get(scode, {}) or {}).get(pcode, 0)
                cells.append({
                    'name': f'm__{icode}__{scode}__{pcode}',
                    'value': val,
                })
            rows.append({'label': slabel, 'cells': cells})
        tables.append({
            'code': icode,
            'label': ilabel,
            'papers': [pl for _pc, pl in BOOK_MATRIX_PAPERS],
            'rows': rows,
        })
    return tables


def _build_spreadsheet_rows(components):
    """Render the price sheet one workbook record at a time."""
    rows = []
    for icode, ilabel in BOOK_MATRIX_INTERIORS:
        for scode, slabel in BOOK_MATRIX_SIZES:
            for pcode, plabel in BOOK_MATRIX_PAPERS:
                cell = (components.get(icode, {}).get(scode, {}) or {}).get(pcode, {})
                rows.append({
                    'interior': ilabel,
                    'size': slabel,
                    'paper': plabel,
                    'printing_name': f'print__{icode}__{scode}__{pcode}',
                    'paper_name': f'paper__{icode}__{scode}__{pcode}',
                    'printing': cell.get('printing', 0),
                    'paper_cost': cell.get('paper', 0),
                    'active': cell.get('active', True),
                })
    return rows


@staff_member_required
def pricing_book(request):
    """Edit the Book Printing price sheet (singleton)."""
    pricing = BookPrintingPricing.load()

    if request.method == 'POST':
        updated = 0
        # The client-facing page is deliberately limited to the spreadsheet
        # rates supplied in book.xlsx.  Legacy add-ons are not shown here.
        matrix = {}
        components = {}
        for icode, _il in BOOK_MATRIX_INTERIORS:
            for scode, _sl in BOOK_MATRIX_SIZES:
                for pcode, _pl in BOOK_MATRIX_PAPERS:
                    printing_field = f'print__{icode}__{scode}__{pcode}'
                    paper_field = f'paper__{icode}__{scode}__{pcode}'
                    if printing_field not in request.POST or paper_field not in request.POST:
                        continue
                    try:
                        printing = Decimal(request.POST.get(printing_field, '').strip() or '0')
                        paper_cost = Decimal(request.POST.get(paper_field, '').strip() or '0')
                    except (InvalidOperation, TypeError, ValueError):
                        continue
                    components.setdefault(icode, {}).setdefault(scode, {})[pcode] = {
                        'printing': float(printing),
                        'paper': float(paper_cost),
                        'active': True,
                    }
                    matrix.setdefault(icode, {}).setdefault(scode, {})[pcode] = float(printing + paper_cost)
        if matrix:
            if matrix != pricing.page_price_matrix:
                updated += 1
            pricing.page_price_matrix = matrix
            if components != pricing.page_price_components:
                updated += 1
            pricing.page_price_components = components

        pricing.save()
        messages.success(request, f'Book printing prices saved. {updated} value(s) updated.')
        return redirect('services:pricing_book')

    return render(request, 'pricing_manager/book_edit.html', {
        'pricing': pricing,
        'spreadsheet_rows': _build_spreadsheet_rows(pricing.page_price_components or {}),
    })
