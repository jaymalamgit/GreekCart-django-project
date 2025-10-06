from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from store.models import Product, Variation
from .models import Cart, CartItem

# ----------------------------- GET OR CREATE CART ID -----------------------------
def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart

# ----------------------------- ADD TO CART -----------------------------
def add_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product_variation = []

    # Get selected variations from POST
    if request.method == 'POST':
        for item in request.POST:
            key = item
            value = request.POST[key]

            try:
                variation = Variation.objects.get(product=product, variation_category__iexact=key, variation_value__iexact=value)
                product_variation.append(variation)
            except Variation.DoesNotExist:
                pass
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request)) #get  the cart using the  cart_id  present in the session_key
    except Cart.DoesNotExist:
        cart = Cart.objects.create(
            cart_id = _cart_id(request)
        )
    cart.save()


    is_cart_item_exists = CartItem.objects.filter(product=product ,cart=cart).exists()
    if is_cart_item_exists:
        cart_items = CartItem.objects.filter(product=product, cart=cart)
        # existing variations  ->  database
        # current variations   -> product variation
        # item_id  -> database
        ex_var_list = []
        item_ids =[]
        for item in cart_items:
            existing_variation = item.variations.all()
            ex_var_list.append(list(existing_variation))
            item_ids.append(item.id)

        print(ex_var_list)

        if product_variation in ex_var_list:
            # Increase quantity of existing cart item
            index = ex_var_list.index(product_variation)
            item_id = item_ids[index]
            item = CartItem.objects.get(product=product, id=item_id)
            item.quantity += 1
            item.save()

        else:
            item = CartItem.objects.create(product=product, quantity=1, cart=cart)
            if len(product_variation) > 0:
                item.variations.clear()
                item.variations.add(*product_variation)
            item.save()
    else:
        cart_item = CartItem.objects.create(
            product = product,
            quantity = 1,
            cart = cart,
        )
        if len(product_variation) > 0:
            cart_item.variations.clear()
            cart_item.variations.add(*product_variation)
        cart_item.save()
    return redirect('cart')

# ----------------------------- REMOVE ONE QUANTITY -----------------------------

def remove_cart(request, product_id, cart_item_id):
    cart = Cart.objects.get(cart_id=_cart_id(request))
    product = get_object_or_404(Product, id=product_id)
    try:
        cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
    except:
        pass
    return redirect('cart')

# ----------------------------- REMOVE ENTIRE CART ITEM -----------------------------
def remove_cart_item(request, product_id, cart_item_id):
    cart = get_object_or_404(Cart, cart_id=_cart_id(request))
    try:
        cart_item = CartItem.objects.get(product_id=product_id, cart=cart, id=cart_item_id)
        cart_item.delete()
    except CartItem.DoesNotExist:
        pass
    return redirect('cart')


# ----------------------------- DISPLAY CART PAGE -----------------------------
def cart(request, total=0, quantity=0, cart_items=None):
    tax = 0
    grand_total = 0

    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_items = CartItem.objects.filter(cart=cart, is_active=True)

        for cart_item in cart_items:
            total += cart_item.product.price * cart_item.quantity
            quantity += cart_item.quantity

        tax = (2 * total) / 100
        grand_total = total + tax

    except ObjectDoesNotExist:
        cart_items = []

    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'tax': tax,
        'grand_total': grand_total,
    }
    return render(request, 'store/cart.html', context)
