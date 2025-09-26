# apps/core/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Q

from .models import HomepageSlider, Page, ContactSubmission, Testimonial, FAQCategory, FAQ
from apps.services.models import ServiceCategory, Product


def home_view(request):
    """Homepage view with slider and featured products"""
    sliders = HomepageSlider.objects.filter(is_active=True).order_by('order')
    featured_products = Product.objects.filter(is_active=True, is_featured=True)[:6]
    design_enabled_products = Product.objects.filter(is_active=True, has_design_tool=True)[:6]
    service_categories = ServiceCategory.objects.filter(is_active=True).order_by('order')[:4]
    testimonials = Testimonial.objects.filter(is_active=True, is_featured=True).order_by('order')[:6]
    
    context = {
        'sliders': sliders,
        'featured_products': featured_products,
        'design_enabled_products': design_enabled_products,
        'service_categories': service_categories,
        'testimonials': testimonials,
    }
    return render(request, 'core/home.html', context)


def about_view(request):
    """About page view"""
    testimonials = Testimonial.objects.filter(is_active=True).order_by('order')[:8]
    stats = {
        'happy_customers': 1000,
        'projects_completed': 5000,
        'product_types': 50,
        'years_experience': 10,
    }
    
    context = {
        'testimonials': testimonials,
        'stats': stats,
    }
    return render(request, 'core/about.html', context)


def contact_view(request):
    """Contact page view"""
    # Get product if specified in query params (for product-specific inquiries)
    product_slug = request.GET.get('product')
    product = None
    if product_slug:
        try:
            product = Product.objects.get(slug=product_slug, is_active=True)
        except Product.DoesNotExist:
            pass
    
    faq_categories = FAQCategory.objects.filter(is_active=True)[:3]
    
    context = {
        'product': product,
        'faq_categories': faq_categories,
    }
    return render(request, 'core/contact.html', context)


@require_http_methods(["POST"])
def contact_submit_view(request):
    """Handle contact form submission"""
    try:
        # Get client IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        
        # Create contact submission
        submission = ContactSubmission.objects.create(
            name=request.POST.get('name', ''),
            email=request.POST.get('email', ''),
            phone=request.POST.get('phone', ''),
            subject=request.POST.get('subject', ''),
            message=request.POST.get('message', ''),
            ip_address=ip
        )
        
        # Send notification email to admin
        try:
            send_mail(
                subject=f'New Contact Form Submission: {submission.subject}',
                message=f'''
                New contact form submission:
                
                Name: {submission.name}
                Email: {submission.email}
                Phone: {submission.phone}
                Subject: {submission.subject}
                
                Message:
                {submission.message}
                
                Submitted at: {submission.created_at}
                IP Address: {submission.ip_address}
                ''',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.ADMIN_EMAIL] if hasattr(settings, 'ADMIN_EMAIL') else ['admin@shirstiprinting.com'],
                fail_silently=True,
            )
        except Exception as e:
            print(f"Email sending failed: {e}")
        
        messages.success(request, 'Thank you for your message! We will get back to you soon.')
        return redirect('core:contact')
        
    except Exception as e:
        messages.error(request, 'Sorry, there was an error sending your message. Please try again.')
        return redirect('core:contact')


def page_view(request, slug):
    """Dynamic page view for CMS pages"""
    page = get_object_or_404(Page, slug=slug, is_published=True)
    
    context = {
        'page': page,
        'page_title': page.title
    }
    return render(request, 'core/page.html', context)


def faq_view(request):
    """FAQ page with categories"""
    categories = FAQCategory.objects.filter(is_active=True).prefetch_related(
        'faqs'
    )
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        faqs = FAQ.objects.filter(
            Q(question__icontains=search_query) | Q(answer__icontains=search_query),
            is_active=True
        ).select_related('category')
        
        context = {
            'faqs': faqs,
            'search_query': search_query,
            'page_title': f'FAQ Search Results for "{search_query}"'
        }
        return render(request, 'core/faq_search.html', context)
    
    context = {
        'categories': categories,
        'page_title': 'Frequently Asked Questions'
    }
    return render(request, 'core/faq.html', context)


def handler404(request, exception):
    """Custom 404 error handler"""
    return render(request, 'errors/404.html', status=404)


def handler500(request):
    """Custom 500 error handler"""
    return render(request, 'errors/500.html', status=500)