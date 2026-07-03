"""Canonical product pricing engine — the single source of truth.

Used by:
  - quote estimates (apps.orders.views.quote_detail)
  - the public price API (/services/api/price-quote/)

Two engines, dispatched by category:

  Option-based products (stationery, marketing material, paper boxes):
    unit      = base_price + Σ(selected option add-ons)   [ProductFieldOption rows]
    gross     = unit × qty
    discount  = best QuantityTier slab (highest satisfied min_quantity wins)
    total     = (gross − discount) × 1.18 (GST)

  Book printing (per-page engine, rates from the BookPrintingPricing sheet):
    cost/book = interior(per-page) + size + paper + binding + cover finish
    gross     = cost/book × qty + design services + ISBN
    discount  = editable bulk slabs (bulk_qty_1/2, bulk_disc_1/2)
    total     = (gross − discount) × 1.18 (GST)

All rates are editable in the Pricing Manager (/services/manage/pricing/).
"""
from decimal import Decimal, InvalidOperation

GST_RATE = Decimal('0.18')
_TWO = Decimal('0.01')


def _q(value):
    return Decimal(value).quantize(_TWO)


def _to_int(value):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _pct_display(pct):
    """Decimal('10.00') -> 10, Decimal('7.50') -> 7.5 — clean template display."""
    f = float(pct)
    return int(f) if f == int(f) else f


def get_tier_discount(product, quantity):
    """Return the best (highest satisfied min_quantity) active tier, or None."""
    best = None
    for tier in product.qty_tiers.filter(is_active=True).order_by('min_quantity'):
        if quantity >= tier.min_quantity:
            best = tier
    return best


def calculate_option_pricing(product, specs, quantity):
    """Price an option-based product from its ProductFieldOption rows."""
    base = Decimal(str(product.base_price or 0))
    specs = specs or {}
    qty = max(int(quantity or 1), 1)

    # {field_name: {value: price_modifier}} lookup
    modifier_lookup = {}
    for field in product.form_fields.filter(is_active=True):
        opt_map = {}
        for opt in field.get_options():
            try:
                opt_map[str(opt.get('value'))] = Decimal(str(opt.get('price_modifier', 0) or 0))
            except (TypeError, ValueError, InvalidOperation):
                opt_map[str(opt.get('value'))] = Decimal('0')
        modifier_lookup[field.field_name] = opt_map

    modifiers = []
    modifier_total = Decimal('0')
    for field_name, value in specs.items():
        opt_map = modifier_lookup.get(field_name)
        if not opt_map:
            continue
        mod = opt_map.get(str(value), Decimal('0'))
        if mod:
            modifiers.append({'label': str(value), 'amount': _q(mod)})
            modifier_total += mod

    unit_price = base + modifier_total
    gross_subtotal = unit_price * qty

    tier = get_tier_discount(product, qty)
    discount_pct = Decimal(tier.discount_percent) if tier else Decimal('0')
    discount = gross_subtotal * discount_pct / Decimal('100')

    taxable = gross_subtotal - discount
    tax = taxable * GST_RATE
    total = taxable + tax

    return {
        'is_book': False,
        'base_price': _q(base),
        'modifiers': modifiers,
        'unit_price': _q(unit_price),
        'quantity': qty,
        'gross_subtotal': _q(gross_subtotal),
        'discount': _q(discount),
        'discount_pct': _pct_display(discount_pct),
        'subtotal': _q(taxable),   # taxable base — used for grand totals
        'tax': _q(tax),
        'total': _q(total),
    }


