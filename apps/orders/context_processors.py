# Context processor to add cart count to all templates
# apps/orders/context_processors.py
def cart_context(request):
    """Add cart information to all template contexts"""
    cart_count = 0
    cart_total = 0
    
    if hasattr(request, 'user'):
        cart_manager = CartManager(request)
        cart_count = cart_manager.get_cart_count()
        cart_total = cart_manager.get_cart_total()
    
    return {
        'cart_count': cart_count,
        'cart_total': cart_total,
    }

