from django.db import models
from django.contrib.auth.models import User


class Request(models.Model):
    PRICE_DOT_COM = 1
    FACEBOOK_BOT = 2
    CHROME_EXTENSION = 3
    MOBILE_APP = 4
    SCANNER = 5
    MOBILE_APP_ANDROID = 6
    MOBILE_APP_IOS = 7
    DEALS = 8
    PRICE_DOT_COM_WEB = 9
    PRICE_DOT_COM_MOBILE = 10
    CHAT_FUEL_BOT = 11
    USER_ID = 1
    FACEBOOK_ID = 2
    EMAIL = 3
    SOURCE_TYPE_OPTIONS = (
        (PRICE_DOT_COM, 'PRICE.COM'),
        (PRICE_DOT_COM_WEB, 'PRICE.COM_WEB'),
        (PRICE_DOT_COM_MOBILE, 'PRICE.COM_MOBILE'),
        (FACEBOOK_BOT, 'FACEBOOK BOT'),
        (CHROME_EXTENSION, 'CHROME EXTENSION'),
        (MOBILE_APP, 'MOBILE_APP'),
        (MOBILE_APP_ANDROID, 'MOBILE_APP_ANDROID'),
        (MOBILE_APP_IOS, 'MOBILE_APP_IOS'),
        (SCANNER, 'SCANNER'),
        (DEALS, 'DEALS'),
        (CHAT_FUEL_BOT, 'CHAT_FUEL'),
        )
    USER_TYPE_OPTIONS = (
        (USER_ID, 'USER ID'),
        (FACEBOOK_ID, 'FACEBOOK ID'),
        (EMAIL, 'EMAIL'),
        (DEALS, 'DEALS'),
        )

    PROCESSING = 0 # Default
    COMPLETED = 1 # After finding the best price
    FAILED = 2 # Unable to find the actual product

    STATUS_TYPE_OPTIONS = (
        (PROCESSING, 'in_progress'),
        (COMPLETED, 'completed'),
        (FAILED, 'failed'))

    SCAN = 1
    SHARE = 2
    BROWSE = 3
    SEARCH = 4
    SNAP = 5
    CHROME = 6
    # To identify mode of price it from mobile apps
    PRICEIT_TYPES = (
        (SCAN, 'SCAN'),
        (SHARE, 'SHARE'),
        (BROWSE, 'BROWSE'),
        (SEARCH, 'SEARCH'),
        (SNAP, 'SNAP'),
        (DEALS, 'DEALS'),
        (CHROME, 'CHROME'))

    url = models.URLField(max_length=2000, blank=True, null=True, db_index=True)
    sku = models.CharField(max_length=250, blank=True, null=True, db_index=True)
    product = models.ForeignKey('brand_favourite.ProductsV2',
                                  blank=True, null=True, on_delete=models.CASCADE)
    original_price = models.FloatField(null=True, blank=True, max_length=20)
    source = models.IntegerField(choices=SOURCE_TYPE_OPTIONS, db_index=True)
    user_type = models.IntegerField(choices=USER_TYPE_OPTIONS, db_index=True)
    request_from = models.CharField(max_length=250, db_index=True)
    created_on = models.DateTimeField(auto_now_add=True, db_index=True)
    udpated_on = models.DateTimeField(auto_now=True, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    is_deleted = models.BooleanField(default=False, db_index=True)
    total_saved = models.IntegerField(blank=True, null=True,max_length=20)
    upc = models.CharField(max_length=20, blank=True, null=True, db_index=True)
    status = models.IntegerField(choices=STATUS_TYPE_OPTIONS, default=PROCESSING)
    mark_as_price_drop = models.BooleanField(default=False)
    non_supported_site = models.BooleanField(default=False)
    user = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE)
    is_search = models.BooleanField(default=False)
    is_review = models.BooleanField(default=False)
    priceit_type = models.IntegerField(choices=PRICEIT_TYPES, blank=True, null=True, db_index=True)
    image_url = models.URLField(max_length=2000, blank=True, null=True, db_index=True)
    coupons_found = models.BooleanField(default=False)
    coupon_not_available = models.BooleanField(default=False)
    channel = models.CharField(max_length=20, blank=True, null=True)
    is_mixpanel_result_pushed = models.BooleanField(default=False)
    task_received_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    celery_task_id = models.CharField(max_length=50, blank=True, null=True)
    celery_task_state = models.CharField(max_length=10, blank=True, null=True)
    api_version = models.IntegerField(default=1)
    similar_api_version = models.IntegerField(default=1)
    ip = models.GenericIPAddressField(blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True, max_length=20)
    longitude = models.FloatField(blank=True, null=True, max_length=20)
    is_google_api_processed = models.BooleanField(default=False)
    google_api_run_on = models.DateTimeField(blank=True, null=True)
    search_term = models.CharField(max_length=256, blank=True, null=True)
    sh_job_id = models.CharField(max_length=100, blank=True, null=True)
    is_sh_wehhook_received = models.BooleanField(default=False)
    objectID = models.CharField(max_length=1500, blank=True, null=True)
    price_category = models.CharField(max_length=256, blank=True, null=True, db_index=True)
    is_es_description_processed = models.BooleanField(default=False)
    is_refresh_completed = models.BooleanField(default=True)
    last_refreshed_at = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return str(self.id)

    class Meta:
        db_table = 'PriceIT_request'

    def save(self, *args, **kwargs):
        print("SAVE-REQUEST")
        sem3_domain = "http://sem3-idn.s3-website-us-east-1.amazonaws.com"
        if self.image_url and sem3_domain in self.image_url:
            print("SELF.IMAGE")
            # since we need to make it HTTPS
            image_url = self.image_url.replace(
                sem3_domain,
                "https://d3ouh4psrmopuu.cloudfront.net"
            )
            self.image_url = image_url
        super(Request, self).save(*args, **kwargs)
