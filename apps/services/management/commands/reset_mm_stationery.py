"""
Reset Marketing Material and Stationery products.
Deletes all existing products in those two categories and re-creates
them from scratch with the correct form fields per products.md.
Book Printing and Paper Boxes are NOT touched.
"""
import json
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from apps.services.models import ServiceCategory, StaticProduct, ProductFormField


def opts(*labels):
    return json.dumps([{'value': slugify(l), 'label': l, 'price_modifier': 0} for l in labels])


def field(name, label, options_json, order, condition=None):
    d = {
        'field_name': name,
        'field_label': label,
        'field_type': 'select',
        'options': options_json,
        'order': order,
        'section_order': 0,
        'field_section': 'product_specs',
        'is_required': True,
        'is_active': True,
    }
    if condition:
        d['show_condition'] = json.dumps(condition)
    return d


# ── Marketing Material ──────────────────────────────────────────────────────

MARKETING_MATERIAL = [
    {
        'name': 'Brochures',
        'slug': 'brochures',
        'fields': [
            field('brochure_type', 'Brochure Type',
                  opts('Bi-fold Brochure', 'Tri-fold Brochure'), 0),
            field('open_size', 'Open Size',
                  opts('A-4', 'A-5'), 1),
            field('paper_material', 'Paper Material',
                  opts('300 gsm Matt', '300 Gsm Gloss'), 2),
            field('lamination', 'Lamination',
                  opts('Matt Lamination', 'Gloss Lamination'), 3),
            field('qty', 'Qty.',
                  opts('100', '200', '300', '400', '500'), 4),
        ],
    },
    {
        'name': 'Button Badges',
        'slug': 'button-badges',
        'fields': [
            field('size', 'Size',
                  opts('40 mm Dia (Small Size)', '60 mm Dia (Big Size)'), 0),
            field('qty', 'Qty.',
                  opts('100', '200', '300', '400', '500'), 1),
        ],
    },
    {
        'name': 'Certificates',
        'slug': 'certificates',
        'fields': [
            field('size', 'Size',
                  opts('A-5 (5.8 x 8.3 inches)', 'A-4 (11.7 x 8.3 inches)', 'A-3 (11.7 x 16.5 inches)'), 0),
            field('paper_material', 'Paper Material',
                  opts('350 Gsm Art paper', '300 Gsm Art paper'), 1),
            field('qty', 'Qty.',
                  opts('100', '200', '300', '400', '500'), 2),
        ],
    },
    {
        'name': 'Custom Roll Up Standees',
        'slug': 'custom-roll-up-standees',
        'fields': [
            field('size', 'Size',
                  opts('2 feet x 5 feet', '2.5 feet x 6 feet'), 0),
            field('paper_material', 'Paper Material',
                  opts('Premium Flex', 'Banner Media'), 1),
            field('lamination', 'Lamination',
                  opts('Matt', 'Glossy'), 2),
            field('qty', 'Qty.',
                  opts('1', '2', '3', '4', '5'), 3),
        ],
    },
    {
        'name': 'Danglers',
        'slug': 'danglers',
        'fields': [
            field('shape', 'Select Shape',
                  opts('Normal', 'Classic', 'Round', 'Custom/Any Other'), 0),
            field('size', 'Size',
                  opts('3x5', '5x5', '8x8', 'A-5', 'A-4', 'Custom Size'), 1),
            field('paper_material', 'Paper Material',
                  opts('250 Gsm paper', '300 Gsm paper'), 2),
            field('lamination', 'Lamination',
                  opts('Matt Lamination', 'Gloss Lamination'), 3),
            field('qty', 'Qty.',
                  opts('100', '200', '300', '400', '500'), 4),
        ],
    },
    {
        'name': 'Flyers & Leaflets',
        'slug': 'flyers-leaflets',
        'fields': [
            field('size', 'Size',
                  opts('A-5', 'A-4', 'A-6', 'A-7', 'A-3', 'DL Size'), 0),
            field('printing_colour', 'Printing Colour',
                  opts('Single Colour', 'Four Colour'), 1),
            field('paper_material', 'Paper Material',
                  opts('75 gsm Paper', '100 gsm Paper', '130 Gsm Art Paper',
                       '170 Gsm Art paper', '250 Gsm Art paper'), 2),
            field('printing_side', 'Printing Side',
                  opts('Single Side', 'Both Side'), 3),
            field('qty', 'Qty.',
                  opts('100', '200', '300', '400', '500'), 4),
        ],
    },
    {
        'name': 'Poster',
        'slug': 'poster',
        'fields': [
            field('size', 'Size',
                  opts('A-3', 'A-4'), 0),
            field('paper_quality', 'Paper Quality',
                  opts('170 Gsm', '250 Gsm', '300 Gsm'), 1),
            field('lamination', 'Lamination',
                  opts('None', 'Matt Lamination', 'Gloss Lamination'), 2),
            field('printed_sides', 'Printed Sides',
                  opts('Single Side'), 3),
            field('glued_edges', 'Glued Edges',
                  opts('None', '0.5 inch Wide Glued Edges'), 4),
            field('corner_style', 'Corner Style',
                  opts('Straight Corners'), 5),
            field('qty', 'Qty.',
                  opts('100', '200', '300', '400', '500'), 6),
        ],
    },
    {
        'name': 'Tent Cards',
        'slug': 'tent-cards',
        'fields': [
            field('size', 'Size',
                  opts('A-5 (5.8 x 8.3 inches) Portrait',
                       'A-4 (11.7 x 8.3 inches) Landscape',
                       'A-5 (8.3 x 5.8 inches) Landscape',
                       'A-6 (4.1 x 5.8 inches) Portrait',
                       'A-6 (5.8 x 4.1 inches) Landscape'), 0),
            field('paper_material', 'Paper Material',
                  opts('250 Gsm Art paper', '300 Gsm Art paper'), 1),
            field('qty', 'Qty.',
                  opts('100', '200', '300', '400', '500'), 2),
        ],
    },
]


