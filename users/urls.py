from django.urls import path

from users.views import user_details

urlpatterns = [
    path('detail/<int:id>/', user_details)

]
