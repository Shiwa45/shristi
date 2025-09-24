# apps/orders/emails.py
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
from .models import Order, OrderStatusHistory
import logging

logger = logging.getLogger(__name__)


class OrderEmailManager:
    """Manage all order-related email notifications"""
    
    @staticmethod
    def send_order_confirmation(order):
        """Send order confirmation email to customer"""
        try:
            subject = f'Order Confirmation - {order.order_number} | Shirsti Printing'
            
            context = {
                'order': order,
                'order_items': order.items.select_related('product'),
                'company_name': 'Shirsti Printing Company',
                'support_email': settings.DEFAULT_FROM_EMAIL,
                'company_phone': '+91 123 456 7890',
            }
            
            html_content = render_to_string('orders/emails/order_confirmation.html', context)
            text_content = strip_tags(html_content)
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[order.customer_email],
            )
            email.attach_alternative(html_content, "text/html")
            email.send()
            
            logger.info(f'Order confirmation email sent for order {order.order_number}')
            return True
            
        except Exception as e:
            logger.error(f'Failed to send order confirmation for {order.order_number}: {str(e)}')
            return False
    
    @staticmethod
    def send_status_update(order, old_status, new_status, notes=''):
        """Send order status update email to customer"""
        try:
            # Don't send email for draft orders
            if new_status == 'draft':
                return True
            
            subject = f'Order Update - {order.order_number} | Shirsti Printing'
            
            context = {
                'order': order,
                'old_status': old_status,
                'new_status': new_status,
                'status_display': order.get_status_display(),
                'notes': notes,
                'company_name': 'Shirsti Printing Company',
                'support_email': settings.DEFAULT_FROM_EMAIL,
                'company_phone': '+91 123 456 7890',
                'order_tracking_url': f"{settings.SITE_URL}/orders/{order.order_number}/",
            }
            
            html_content = render_to_string('orders/emails/status_update.html', context)
            text_content = strip_tags(html_content)
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[order.customer_email],
            )
            email.attach_alternative(html_content, "text/html")
            email.send()
            
            logger.info(f'Status update email sent for order {order.order_number}: {old_status} -> {new_status}')
            return True
            
        except Exception as e:
            logger.error(f'Failed to send status update for {order.order_number}: {str(e)}')
            return False
    
    @staticmethod
    def send_admin_notification(order, event_type='new_order'):
        """Send notification to admin about order events"""
        try:
            admin_emails = getattr(settings, 'ADMIN_EMAIL_LIST', [settings.DEFAULT_FROM_EMAIL])
            
            if event_type == 'new_order':
                subject = f'New Order Received - {order.order_number}'
                template = 'orders/emails/admin_new_order.html'
            elif event_type == 'payment_received':
                subject = f'Payment Received - {order.order_number}'
                template = 'orders/emails/admin_payment_received.html'
            else:
                return True
            
            context = {
                'order': order,
                'order_items': order.items.select_related('product'),
                'admin_url': f"{settings.SITE_URL}/admin/orders/order/{order.id}/",
            }
            
            html_content = render_to_string(template, context)
            text_content = strip_tags(html_content)
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=admin_emails,
            )
            email.attach_alternative(html_content, "text/html")
            email.send()
            
            logger.info(f'Admin notification sent for order {order.order_number}: {event_type}')
            return True
            
        except Exception as e:
            logger.error(f'Failed to send admin notification for {order.order_number}: {str(e)}')
            return False
    
    @staticmethod
    def send_quote_confirmation(quote_request):
        """Send quote request confirmation email"""
        try:
            subject = f'Quote Request Received - {quote_request.quote_number} | Shirsti Printing'
            
            context = {
                'quote': quote_request,
                'quote_items': quote_request.items.all(),
                'company_name': 'Shirsti Printing Company',
                'support_email': settings.DEFAULT_FROM_EMAIL,
                'company_phone': '+91 123 456 7890',
            }
            
            html_content = render_to_string('orders/emails/quote_confirmation.html', context)
            text_content = strip_tags(html_content)
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[quote_request.customer_email],
            )
            email.attach_alternative(html_content, "text/html")
            email.send()
            
            logger.info(f'Quote confirmation email sent for {quote_request.quote_number}')
            return True
            
        except Exception as e:
            logger.error(f'Failed to send quote confirmation for {quote_request.quote_number}: {str(e)}')
            return False


# apps/orders/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order, OrderStatusHistory
from .emails import OrderEmailManager


@receiver(post_save, sender=Order)
def handle_order_creation(sender, instance, created, **kwargs):
    """Handle order creation events"""
    if created and instance.status != 'draft':
        # Send confirmation email to customer
        OrderEmailManager.send_order_confirmation(instance)
        
        # Send notification to admin
        OrderEmailManager.send_admin_notification(instance, 'new_order')


@receiver(post_save, sender=OrderStatusHistory)
def handle_status_change(sender, instance, created, **kwargs):
    """Handle order status changes"""
    if created:
        # Send status update email to customer
        OrderEmailManager.send_status_update(
            instance.order,
            instance.old_status,
            instance.new_status,
            instance.notes
        )
        
        # Send admin notification for payment received
        if instance.new_status == 'paid':
            OrderEmailManager.send_admin_notification(instance.order, 'payment_received')


# Email Templates

