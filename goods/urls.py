from django.urls import path
from . import views

app_name = 'goods'

urlpatterns = [
    path('', views.index, name='index'),
    path('index/', views.index, name='index'),
    path('detail/<int:id>', views.detail, name='detail'),
    path('carts/', views.showcart, name='carts'),          # ← 注意这里是 name='carts'
    path('addcart/<int:id>', views.addcart, name='addcart'),
    path('delt/<int:id>', views.delt, name='delt'),
    path('batch_delete/', views.batch_delete_cart, name='batch_delete'),
    path('checkout/', views.checkout, name='checkout'),
    path('confirm_checkout/', views.confirm_checkout, name='confirm_checkout'),
    path('orderinfo/', views.showoderinfo, name='orderinfo'),
    path('address/list/', views.address_list, name='address_list'),
    path('address/add/', views.address_add, name='address_add'),
    path('address/setdefault/<int:id>/', views.set_default, name='set_default'),
    path('product/<int:product_id>/review/', views.add_review, name='add_review'),
    path('review/<int:review_id>/delete/', views.delete_review, name='delete_review'),
]