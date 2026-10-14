from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q, Avg
from django.contrib import messages
from datetime import datetime

from .models import (
    shangpin, GoodsCategory, Guige, GoodsDetailImage,
    CartInfos, OrderInfos, Address, ProductReview
)
from .forms import ReviewForm


# ===================== 首页 =====================

@login_required
def index(request):
    """首页商品展示"""
    cid = request.GET.get('cid', 0)
    keyword = request.GET.get('keyword', '')

    categories = GoodsCategory.objects.all()
    shangpin_list = shangpin.objects.all()

    if cid and cid.isdigit() and int(cid) > 0:
        shangpin_list = shangpin_list.filter(category_id=int(cid))
    if keyword:
        shangpin_list = shangpin_list.filter(
            Q(name__icontains=keyword) | Q(caption__icontains=keyword)
        )

    hot_products = shangpin.objects.all().order_by('-sales')[:8]
    cart_count = CartInfos.objects.filter(user_id=request.user.id).count()

    return render(request, 'index.html', {
        'shangpin': shangpin_list,
        'categories': categories,
        'hot_products': hot_products,
        'keyword': keyword,
        'cart_total_count': cart_count,
    })


# ===================== 商品详情 =====================

@login_required
def detail(request, id):
    """商品详情页"""
    shangpin1 = get_object_or_404(shangpin, id=id)
    guige = Guige.objects.filter(guige_leixing_id=shangpin1.guige_leixing_id) if shangpin1.guige_leixing else []
    detail_images = GoodsDetailImage.objects.filter(shangpin=shangpin1)

    reviews = ProductReview.objects.filter(product=shangpin1).order_by('-created_at')
    review_count = reviews.count()
    average_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    user_has_reviewed = ProductReview.objects.filter(user=request.user, product=shangpin1).exists()
    user_has_purchased = CartInfos.objects.filter(user_id=request.user.id, shangpin_id=shangpin1.id).exists()
    cart_count = CartInfos.objects.filter(user_id=request.user.id).count()

    return render(request, 'detail.html', {
        'shangpin': shangpin1,
        'guiges': guige,
        'detail_images': detail_images,
        'reviews': reviews[:10],
        'review_count': review_count,
        'average_rating': average_rating,
        'user_has_reviewed': user_has_reviewed,
        'user_has_purchased': user_has_purchased,
        'cart_total_count': cart_count,
    })


# ===================== 购物车 =====================

@login_required
def showcart(request):
    """购物车页面"""
    userid = request.user.id
    carts = CartInfos.objects.filter(user_id=userid)
    sumlist = []

    for cart in carts:
        shangpin1 = shangpin.objects.get(id=cart.shangpin_id)
        guige = Guige.objects.filter(id=cart.guige_id).first() if cart.guige_id else None
        guige_name = guige.name if guige else '默认'
        sumlist.append({
            'cart': cart,
            'good': shangpin1,
            'guige_name': guige_name
        })

    cart_total_count = sum(item['cart'].num for item in sumlist)

    return render(request, 'cart.html', {
        'sumlist': sumlist,
        'cart_total_count': cart_total_count
    })