# ── Stationery ──────────────────────────────────────────────────────────────

def cond_in(trigger_field, *values):
    return {'field': trigger_field, 'value': list(values), 'operator': 'in'}


def cond_eq(trigger_field, value):
    return {'field': trigger_field, 'value': value}


STATIONERY = [
    {
        'name': 'Bill Book',
        'slug': 'bill-book',
        'fields': [
            field('bill_book_type', 'Bill Book Type',
                  opts('Black & White', 'Colour'), 0),
            field('book_type', 'Book Type',
                  opts('Original + Duplicate', 'Original + 1 Duplicate',
                       'Original + 2 Duplicate', 'Original + 3 Duplicate'), 1),
            field('first_dup_colour', '1st Duplicate Sheet Colour',
                  opts('Pink', 'Yellow', 'Light Green', 'Light Blue'), 2),
            field('second_dup_colour', '2nd Duplicate Sheet Colour',
                  opts('Pink', 'Yellow', 'Light Green', 'Light Blue'), 3),
            field('third_dup_colour', '3rd Duplicate Sheet Colour',
                  opts('Pink', 'Yellow', 'Light Green', 'Light Blue'), 4),
            field('invoice_numbering', 'Invoice Numbering',
                  opts('With Invoice Number', 'Without Invoice Number'), 5),
            field('qty', 'Qty.',
                  opts('2', '5', '10', '15', '20'), 6),
        ],
    },
    {
        'name': 'Business Cards',
        'slug': 'business-cards',
        'fields': [
            # Type selector
            field('card_type', 'Card Type',
                  opts('Non Tear Business Cards', 'Raised Foil Business Cards',
                       'Raised Spot-UV Business Card', 'Standard Business Card',
                       'Texture Business Card'), 0),

            # Non Tear fields
            field('nt_printing_side', 'Printing Side',
                  opts('Front Side', 'Both Side'), 1,
                  cond_eq('card_type', 'non-tear-business-cards')),
            field('nt_paper_quality', 'Paper Quality',
                  opts('Non Tearable (250 micron)'), 2,
                  cond_eq('card_type', 'non-tear-business-cards')),

            # Raised Foil fields
            field('rf_printing_side', 'Printing Side',
                  opts('Front Side', 'Both Side'), 3,
                  cond_eq('card_type', 'raised-foil-business-cards')),
            field('rf_foil_colour', 'Foil Colour',
                  opts('Gold', 'Silver', 'Rose Gold'), 4,
                  cond_eq('card_type', 'raised-foil-business-cards')),
            field('rf_lamination', 'Lamination',
                  opts('None', 'Matt Lamnation', 'Gloss Lamnation'), 5,
                  cond_eq('card_type', 'raised-foil-business-cards')),

            # Raised Spot-UV fields
            field('rs_printing_side', 'Printing Side',
                  opts('Front Side', 'Both Side'), 6,
                  cond_eq('card_type', 'raised-spot-uv-business-card')),
            field('rs_raised_spot_uv', 'Raised Spot-UV',
                  opts('1 side Spot-UV'), 7,
                  cond_eq('card_type', 'raised-spot-uv-business-card')),
            field('rs_lamination', 'Lamination',
                  opts('None', 'Matt Lamnation', 'Gloss Lamnation'), 8,
                  cond_eq('card_type', 'raised-spot-uv-business-card')),

            # Standard Business Card fields
            field('st_printing_side', 'Printing Side',
                  opts('Front Side', 'Back Side'), 9,
                  cond_eq('card_type', 'standard-business-card')),
            field('st_corner_style', 'Corner Style',
                  opts('Straight Corners', 'Rounded Corners'), 10,
                  cond_eq('card_type', 'standard-business-card')),
            field('st_lamination', 'Lamination',
                  opts('None', 'Matt Lamnation', 'Gloss Lamnation'), 11,
                  cond_eq('card_type', 'standard-business-card')),

            # Texture Business Card fields
            field('tx_paper_materials', 'Paper Materials',
                  opts('Fine Needle Point', 'Rendezvous Hi Print', 'Contrast Ivory',
                       'Contrast N White', 'Contrast Laid White', 'Mermaid Linen',
                       'Leathack 85 White', 'Leathack 205 White'), 12,
                  cond_eq('card_type', 'texture-business-card')),
            field('tx_printing_side', 'Printing Side',
                  opts('Front Side', 'Back Side'), 13,
                  cond_eq('card_type', 'texture-business-card')),

            # Qty (common to all types)
            field('qty', 'Qty.',
                  opts('200', '300', '400', '500', '600', '700', '800', '900', '1000'), 14),
        ],
    },
    {
        'name': 'Envelopes',
        'slug': 'envelopes',
        'fields': [
            field('envelope_size', 'Size',
                  opts('Envelopes 10x 4.5', 'Envelopes A-5', 'Envelopes A-6'), 0),
            field('paper_type', 'Paper Type',
                  opts('80 Gsm', '100 gsm', '120 gsm'), 1),
            field('printing', 'Printing',
                  opts('Black & White', 'Colour'), 2),
            field('qty', 'Qty.',
                  opts('100', '200', '300', '400', '500', '1000', '2000', '3000'), 3),
        ],
    },
    {
        'name': 'ID Cards & Lanyards',
        'slug': 'id-cards-lanyards',
        'fields': [
            field('id_card_type', 'Type',
                  opts('Event ID Cards', 'PVC ID Cards', 'Multicolour Lanyards'), 0),

            # Event ID Card & PVC fields
            field('ic_id_card_finish', 'ID Card Finish',
                  opts('Matt Lamination', 'Gloosy Lamination'), 1,
                  cond_in('id_card_type', 'event-id-cards', 'pvc-id-cards')),
            field('ic_orientation', 'Orientation',
                  opts('Portrait', 'Landscape'), 2,
                  cond_in('id_card_type', 'event-id-cards', 'pvc-id-cards')),
            field('ic_print_location', 'Print Location',
                  opts('Front Side', 'Back Side'), 3,
                  cond_in('id_card_type', 'event-id-cards', 'pvc-id-cards')),

            # Multicolour Lanyards fields
            field('ml_attachment_type', 'Attachment Type',
                  opts('SD Lever Hook'), 4,
                  cond_eq('id_card_type', 'multicolour-lanyards')),

            field('qty', 'Qty.',
                  opts('100', '200', '300', '400', '500', '1000', '2000', '3000'), 5),
        ],
    },
    {
        'name': 'Letter Head',
        'slug': 'letter-head',
        'fields': [
            field('letterhead_type', 'Type',
                  opts('Standard Letter Head', 'Corporate Letter Head'), 0),
            field('size', 'Size',
                  opts('A-4'), 1),
            field('paper_type', 'Paper Type',
                  opts('JK Excecl Bond Paper 100 Gsm', 'DO Paper 100 Gsm'), 2),
            field('printed_sides', 'Printed Sides',
                  opts('Single Side', 'Both Side'), 3,
                  cond_eq('letterhead_type', 'standard-letter-head')),
            # Combined qty for both types
            field('qty', 'Qty.',
                  opts('200', '300', '400', '500', '600', '700', '800', '900',
                       '1000', '1500', '2000'), 4),
        ],
    },
    {
        'name': 'Sticker',
        'slug': 'sticker',
        'fields': [
            field('sticker_type', 'Sticker Type',
                  opts('Address Labels', 'Barcode Labels', 'Circle Stickers',
                       'Custom Stickers', 'Product Labels', 'Rectangle Stickers',
                       'Square Stickers', 'Warning Labels'), 0),

            # ── Address Labels
            field('addr_material', 'Material',
                  opts('Paper Sticker (Chromo)', 'PVC Vinyl', 'PVC Transparent Vinyl'), 1,
                  cond_eq('sticker_type', 'address-labels')),
            field('addr_shape', 'Shape',
                  opts('Rectangle', 'Rectangle with Rounded Corner', 'Square',
                       'Square with Rounded Corner', 'Circle', 'Oval', 'Custom/Any Shape'), 2,
                  cond_eq('sticker_type', 'address-labels')),
            field('addr_size', 'Size',
                  opts('2x1', '2x2', '2x3', '3x2', '3x3', '4x3', '4x4',
                       '5x2', '5x3', '6x3', '6x4', 'Custom Size'), 3,
                  cond_eq('sticker_type', 'address-labels')),

            # ── Barcode Labels
            field('bc_material', 'Material',
                  opts('Paper Sticker (Chromo)', 'PVC Vinyl'), 4,
                  cond_eq('sticker_type', 'barcode-labels')),
            field('bc_shape', 'Shape',
                  opts('Rectangle', 'Rectangle with Rounded Corner', 'Square',
                       'Square with Rounded Corner', 'Circle', 'Oval', 'Custom/Any Shape'), 5,
                  cond_eq('sticker_type', 'barcode-labels')),
            field('bc_size', 'Size',
                  opts('2x1', '2x2', '2x3', '3x2', '3x3', '4x3', '4x4',
                       '5x2', '5x3', '6x3', '6x4', 'Custom Size'), 6,
                  cond_eq('sticker_type', 'barcode-labels')),

            # ── Circle Stickers
            field('ci_material', 'Material',
                  opts('Paper Sticker (Chromo)', 'PVC Vinyl', 'PVC Transparent Vinyl',
                       'Dome Stickers', 'Front Transparent'), 7,
                  cond_eq('sticker_type', 'circle-stickers')),
            field('ci_size', 'Size',
                  opts('2x2', '3x3', '4x4', '5x5'), 8,
                  cond_eq('sticker_type', 'circle-stickers')),

            # ── Custom Stickers
            field('cs_material', 'Material',
                  opts('Paper Sticker (Chromo)', 'PVC Vinyl', 'PVC Transparent Vinyl',
                       'Dome Stickers', 'Front Transparent'), 9,
                  cond_eq('sticker_type', 'custom-stickers')),
            field('cs_shape', 'Shape',
                  opts('Rectangle', 'Rectangle with Rounded Corner', 'Square',
                       'Square with Rounded Corner', 'Circle', 'Oval', 'Custom/Any Shape'), 10,
                  cond_eq('sticker_type', 'custom-stickers')),
            field('cs_size', 'Size',
                  opts('2x1', '2x3', '3x2', '3x3', '4x3', '4x4',
                       '5x2', '5x3', '6x3', '6x4'), 11,
                  cond_eq('sticker_type', 'custom-stickers')),

            # ── Product Labels
            field('pl_material', 'Material',
                  opts('Paper Sticker (Chromo)', 'PVC Vinyl', 'PVC Transparent Vinyl'), 12,
                  cond_eq('sticker_type', 'product-labels')),
            field('pl_shape', 'Shape',
                  opts('Rectangle', 'Rectangle with Rounded Corner', 'Square',
                       'Square with Rounded Corner', 'Circle', 'Oval', 'Custom/Any Shape'), 13,
                  cond_eq('sticker_type', 'product-labels')),
            field('pl_size', 'Size',
                  opts('2x1', '2x2', '2x3', '3x2', '3x3', '4x3', '4x4',
                       '5x2', '5x3', '6x3', '6x4', 'Custom Size'), 14,
                  cond_eq('sticker_type', 'product-labels')),

            # ── Rectangle Stickers
            field('rs_material', 'Material',
                  opts('Paper Sticker (Chromo)', 'PVC Vinyl', 'PVC Transparent Vinyl',
                       'Dome Stickers', 'Front Transparent'), 15,
                  cond_eq('sticker_type', 'rectangle-stickers')),
            field('rs_size', 'Size',
                  opts('2x1', '2x3', '3x2', '4x3', '5x2', '6x3', '6x4'), 16,
                  cond_eq('sticker_type', 'rectangle-stickers')),

            # ── Square Stickers
            field('sq_material', 'Material',
                  opts('Paper Sticker (Chromo)', 'PVC Vinyl', 'PVC Transparent Vinyl',
                       'Dome Stickers', 'Front Transparent'), 17,
                  cond_eq('sticker_type', 'square-stickers')),
            field('sq_size', 'Size',
                  opts('2x2', '3x3', '4x4', '5x5'), 18,
                  cond_eq('sticker_type', 'square-stickers')),

            # ── Warning Labels
            field('wl_material', 'Material',
                  opts('Paper Sticker (Chromo)', 'PVC Vinyl', 'PVC Transparent Vinyl'), 19,
                  cond_eq('sticker_type', 'warning-labels')),
            field('wl_shape', 'Shape',
                  opts('Rectangle', 'Rectangle with Rounded Corner', 'Square',
                       'Square with Rounded Corner', 'Circle', 'Oval', 'Custom/Any Shape'), 20,
                  cond_eq('sticker_type', 'warning-labels')),
            field('wl_size', 'Size',
                  opts('2x1', '2x2', '2x3', '3x2', '3x3', '4x3', '4x4',
                       '5x2', '5x3', '6x3', '6x4', 'Custom Size'), 21,
                  cond_eq('sticker_type', 'warning-labels')),

            # Common qty for all sticker types
            field('qty', 'Qty.',
                  opts('100', '200', '300', '400', '500', '1000', '2000', '3000'), 22),
        ],
    },
]


