from django.urls import path

from price_alert import views

urlpatterns = [
    path('create/', views.alert_create),

]
