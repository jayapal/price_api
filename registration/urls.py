from django.urls import path

urlpatterns = [
    url(r'^sign-in/$', 'PriceIT.views.get_user_with_email')

]

