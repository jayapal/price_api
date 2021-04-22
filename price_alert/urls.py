from django.urls import path

from price_alert import views

urlpatterns = [
    path('create/', views.alert_create),
    path('list/', views.alert_list),
    path('mark_as_inactive/', views.mark_as_inactive),
    path('delete/', views.alert_delete, name='delete'),
]
