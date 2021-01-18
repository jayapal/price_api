from django.urls import path

from registration.views import get_user_with_email

urlpatterns = [
    path('sign-in/', get_user_with_email)

]