def calculate_book_pricing(product, specs, quantity):
    """Price a Book Printing product with the per-page engine.

    Mirrors the live calculator on book_printing_detail.html exactly; both read
    the same BookPrintingPricing sheet, so they cannot drift on rates.
    """
    from .models import BookPrintingPricing

    bp = BookPrintingPricing.load()
    specs = specs or {}
    qty = max(int(quantity or 1), 1)

    page_count = _to_int(specs.get('page_count'))
    bw_pages = _to_int(specs.get('bw_page_count'))
    color_pages = _to_int(specs.get('color_page_count'))
    total_pages = page_count if page_count else (bw_pages + color_pages)

    components = []
    interior = specs.get('interior_color')
    interior_cost = Decimal('0')
    if interior == 'bw_standard':
        pages = bw_pages if bw_pages > 0 else total_pages
        interior_cost = pages * bp.color_bw_standard_per_page
        components.append({'label': f'Interior: B&W Standard — {pages} pg × ₹{bp.color_bw_standard_per_page}', 'amount': interior_cost})
    elif interior == 'bw_premium':
        pages = bw_pages if bw_pages > 0 else total_pages
        interior_cost = pages * bp.color_bw_premium_per_page
        components.append({'label': f'Interior: B&W Premium — {pages} pg × ₹{bp.color_bw_premium_per_page}', 'amount': interior_cost})
    elif interior == 'color_standard':
        pages = color_pages if color_pages > 0 else total_pages
        interior_cost = pages * bp.color_standard_per_page
        components.append({'label': f'Interior: Colour Standard — {pages} pg × ₹{bp.color_standard_per_page}', 'amount': interior_cost})
    elif interior == 'color_premium':
        pages = color_pages if color_pages > 0 else total_pages
        interior_cost = pages * bp.color_premium_per_page
        components.append({'label': f'Interior: Colour Premium — {pages} pg × ₹{bp.color_premium_per_page}', 'amount': interior_cost})
    elif interior == 'combine_color':
        interior_cost = (bw_pages * bp.combine_bw_per_page) + (color_pages * bp.combine_color_per_page)
        components.append({'label': f'Interior: Combined — {bw_pages} B&W + {color_pages} colour pg', 'amount': interior_cost})

    size_map = {'a4': bp.size_a4, 'letter': bp.size_letter, 'executive': bp.size_executive, 'a5': bp.size_a5}
    paper_map = {'75gsm': bp.paper_75gsm, '100gsm': bp.paper_100gsm, '100gsm_art': bp.paper_100gsm_art, '130gsm_art': bp.paper_130gsm_art}
    binding_map = {'saddle_stitch': bp.binding_saddle_stitch, 'spiral_binding': bp.binding_spiral, 'paperback_perfect': bp.binding_paperback_perfect, 'hardcover': bp.binding_hardcover}
    finish_map = {'matte': bp.cover_matte, 'glossy': bp.cover_glossy}

    def _add(label, mapping, key):
        val = mapping.get(key)
        if val is None:
            return Decimal('0')
        components.append({'label': label, 'amount': Decimal(val)})
        return Decimal(val)

    size_cost = _add(f"Size: {specs.get('book_size', '')}", size_map, specs.get('book_size'))
    paper_cost = _add(f"Paper: {specs.get('paper_type', '')}", paper_map, specs.get('paper_type'))
    binding_cost = _add(f"Binding: {specs.get('binding_type', '')}", binding_map, specs.get('binding_type'))
    finish_cost = _add(f"Cover finish: {specs.get('cover_finish', '')}", finish_map, specs.get('cover_finish'))

    cost_per_book = interior_cost + size_cost + paper_cost + binding_cost + finish_cost

    design_cost = Decimal('0')
    if specs.get('cover_page_design') == 'yes':
        design_cost += bp.cover_design_price
    if specs.get('inner_page_design') == 'yes':
        design_cost += total_pages * bp.inner_page_design_per_page
    isbn_cost = bp.isbn_price if specs.get('isbn_allocation') == 'assign_isbn' else Decimal('0')

    books_subtotal = cost_per_book * qty
    gross_subtotal = books_subtotal + design_cost + isbn_cost

    # Editable bulk slabs — highest satisfied threshold wins
    slabs = [(bp.bulk_qty_1, bp.bulk_disc_1), (bp.bulk_qty_2, bp.bulk_disc_2)]
    satisfied = [(q_, d_) for q_, d_ in slabs if q_ and qty >= q_]
    discount_pct = Decimal(max(satisfied, key=lambda t: t[0])[1]) if satisfied else Decimal('0')

    discount = gross_subtotal * discount_pct / Decimal('100')
    after_discount = gross_subtotal - discount
    tax = after_discount * GST_RATE
    total = after_discount + tax

    return {
        'is_book': True,
        'components': [{'label': c['label'], 'amount': _q(c['amount'])} for c in components],
        'cost_per_book': _q(cost_per_book),
        'quantity': qty,
        'books_subtotal': _q(books_subtotal),
        'design_cost': _q(design_cost),
        'isbn_cost': _q(isbn_cost),
        'gross_subtotal': _q(gross_subtotal),
        'discount': _q(discount),
        'discount_pct': _pct_display(discount_pct),
        'subtotal': _q(after_discount),   # taxable base — used for grand totals
        'tax': _q(tax),
        'total': _q(total),
    }


def calculate_product_pricing(product, specs, quantity):
    """Dispatch to the right engine by category. Returns None without a product."""
    if product is None:
        return None
    if product.category and product.category.slug == 'book-printing':
        return calculate_book_pricing(product, specs, quantity)
    return calculate_option_pricing(product, specs, quantity)


def serialize_pricing(pricing):
    """Decimal-safe copy of a pricing dict for JsonResponse."""
    def conv(v):
        if isinstance(v, Decimal):
            return str(v)
        if isinstance(v, list):
            return [conv(x) for x in v]
        if isinstance(v, dict):
            return {k: conv(x) for k, x in v.items()}
        return v
    return conv(pricing)
