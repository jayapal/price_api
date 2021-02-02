from django.urls import path

from coupons.views import coupon_list, coupon_details

urlpatterns = [
    path('list/', coupon_list),
    path('detail/', coupon_details)

]