class Command(BaseCommand):
    help = 'Wipe and recreate Marketing Material & Stationery products from products.md spec'

    def handle(self, *args, **options):
        for cat_slug, products_data in [
            ('marketing-material', MARKETING_MATERIAL),
            ('stationery', STATIONERY),
        ]:
            cat = ServiceCategory.objects.get(slug=cat_slug)

            # Delete all existing products in this category
            deleted, _ = cat.static_products.all().delete()
            self.stdout.write(f'Deleted {deleted} rows from {cat_slug}')

            # Create fresh products
            for p_data in products_data:
                product = StaticProduct.objects.create(
                    category=cat,
                    name=p_data['name'],
                    slug=p_data['slug'],
                    is_active=True,
                    design_tool_enabled=False,
                    base_price=0,
                )
                for f_data in p_data['fields']:
                    ProductFormField.objects.create(
                        static_product=product,
                        field_name=f_data['field_name'],
                        field_label=f_data['field_label'],
                        field_type=f_data['field_type'],
                        options=f_data['options'],
                        order=f_data['order'],
                        section_order=f_data['section_order'],
                        field_section=f_data['field_section'],
                        is_required=f_data['is_required'],
                        is_active=f_data['is_active'],
                        show_condition=f_data.get('show_condition', ''),
                    )
                self.stdout.write(f'  Created: {product.name} ({len(p_data["fields"])} fields)')

        self.stdout.write(self.style.SUCCESS('Done.'))
