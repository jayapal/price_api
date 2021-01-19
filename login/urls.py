from django.urls import path

from login.views import get_user_with_email

urlpatterns = [
    path('login/', get_user_with_email)

]

