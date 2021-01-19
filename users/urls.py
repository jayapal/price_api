from django.urls import path

from users.views import user_details

urlpatterns = [
    path('detail/<int:user_id>/', user_details)

]
