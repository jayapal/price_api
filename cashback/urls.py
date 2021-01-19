from django.urls import path

from cashback.views import get_category_list

urlpatterns = [
    path('category/list/', get_category_list)

]
