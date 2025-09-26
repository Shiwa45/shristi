# apps/services/views_product_types.py
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from .models_product_types import BookPrintingQuote, BusinessCardQuote, BrochureQuote, ChildrenBookQuote
from .models import Product


def book_printing_quote_view(request, product_slug):
    """Book printing quote form and calculator"""
    product = get_object_or_404(Product, slug=product_slug, is_active=True)
    
    if request.method == 'POST':
        # Create quote from form data
        quote = BookPrintingQuote(
            quantity=int(request.POST.get('quantity', 100)),
            book_size=request.POST.get('book_size', 'A5'),
            page_count=int(request.POST.get('page_count', 100)),
            inner_paper=request.POST.get('inner_paper', '70gsm_offset'),
            inner_printing=request.POST.get('inner_printing', 'bw'),
            cover_paper=request.POST.get('cover_paper', '250gsm_art'),
            cover_printing=request.POST.get('cover_printing', 'color_4_0'),
            binding_type=request.POST.get('binding_type', 'perfect_binding'),
            cover_finish=request.POST.get('cover_finish', 'matte_lam'),
            design_service=request.POST.get('design_service', 'none'),
            isbn_service=bool(request.POST.get('isbn_service')),
            barcode_service=bool(request.POST.get('barcode_service')),
            copyright_service=bool(request.POST.get('copyright_service')),
            customer_name=request.POST.get('customer_name', ''),
            customer_email=request.POST.get('customer_email', ''),
            customer_phone=request.POST.get('customer_phone', ''),
        )
        quote.save()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # AJAX request - return JSON
            pricing = quote.calculate_price()
            return JsonResponse({
                'success': True,
                'unit_price': pricing['unit_price'],
                'total_price': pricing['total_price'],
                'quantity': pricing['quantity'],
                'discount_percent': pricing['discount_percent'],
                'quote_id': quote.id
            })
        else:
            messages.success(request, f'Quote generated! Total: ₹{quote.total_price:,.2f}')
            return redirect('services:product_detail', slug=product_slug)
    
    # GET request - show form
    context = {
        'product': product,
        'quote_form': BookPrintingQuote(),
    }
    return render(request, 'services/quotes/book_printing.html', context)


def business_card_quote_view(request, product_slug):
    """Business card quote form and calculator"""
    product = get_object_or_404(Product, slug=product_slug, is_active=True)
    
    if request.method == 'POST':
        quote = BusinessCardQuote(
            quantity=int(request.POST.get('quantity', 500)),
            card_size=request.POST.get('card_size', 'standard'),
            paper_type=request.POST.get('paper_type', '300gsm_art'),
            printing_sides=request.POST.get('printing_sides', 'double'),
            finishing=request.POST.get('finishing', 'matte_lam'),
            design_service=request.POST.get('design_service', 'none'),
            customer_name=request.POST.get('customer_name', ''),
            customer_email=request.POST.get('customer_email', ''),
            customer_phone=request.POST.get('customer_phone', ''),
        )
        quote.save()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            pricing = quote.calculate_price()
            return JsonResponse({
                'success': True,
                'unit_price': pricing['unit_price'],
                'total_price': pricing['total_price'],
                'quantity': pricing['quantity'],
                'discount_percent': pricing['discount_percent'],
                'quote_id': quote.id
            })
        else:
            messages.success(request, f'Quote generated! Total: ₹{quote.total_price:,.2f}')
            return redirect('services:product_detail', slug=product_slug)
    
    context = {
        'product': product,
        'quote_form': BusinessCardQuote(),
    }
    return render(request, 'services/quotes/business_cards.html', context)


def brochure_quote_view(request, product_slug):
    """Brochure/flyer quote form and calculator"""
    product = get_object_or_404(Product, slug=product_slug, is_active=True)
    
    if request.method == 'POST':
        quote = BrochureQuote(
            quantity=int(request.POST.get('quantity', 500)),
            size=request.POST.get('size', 'A4'),
            paper_type=request.POST.get('paper_type', '170gsm_art'),
            folding=request.POST.get('folding', 'tri_fold'),
            printing_sides=request.POST.get('printing_sides', 'double'),
            finishing=request.POST.get('finishing', 'matte_lam'),
            customer_name=request.POST.get('customer_name', ''),
            customer_email=request.POST.get('customer_email', ''),
            customer_phone=request.POST.get('customer_phone', ''),
        )
        quote.save()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            pricing = quote.calculate_price()
            return JsonResponse({
                'success': True,
                'unit_price': pricing['unit_price'],
                'total_price': pricing['total_price'],
                'quantity': pricing['quantity'],
                'discount_percent': pricing['discount_percent'],
                'quote_id': quote.id
            })
        else:
            messages.success(request, f'Quote generated! Total: ₹{quote.total_price:,.2f}')
            return redirect('services:product_detail', slug=product_slug)
    
    context = {
        'product': product,
        'quote_form': BrochureQuote(),
    }
    return render(request, 'services/quotes/brochures.html', context)


