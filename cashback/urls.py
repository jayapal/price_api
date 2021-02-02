from django.urls import path

from cashback.views import get_category_list, cash_back_stores_list, cashback_list

urlpatterns = [
    path('category/list/', get_category_list),
    path('cash_back_stores/', cash_back_stores_list),
    path('user/', cashback_list)

]
