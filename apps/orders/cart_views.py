# apps/services/cart_views.py
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from apps.services.models import StaticProduct
from .utils import CartManager
import json


class AddToCartView(LoginRequiredMixin, View):
    """Add product to cart via AJAX"""
    
    def post(self, request, product_id):
        try:
            product = get_object_or_404(StaticProduct, id=product_id)
            
            # Parse request data
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST
            
            quantity = int(data.get('quantity', 1))
            specifications = data.get('specifications', {})
            design_id = data.get('design_id')
            
            # Validate quantity
            if quantity < 1 or quantity > 999:
                return JsonResponse({
                    'success': False,
                    'message': 'Please enter a valid quantity (1-999)'
                }, status=400)
            
            cart_manager = CartManager(request)
            
            # Get user design if provided
            user_design = None
            if design_id and request.user.is_authenticated:
                from templates_mgmt.models import UserDesign
                try:
                    user_design = UserDesign.objects.get(id=design_id, user=request.user)
                except UserDesign.DoesNotExist:
                    pass
            
            # Add item to cart
            cart_item = cart_manager.add_item(
                product=product,
                quantity=quantity,
                user_design=user_design,
                specifications=specifications
            )
            
            return JsonResponse({
                'success': True,
                'message': f'{product.name} added to cart successfully!',
                'cart_count': cart_manager.get_cart_count(),
                'cart_total': str(cart_manager.get_cart_total()),
                'item_id': cart_item.id
            })
            
        except Product.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Product not found'
            }, status=404)
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': 'Error adding item to cart. Please try again.'
            }, status=500)


