from django.urls import path

from price_alert import views

urlpatterns = [
    path('create/', views.alert_create),
    path('list/', views.alert_list),
]
