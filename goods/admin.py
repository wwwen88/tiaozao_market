from django.contrib import admin
from .models import *

# 注册所有商品相关模型
admin.site.register(GoodsCategory)      # 商品分类
admin.site.register(Brand)              # 品牌
admin.site.register(Guige_leixing)      # 规格类型
admin.site.register(Guige)              # 规格
admin.site.register(shangpin)           # 商品 ⭐ 最重要
admin.site.register(GoodsDetailImage)   # 商品详情图片
admin.site.register(CartInfos)          # 购物车
admin.site.register(OrderInfos)         # 订单
admin.site.register(Address)            # 收货地址
admin.site.register(ProductReview)      # 商品评价