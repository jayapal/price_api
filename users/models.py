import uuid

from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    user = models.ForeignKey(User, unique=True, on_delete=models.CASCADE)
    key = models.CharField("Key", max_length=40)
    email = models.EmailField(blank=True, null=True, db_index=True)
    gender = models.CharField(blank=True, null=True, max_length=10)
    age = models.IntegerField(blank=True, null=True)
    location = models.CharField(blank=True, null=True, max_length=1000)
    likes = models.CharField(blank=True, null=True, max_length=1000)
    profile_pic = models.ImageField(blank=True, null=True, upload_to='userprofile/',)
    first_product_price_it_notification = models.BooleanField(default=False)
    you_earned_notification = models.BooleanField(default=True)
    login_key = models.UUIDField(max_length=32, default=str(uuid.uuid4()), blank=True, null=True)
    price_points = models.IntegerField(default=0)
    price_points_updated_on = models.DateTimeField(blank=True, null=True)
    facebook_user_token = models.CharField(blank=True, null=True, max_length=1000)
    google_user_token = models.CharField(blank=True, null=True, max_length=1500)
    apple_user_identifier = models.CharField(blank=True, null=True, max_length=1500)
    birthday = models.DateField(blank=True, null=True)
    amt_time_returned_lowest_price = models.IntegerField(default=0, db_index=True)
    referral_code = models.CharField(max_length=255, blank=True, null=True)
    referral_source = models.CharField(max_length=255, blank=True, null=True)
    referred_by = models.ForeignKey(User, related_name="referred_by", blank=True, null=True, on_delete=models.CASCADE)
    updated_on = models.DateTimeField(auto_now=True, db_index=True)
    created_on = models.DateTimeField(auto_now_add=True, db_index=True)
    ebates_id = models.CharField(max_length=255, blank=True, null=True)
    ebtoken = models.CharField(max_length=255, blank=True, null=True)
    ebates_response = models.CharField(max_length=255, blank=True, null=True)
    is_welcome_email_sent = models.BooleanField(default=False)
    is_ebates_day_1_email_sent = models.BooleanField(default=False)
    is_ebates_day_3_email_sent = models.BooleanField(default=False)
    is_ebates_day_5_email_sent = models.BooleanField(default=False)
    your_cashback_balance = models.FloatField(blank=True, null=True)
    your_next_payout = models.FloatField(blank=True, null=True)

    class Meta:
        db_table = 'Klutterapp_userprofile'


class UserSignUp(models.Model):
    PRICE_DOT_COM = 1
    FACEBOOK_BOT = 2
    CHROME_EXTENSION = 3
    MOBILE_APP_ANDROID = 4
    MOBILE_APP_IOS = 5
    MOBILE_APP = 6
    PRICE_DOT_COM_WEB = 7
    PRICE_DOT_COM_MOBILE = 8
    SOURCE_TYPE_OPTIONS = (
        (PRICE_DOT_COM, 'PRICE.COM'),
        (FACEBOOK_BOT, 'FACEBOOK BOT'),
        (CHROME_EXTENSION, 'CHROME EXTENSION'),
        (MOBILE_APP_ANDROID, 'MOBILE_APP_ANDROID'),
        (MOBILE_APP_IOS, 'MOBILE_APP_IOS'),
        (MOBILE_APP, 'MOBILE_APP'),
        (PRICE_DOT_COM_WEB, 'PRICE.COM_WEB'),
        (PRICE_DOT_COM_MOBILE, 'PRICE.COM_MOBILE'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    source = models.IntegerField(choices=SOURCE_TYPE_OPTIONS, db_index=True)
    ip = models.GenericIPAddressField(blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'Klutterapp_usersignup'