@login_required
def addcart(request, id):
    """添加购物车"""
    if request.method == 'POST':
        try:
            quantity = int(request.POST.get('quantity', 1))
            guige_id = request.POST.get('guige_id')
            guige_id = int(guige_id) if guige_id and guige_id.isdigit() else None

            product = shangpin.objects.get(id=id)
            if quantity > product.stock:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'message': f'库存不足，仅剩{product.stock}件'})
                messages.error(request, f'库存不足，仅剩{product.stock}件')
                return redirect('goods:detail', id=id)

            cart_item, created = CartInfos.objects.get_or_create(
                user_id=request.user.id,
                shangpin_id=id,
                guige_id=guige_id,
                defaults={'num': quantity}
            )

            if not created:
                new_num = cart_item.num + quantity
                if new_num > product.stock:
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse(
                            {'success': False, 'message': f'库存不足，最多还能购买{product.stock - cart_item.num}件'})
                    messages.error(request, f'库存不足，最多还能购买{product.stock - cart_item.num}件')
                    return redirect('goods:detail', id=id)
                cart_item.num = new_num
                cart_item.save()

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': '添加成功'})

            messages.success(request, '已添加到购物车')
            return redirect('goods:carts')

        except Exception as e:
            print(f"Error adding to cart: {e}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': str(e)}, status=400)
            return redirect('goods:detail', id=id)

    return redirect('goods:detail', id=id)


@login_required
def delt(request, id):
    """删除单个购物车项"""
    try:
        cart_item = CartInfos.objects.filter(id=id, user_id=request.user.id).first()
        if cart_item:
            cart_item.delete()
            messages.success(request, '✅ 商品已从购物车删除')
        else:
            messages.error(request, '❌ 商品不存在或不属于您')
    except Exception as e:
        print(f"删除购物车项错误: {e}")
        messages.error(request, '❌ 删除失败')

    return redirect('goods:carts')


@login_required
def batch_delete_cart(request):
    """批量删除购物车"""
    if request.method == 'POST':
        try:
            cart_ids = request.POST.getlist('cart_items')
            if cart_ids:
                cart_ids = [int(cid) for cid in cart_ids if cid.isdigit()]
                CartInfos.objects.filter(id__in=cart_ids, user_id=request.user.id).delete()

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': f'成功删除{len(cart_ids)}个商品'})
            return redirect('goods:carts')
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': str(e)}, status=400)
            return redirect('goods:carts')
    return redirect('goods:carts')


# ===================== 订单功能 =====================

@login_required
def checkout(request):
    """订单确认页面"""
    userid = request.user.id
    selected_cart_ids = request.POST.getlist('cart_items')

    if not selected_cart_ids:
        carts = CartInfos.objects.filter(user_id=userid)
        sumlist = []
        for cart in carts:
            shangpin1 = shangpin.objects.get(id=cart.shangpin_id)
            guige = Guige.objects.filter(id=cart.guige_id).first() if cart.guige_id else None
            guige_name = guige.name if guige else '默认'
            sumlist.append({'cart': cart, 'good': shangpin1, 'guige_name': guige_name})
        messages.error(request, '请至少选择一个商品进行结算！')
        return render(request, 'cart.html', {'sumlist': sumlist})

    carts = CartInfos.objects.filter(id__in=selected_cart_ids, user_id=userid)
    total_price = 0
    shangpins = []
    for cart in carts:
        shangpin1 = shangpin.objects.get(id=cart.shangpin_id)
        shangpins.append(shangpin1)
        total_price += float(shangpin1.price) * cart.num

    sumlist = zip(list(carts), shangpins)
    address_list = Address.objects.filter(user=request.user).order_by("-is_default")

    request.session['selected_cart_ids'] = selected_cart_ids

    return render(request, 'checkout.html', {
        'sumlist': sumlist,
        'total_price': total_price,
        'address_list': address_list,
    })


@login_required
def confirm_checkout(request):
    """确认下单"""
    userid = request.user.id
    selected_cart_ids = request.session.get('selected_cart_ids', [])
    selected_address_id = request.POST.get('selected_address_id')

    if not selected_address_id:
        messages.error(request, '请选择收货地址！')
        return redirect('goods:checkout')

    if not selected_cart_ids:
        return redirect('goods:carts')

    carts = CartInfos.objects.filter(id__in=selected_cart_ids, user_id=userid)

    if not carts.exists():
        messages.error(request, '购物车为空，请重新选择商品')
        return redirect('goods:carts')

    total_price = 0
    for cart in carts:
        shangpin1 = shangpin.objects.get(id=cart.shangpin_id)
        total_price += float(shangpin1.price) * cart.num

    order = OrderInfos.objects.create(
        price=total_price,
        user_id=userid,
        state='待支付',
    )

    carts.delete()

    if 'selected_cart_ids' in request.session:
        del request.session['selected_cart_ids']

    return render(request, 'success.html', {
        'id': order.id,
        'time': order.create_time,
    })


@login_required
def showoderinfo(request):
    """我的订单列表"""
    userid = request.user.id
    orderinfos = OrderInfos.objects.filter(user_id=userid).order_by('-create_time')

    cart_count = CartInfos.objects.filter(user_id=request.user.id).count()

    return render(request, 'orderinfo.html', {
        'orderInfos': orderinfos,
        'cart_total_count': cart_count,
    })


# ===================== 收货地址管理 =====================

@login_required
def address_list(request):
    """地址列表"""
    addresses = Address.objects.filter(user=request.user).order_by("-is_default")
    cart_count = CartInfos.objects.filter(user_id=request.user.id).count()

    return render(request, "address_list.html", {
        "addresses": addresses,
        "cart_total_count": cart_count,
    })


@login_required
def address_add(request):
    """添加地址"""
    if request.method == "POST":
        receiver = request.POST.get("receiver")
        phone = request.POST.get("phone")
        province = request.POST.get("province")
        city = request.POST.get("city")
        district = request.POST.get("district")
        detail = request.POST.get("detail")

        is_first = not Address.objects.filter(user=request.user).exists()

        Address.objects.create(
            user=request.user,
            receiver=receiver,
            phone=phone,
            province=province,
            city=city,
            district=district,
            detail=detail,
            is_default=is_first
        )
        messages.success(request, '✅ 地址添加成功！')
        return redirect("goods:address_list")

    cart_count = CartInfos.objects.filter(user_id=request.user.id).count()
    return render(request, "address_add.html", {
        "cart_total_count": cart_count,
    })


@login_required
def set_default(request, id):
    """设置默认地址"""
    Address.objects.filter(user=request.user, is_default=True).update(is_default=False)
    addr = get_object_or_404(Address, id=id, user=request.user)
    addr.is_default = True
    addr.save()
    messages.success(request, '✅ 已设为默认地址！')
    return redirect("goods:address_list")


# ===================== 评价功能 =====================

@login_required
def add_review(request, product_id):
    """添加/编辑商品评价"""
    product = get_object_or_404(shangpin, id=product_id)

    existing_review = ProductReview.objects.filter(
        user=request.user,
        product=product
    ).first()

    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=existing_review)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.product = product
            review.save()

            product.comments = ProductReview.objects.filter(product=product).count()
            product.save()

            messages.success(request, '✅ 评价提交成功！' if not existing_review else '✅ 评价修改成功！')
            return redirect('goods:detail', id=product.id)
        else:
            messages.error(request, '❌ 表单验证失败，请检查输入')
    else:
        form = ReviewForm(instance=existing_review)

    cart_count = CartInfos.objects.filter(user_id=request.user.id).count()

    return render(request, 'add_review.html', {
        'form': form,
        'product': product,
        'existing_review': existing_review,
        'cart_total_count': cart_count,
    })


@login_required
def delete_review(request, review_id):
    """删除用户自己的评价"""
    review = get_object_or_404(ProductReview, id=review_id, user=request.user)
    product_id = review.product.id

    review.delete()

    product = shangpin.objects.get(id=product_id)
    product.comments = ProductReview.objects.filter(product=product).count()
    product.save()

    messages.success(request, '✅ 评价已成功删除！')
    return redirect('goods:detail', id=product_id)