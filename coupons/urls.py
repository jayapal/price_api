from django.urls import path

from coupons.views import coupon_list

urlpatterns = [
    path('list/', coupon_list)

]
