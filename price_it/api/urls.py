from django.urls import path
from price_it.api.cloudsight_api import get_image_details


urlpatterns = [
    path('image-details/', get_image_details),
]
