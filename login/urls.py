from django.urls import path

from login.views import login_user

urlpatterns = [
    path('login/', login_user)

]