# templates/orders/emails/base_email.html
BASE_EMAIL_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ subject }}</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            text-align: center;
            border-radius: 8px 8px 0 0;
        }
        .content {
            background: #f9f9f9;
            padding: 30px;
            border-radius: 0 0 8px 8px;
        }
        .order-details {
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }
        .order-items {
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
        }
        .order-items th, .order-items td {
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }
        .order-items th {
            background-color: #f2f2f2;
        }
        .total-row {
            font-weight: bold;
            background-color: #f9f9f9;
        }
        .button {
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 12px 24px;
            text-decoration: none;
            border-radius: 5px;
            margin: 20px 0;
        }
        .footer {
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #666;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ company_name }}</h1>
        <p>Your trusted partner for professional printing services</p>
    </div>
    
    <div class="content">
        {% block content %}{% endblock %}
    </div>
    
    <div class="footer">
        <p>
            <strong>{{ company_name }}</strong><br>
            Email: {{ support_email }} | Phone: {{ company_phone }}<br>
            123 Print Street, New Delhi, India
        </p>
        <p style="font-size: 12px;">
            This email was sent to {{ order.customer_email }}. 
            If you have any questions, please contact our support team.
        </p>
    </div>
</body>
</html>"""

# templates/orders/emails/order_confirmation.html
ORDER_CONFIRMATION_TEMPLATE = """{% extends 'orders/emails/base_email.html' %}

{% block content %}
<h2>Order Confirmation</h2>
<p>Dear {{ order.customer_name }},</p>
<p>Thank you for your order! We've received your order and it's being processed.</p>

<div class="order-details">
    <h3>Order Details</h3>
    <p><strong>Order Number:</strong> {{ order.order_number }}</p>
    <p><strong>Order Date:</strong> {{ order.created_at|date:"F d, Y" }}</p>
    <p><strong>Status:</strong> {{ order.get_status_display }}</p>
    
    {% if order.estimated_delivery_date %}
    <p><strong>Estimated Delivery:</strong> {{ order.estimated_delivery_date|date:"F d, Y" }}</p>
    {% endif %}
</div>

<h3>Order Items</h3>
<table class="order-items">
    <thead>
        <tr>
            <th>Item</th>
            <th>Quantity</th>
            <th>Unit Price</th>
            <th>Total</th>
        </tr>
    </thead>
    <tbody>
        {% for item in order_items %}
        <tr>
            <td>
                {{ item.product_name }}
                {% if item.user_design %}
                <br><small>Custom Design: {{ item.user_design.name }}</small>
                {% elif item.uploaded_file %}
                <br><small>File Uploaded</small>
                {% endif %}
            </td>
            <td>{{ item.quantity }}</td>
            <td>₹{{ item.unit_price }}</td>
            <td>₹{{ item.total_price }}</td>
        </tr>
        {% endfor %}
        <tr class="total-row">
            <td colspan="3">Subtotal</td>
            <td>₹{{ order.subtotal }}</td>
        </tr>
        {% if order.discount_amount > 0 %}
        <tr>
            <td colspan="3">Discount</td>
            <td>-₹{{ order.discount_amount }}</td>
        </tr>
        {% endif %}
        <tr>
            <td colspan="3">GST (18%)</td>
            <td>₹{{ order.tax_amount }}</td>
        </tr>
        <tr class="total-row">
            <td colspan="3"><strong>Total Amount</strong></td>
            <td><strong>₹{{ order.total_amount }}</strong></td>
        </tr>
    </tbody>
</table>

<h3>Shipping Address</h3>
<p>
    {{ order.shipping_address_line1 }}<br>
    {% if order.shipping_address_line2 %}{{ order.shipping_address_line2 }}<br>{% endif %}
    {{ order.shipping_city }}, {{ order.shipping_state }} {{ order.shipping_pincode }}<br>
    {{ order.shipping_country }}
</p>

<div style="text-align: center;">
    <a href="{{ order_tracking_url }}" class="button">Track Your Order</a>
</div>

<p>We'll keep you updated on your order status via email. If you have any questions, please don't hesitate to contact our support team.</p>

<p>Thank you for choosing {{ company_name }}!</p>
{% endblock %}"""

# templates/orders/emails/status_update.html
STATUS_UPDATE_TEMPLATE = """{% extends 'orders/emails/base_email.html' %}

{% block content %}
<h2>Order Status Update</h2>
<p>Dear {{ order.customer_name }},</p>
<p>We have an update on your order <strong>{{ order.order_number }}</strong>.</p>

<div class="order-details">
    <h3>Status Update</h3>
    <p><strong>Previous Status:</strong> {{ old_status|title }}</p>
    <p><strong>Current Status:</strong> {{ status_display }}</p>
    {% if notes %}
    <p><strong>Notes:</strong> {{ notes }}</p>
    {% endif %}
</div>

{% if new_status == 'confirmed' %}
<p>Great news! Your order has been confirmed and is now being prepared for production.</p>
{% elif new_status == 'in_production' %}
<p>Your order is now in production. Our team is working on creating your custom prints.</p>
{% elif new_status == 'ready' %}
<p>Excellent! Your order is ready for pickup/delivery. We'll contact you shortly with details.</p>
{% elif new_status == 'shipped' %}
<p>Your order has been shipped and is on its way to you!</p>
{% elif new_status == 'delivered' %}
<p>Your order has been delivered. We hope you love your prints!</p>
{% elif new_status == 'completed' %}
<p>Your order is now complete. Thank you for choosing our services!</p>
{% endif %}

<div style="text-align: center;">
    <a href="{{ order_tracking_url }}" class="button">View Order Details</a>
</div>

<p>If you have any questions or concerns, please don't hesitate to contact our support team.</p>

<p>Thank you for your business!</p>
{% endblock %}"""