def children_book_quote_view(request, product_slug):
    """Children's book quote form and calculator"""
    product = get_object_or_404(Product, slug=product_slug, is_active=True)
    
    if request.method == 'POST':
        quote = ChildrenBookQuote(
            quantity=int(request.POST.get('quantity', 100)),
            book_size=request.POST.get('book_size', 'A5'),
            page_count=int(request.POST.get('page_count', 24)),
            age_group=request.POST.get('age_group', 'preschool'),
            inner_paper=request.POST.get('inner_paper', '80gsm_offset'),
            inner_printing=request.POST.get('inner_printing', 'full_color'),
            cover_paper=request.POST.get('cover_paper', '300gsm_art'),
            binding_type=request.POST.get('binding_type', 'saddle_stitch'),
            cover_finish=request.POST.get('cover_finish', 'matte_lam'),
            # Special features
            rounded_corners=bool(request.POST.get('rounded_corners')),
            scratch_sniff=bool(request.POST.get('scratch_sniff')),
            pop_up_elements=bool(request.POST.get('pop_up_elements')),
            texture_pages=bool(request.POST.get('texture_pages')),
            glow_in_dark=bool(request.POST.get('glow_in_dark')),
            sound_module=bool(request.POST.get('sound_module')),
            # Services
            design_service=request.POST.get('design_service', 'none'),
            writing_service=request.POST.get('writing_service', 'none'),
            publishing_service=request.POST.get('publishing_service', 'none'),
            # Customer info
            customer_name=request.POST.get('customer_name', ''),
            customer_email=request.POST.get('customer_email', ''),
            customer_phone=request.POST.get('customer_phone', ''),
            book_title=request.POST.get('book_title', ''),
        )
        quote.save()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            pricing = quote.calculate_price()
            return JsonResponse({
                'success': True,
                'unit_price': pricing['unit_price'],
                'total_price': pricing['total_price'],
                'quantity': pricing['quantity'],
                'discount_percent': pricing['discount_percent'],
                'quote_id': quote.id
            })
        else:
            messages.success(request, f'Children\'s Book Quote generated! Total: ₹{quote.total_price:,.2f}')
            return redirect('services:product_detail', slug=product_slug)
    
    context = {
        'product': product,
        'quote_form': ChildrenBookQuote(),
    }
    return render(request, 'services/quotes/children_books.html', context)


@require_POST
def ajax_calculate_price(request):
    """AJAX endpoint for real-time price calculation"""
    product_type = request.POST.get('product_type')
    
    try:
        if product_type == 'book':
            quote = BookPrintingQuote(
                quantity=int(request.POST.get('quantity', 100)),
                book_size=request.POST.get('book_size', 'A5'),
                page_count=int(request.POST.get('page_count', 100)),
                inner_paper=request.POST.get('inner_paper', '70gsm_offset'),
                inner_printing=request.POST.get('inner_printing', 'bw'),
                cover_paper=request.POST.get('cover_paper', '250gsm_art'),
                cover_printing=request.POST.get('cover_printing', 'color_4_0'),
                binding_type=request.POST.get('binding_type', 'perfect_binding'),
                cover_finish=request.POST.get('cover_finish', 'matte_lam'),
                design_service=request.POST.get('design_service', 'none'),
                isbn_service=bool(request.POST.get('isbn_service')),
                barcode_service=bool(request.POST.get('barcode_service')),
                copyright_service=bool(request.POST.get('copyright_service')),
            )
        elif product_type == 'business_card':
            quote = BusinessCardQuote(
                quantity=int(request.POST.get('quantity', 500)),
                card_size=request.POST.get('card_size', 'standard'),
                paper_type=request.POST.get('paper_type', '300gsm_art'),
                printing_sides=request.POST.get('printing_sides', 'double'),
                finishing=request.POST.get('finishing', 'matte_lam'),
                design_service=request.POST.get('design_service', 'none'),
            )
        elif product_type == 'brochure':
            quote = BrochureQuote(
                quantity=int(request.POST.get('quantity', 500)),
                size=request.POST.get('size', 'A4'),
                paper_type=request.POST.get('paper_type', '170gsm_art'),
                folding=request.POST.get('folding', 'tri_fold'),
                printing_sides=request.POST.get('printing_sides', 'double'),
                finishing=request.POST.get('finishing', 'matte_lam'),
            )
        elif product_type == 'children_book':
            quote = ChildrenBookQuote(
                quantity=int(request.POST.get('quantity', 100)),
                book_size=request.POST.get('book_size', 'A5'),
                page_count=int(request.POST.get('page_count', 24)),
                age_group=request.POST.get('age_group', 'preschool'),
                inner_paper=request.POST.get('inner_paper', '80gsm_offset'),
                inner_printing=request.POST.get('inner_printing', 'full_color'),
                cover_paper=request.POST.get('cover_paper', '300gsm_art'),
                binding_type=request.POST.get('binding_type', 'saddle_stitch'),
                cover_finish=request.POST.get('cover_finish', 'matte_lam'),
                # Special features
                rounded_corners=bool(request.POST.get('rounded_corners')),
                scratch_sniff=bool(request.POST.get('scratch_sniff')),
                pop_up_elements=bool(request.POST.get('pop_up_elements')),
                texture_pages=bool(request.POST.get('texture_pages')),
                glow_in_dark=bool(request.POST.get('glow_in_dark')),
                sound_module=bool(request.POST.get('sound_module')),
                # Services
                design_service=request.POST.get('design_service', 'none'),
                writing_service=request.POST.get('writing_service', 'none'),
                publishing_service=request.POST.get('publishing_service', 'none'),
            )
        else:
            return JsonResponse({'success': False, 'error': 'Invalid product type'})
        
        pricing = quote.calculate_price()
        return JsonResponse({
            'success': True,
            'unit_price': pricing['unit_price'],
            'total_price': pricing['total_price'],
            'quantity': pricing['quantity'],
            'discount_percent': pricing['discount_percent'],
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})