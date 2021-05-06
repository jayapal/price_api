from django.urls import path


urlpatterns = [
    path('webhook/', 'price_it.facebook_bot.facebook_bot_webhook',
     name='facebook_bot_webhook'),
    ]