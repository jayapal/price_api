from django.db import models
from django.contrib.auth.models import User


class RequestProductCoupon(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=500)
    expiry_date = models.DateTimeField(auto_now=True)
    savings = models.IntegerField(blank=True, null=True,
                             max_length=20)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = "Request Product Coupon"
        verbose_name_plural = "Request Product Coupon"


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


class WhitelistedDomain(models.Model):

    CATEGORY_CHOICES = (
        ('auto', 'Auto'),
        ('business', 'Business'),
        ('apparel and accessories', 'Apparel and Accessories'),
        ('electronics', 'Electronics'),
        ('department stores', 'Department Stores'),
        ('entertainment and media', 'Entertainment and Media'),
        ('baby', 'Baby'),
        ('family', 'Family'),
        ('food and drink', 'Food and Drink'),
        ('toys', 'Toys'),
        ('gifts & flowers', 'Gifts & Flowers'),
        ('health & beauty', 'Health & Beauty'),
        ('home', 'Home'),
        ('travel', 'Travel'),
        ('sports & fitness', 'Sports & Fitness'),
        ('pets', 'Pets'),
        ('online services', 'Online Services'),
        ('education', 'Education'),
    )

    PJ = 'PJ'
    LS = 'LS'
    Connexity = 'Connexity'
    CJ = 'cj'
    ImpactRadius = 'Impact'
    ShareASale = 'ShareASale'
    FlexOffers = 'FlexOffers'
    Ebay = 'Ebay'
    Awin = 'Awin'
    Viglink = 'Viglink'

    NETWORK_CHOICES = (
        (PJ, PJ),
        (LS, LS),
        (Connexity, Connexity),
        (CJ, CJ),
        (ImpactRadius, ImpactRadius),
        (ShareASale, ShareASale),
        (FlexOffers, FlexOffers),
        (Ebay, Ebay),
        (Awin, Awin),
        (Viglink, Viglink)
    )
    PERCENTAGE = "%"
    FIXED = "$"
    COMMISSION_CHOICES = (
        (PERCENTAGE, PERCENTAGE),
        (FIXED, FIXED)
    )

    network = models.CharField(max_length=10, blank=True, null=True, db_index=True, choices=NETWORK_CHOICES)
    name = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    name_display = models.CharField("store display name", max_length=255, blank=True, null=True, db_index=True)
    domain = models.URLField(max_length=255, unique=True, db_index=True)
    affiliate_url = models.URLField(max_length=500, blank=True, null=True, db_index=True)
    chrome_extension_enabled = models.BooleanField(default=False)
    app_enabled = models.BooleanField(default=False)
    logo = models.ImageField(upload_to='custompic/',
                             blank=True, null=True)
    cashback_enabled = models.BooleanField(default=False)
    visual_search_enabled = models.BooleanField(default=False)
    under_review = models.BooleanField(default=False)
    cashback_value = models.FloatField(blank=True, null=True, max_length=20)
    commission = models.FloatField(blank=True, null=True, max_length=20)
    commission_type = models.CharField(max_length=10, choices=COMMISSION_CHOICES, blank=True, null=True)
    cashback_display_name = models.CharField(blank=True, null=True, max_length=252)
    exclusions = models.CharField(blank=True, null=True, max_length=1024)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    order = models.IntegerField(blank=True, null=True, max_length=20, db_index=True)
    category = models.CharField(blank=True, null=True, max_length=255,
                                db_index=True)
    coupon_enabled = models.BooleanField(default=False)
    number_of_coupons = models.IntegerField(default=0, max_length=20, db_index=True)
    enable_extension_affiliate_link = models.BooleanField(default=True)
    image_square = models.ImageField(upload_to='custompic/', blank=True, null=True)
    top_level_domain = models.CharField(max_length=255, db_index=True, blank=True, null=True)
    ebates_enabled = models.BooleanField(default=False)
    ebates_cashback_value = models.FloatField(blank=True, null=True)
    ebates_shopping_url = models.CharField(max_length=1000, blank=True, null=True)
    is_featured = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Whitelisted Domain"
        verbose_name_plural = "Whitelisted Domains"
        db_table = 'PriceIT_whitelisteddomain'


class PriceappCacheTable(models.Model):
    cache_key = models.CharField(primary_key=True, max_length=255)
    value = models.TextField()
    expires = models.DateTimeField()

    class Meta:
        db_table = 'priceapp_cache_table'


class LinkMonetizer(models.Model):
    """
    Deep Links Monetization

    The three networks that offer deep linking (Linkshare, CJ and PepperJam) all go about it in different ways.
    That being said, I think we can have a standardized table with the below headings.

    Retailer Name (column 1)
    Network (column 2) -- ie. Linkshare, CJ or PepperJam
    Retail Base URL (column 3)
    Price Affiliate ID (column 4)
    Merchant ID (column 5)
    """
    CJ = 1
    PJ = 2
    LINKSHARE = 3
    IMPACT_RADIUS = 4
    SHARE_A_SALE = 5
    AVANTLINKS = 6
    SOURCE_CHOICES = (
        (CJ,'CJ'),
        (LINKSHARE,'Linkshare'),
        (PJ,'PepperJam'),
        (IMPACT_RADIUS, 'ImpactRadius'),
        (SHARE_A_SALE, 'ShareASale'),
        (AVANTLINKS, 'Avantilinks')
    )
    retailer_name = models.CharField(verbose_name="Retailer Name", max_length=250, db_index=True)
    domain = models.URLField(max_length=255, db_index=True, blank=True, null=True)
    network =  models.IntegerField(verbose_name="Network", max_length=100, choices=SOURCE_CHOICES, db_index=True)
    base_url = models.URLField(verbose_name="Retail Base URL", max_length=2000,blank=True, null=True)
    merchant_id = models.IntegerField(verbose_name="Merchant ID", blank=True, null=True)
    commision_rate = models.IntegerField(verbose_name="Commision Rate", blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    enable = models.BooleanField(default=True)


class UserRequest(models.Model):
    request = models.ForeignKey(Request, db_index=True)
    request_from = models.CharField(max_length=250, db_index=True)
    source = models.IntegerField(choices=Request.SOURCE_TYPE_OPTIONS, db_index=True)
    user_type = models.IntegerField(choices=Request.USER_TYPE_OPTIONS, db_index=True)
    is_deleted = models.BooleanField(default=False, db_index=True)
    mark_as_price_drop = models.BooleanField(default=False)
    priceit_type = models.IntegerField(choices=Request.PRICEIT_TYPES,blank=True, null=True, db_index=True)
    channel = models.CharField(max_length=20, blank=True, null=True)
    is_mixpanel_result_pushed = models.BooleanField(default=False)
    ip = models.GenericIPAddressField(blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True, max_length=20)
    longitude = models.FloatField(blank=True, null=True, max_length=20)
    is_buying_tips_registered = models.BooleanField(default=False)
    is_price_drop_alert_registered = models.BooleanField(default=False)
    is_price_drop_alert_shown = models.BooleanField(default=False)
    is_buying_tips_pushed = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True, db_index=True)
    udpated_on = models.DateTimeField(auto_now=True, db_index=True)

"""
Models to store the
    Best Price
    Similar Products
    Used Products
for each request
"""
class Processing(models.Model):
    AUTO = 1
    MANUAL = 2
    MODE_OPTIONS = (
        (AUTO, 'AUTO'),
        (MANUAL, 'MANUAL')
    )
    MANUAL_BEST_PRICE = 1
    USE_SAME = 2
    AUTOMATED_BEST_PRICE = 3
    INDIX_API = 4
    SEMANTICS3_API = 5
    BEST_PRICE_SOURCE = (
        (MANUAL_BEST_PRICE, 'MANUAL'),
        (USE_SAME, 'USED SAME'),
        (AUTOMATED_BEST_PRICE, 'SELECTED FROM AUTOMATED RESULT'),
        (INDIX_API, 'INDIX API'),
        (SEMANTICS3_API, 'SEMANTICS3 API')
    )
    request = models.ForeignKey(Request, unique=True)
    best_price = models.ManyToManyField('BrandFavourite.ProductsV2',
                                  blank=True, null=True,
                                  related_name='best_products',
                                  through='PriceitProcessingBestPrice')
    similar = models.ManyToManyField('BrandFavourite.ProductsV2',
        blank=True, null=True, related_name="similar_products")
    used = models.ManyToManyField('BrandFavourite.ProductsV2',
        blank=True, null=True, related_name="used_products")
    created_on = models.DateTimeField(auto_now_add=True)
    udpated_on = models.DateTimeField(auto_now=True)
    coupons = models.ManyToManyField(RequestProductCoupon,
                                blank=True, null=True)


    mode = models.IntegerField(choices=MODE_OPTIONS, blank=True, null=True)
    best_price_source = models.IntegerField(choices=BEST_PRICE_SOURCE,
                             blank=True, null=True)

    def get_best_price(self):
        # best_price = self.best_price.all().order_by('price_sold')
        best_price = PriceitProcessingBestPrice.objects.filter(
            processing=self, productsv2__price_sold__gt=0.0,
            is_hide=False).distinct().order_by('productsv2__price_sold')
        if not self.request.product:
            return ''
        if best_price.exists() :
            best_price = best_price[0].productsv2
            if best_price.price_sold > self.request.product.price_sold:
                best_price = self.request.product
            elif best_price.price_sold == self.request.product.price_sold:
                best_price = self.request.product
            return best_price
        return ''


    def get_percentage_saved(self):
        best_price = self.get_best_price()
        if best_price:
            # tmp['best_price'] = best_price.price_sold
            if self.request.product.price_sold > best_price.price_sold:
                percentage_saved = (self.request.product.price_sold -
                    best_price.price_sold) /self.request.product.price_sold * 100
                # Below line is commented because we need rounded integer as % savings
                # Since rounding operation is not done in extension front end.
                # (iOS and Android apps perform rounding at their end.)
                # percentage_saved = abs(round(percentage_saved,2))
                percentage_saved = int(round(percentage_saved))

                return percentage_saved
        return 0

    def get_percentage_saved_for_deals(self):
        best_price = self.get_best_price()
        if best_price:
            # tmp['best_price'] = best_price.price_sold
            if self.request.product.price > best_price.price_sold:
                percentage_saved = (self.request.product.price -
                    best_price.price_sold) /self.request.product.price * 100
                # Below line is commented because we need rounded integer as % savings
                # Since rounding operation is not done in extension front end.
                # (iOS and Android apps perform rounding at their end.)
                # percentage_saved = abs(round(percentage_saved,2))
                percentage_saved = int(round(percentage_saved))
                return percentage_saved
            elif self.request.product.price_sold > best_price.price_sold:
                percentage_saved = (self.request.product.price_sold -
                    best_price.price_sold) /self.request.product.price_sold * 100
                # Below line is commented because we need rounded integer as % savings
                # Since rounding operation is not done in extension front end.
                # (iOS and Android apps perform rounding at their end.)
                # percentage_saved = abs(round(percentage_saved,2))
                percentage_saved = int(round(percentage_saved))
                return percentage_saved
        return 0


class PriceitProcessingBestPrice(models.Model):
    processing = models.ForeignKey(Processing)
    productsv2 = models.ForeignKey('BrandFavourite.ProductsV2')
    product_order = models.IntegerField(blank=True, null=True, max_length=3)
    is_manual = models.BooleanField(default=False)
    is_hide = models.BooleanField(default=False)

    class Meta:
        managed = False
        auto_created = True
        db_table = 'PriceIT_processing_best_price'
        unique_together = (('processing', 'productsv2'),)

    def get_product_dict(self):
        product_dict = {}

        # Product check
        product = self.productsv2
        if not product:
            return product_dict

        request = self.processing.request
        if request:
            user = request.user
            if user:
                user = user.id

        is_mobile_request = False
        is_extension_request = False

        if request.source in [Request.MOBILE_APP_ANDROID,
            Request.MOBILE_APP_IOS]:
            is_mobile_request = True
        elif request.source == Request.CHROME_EXTENSION:
            is_extension_request = True

        product_dict['is_manual'] = self.is_manual

        # Get product details.
        product_dict['price'] = product.price_sold
        product_dict['purchase_url'] = product.\
                get_purchase_url_with_affiliate_params(
                user_id=user,
                encode=True,
                is_mobile_request=is_mobile_request,
                is_extension_request=is_extension_request)
        product_dict['encoded_purchase_url'] = product_dict['purchase_url']
        product_dict['item_id'] = product.id
        product_dict['original'] = product.id == request.product.id
        product_dict['data_source'] = product.get_data_source_display() or ''
        # Get store details
        store = product.store
        if store:
            product_dict['name'] = store.display_name or store.name
            product_dict['store_id'] = store.id
            product_dict['store_name'] = store.name
            product_dict['logo'] = store.get_logo()
            product_dict['square_logo'] = store.get_square_logo()
            product_dict['full_logo'] = store.get_full_logo()
            product_dict['variation_type'] = store.get_store_variation()

        return product_dict


class FbBotUsers(models.Model):
    MALE = 1
    FEMALE = 2
    GENDER = (
        (MALE,'MALE'),
        (FEMALE,'FEMALE')
        )

    facebook_id = models.CharField(unique=True, max_length=50, db_index=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(blank=True,null=True)
    gender = models.IntegerField(choices=GENDER, blank=True,null=True)


class DealsFeedType(models.Model):
    feed_type = models.CharField(max_length=250, unique=True)
    feed_label = models.CharField(max_length=250)
    active = models.BooleanField(default=True)
    order = models.IntegerField(max_length=20)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    banner_image = models.ImageField(upload_to='custompic/', blank=True, null=True)
    mobile_image = models.ImageField(upload_to='custompic/', blank=True, null=True)
    desktop_image = models.ImageField(upload_to='custompic/', blank=True, null=True)

    def __unicode__(self):
        return str(self.feed_label)

    class Meta:
        verbose_name = "Deal Feed Type"
        verbose_name_plural = "Deals Feed Type"


import urllib
from core.deep_link_monetizer.get_deep_link import generate_deep_link
from core.utils import get_top_level_domain_from_url_v2
from core.viglink.generate_affiliate_url import get_viglink_url
from django.conf import settings

def get_affiliate_url(purchase_url, user_id='', is_extension_request=False,
                      build="production", is_mobile_request=False,
                      skimlinks_enabled=True, viglinks_enabled=False):
    """
    Generate affiliate link
    """
    affiliate_url = generate_deep_link(purchase_url, user_id, is_extension_request=is_extension_request, build=build)
    if not affiliate_url:
        retailer_name = get_top_level_domain_from_url_v2(purchase_url)
        url = urllib.unquote(purchase_url).decode('utf8')
        # Check products from amazon store.
        # Rj want to enable viglink for amazon
        if is_extension_request == False and retailer_name and retailer_name.lower() == "amazon":
            # aff_url = get_viglink_url_v3(purchase_url)
            # if aff_url: return aff_url
            """params = {'tag':settings.AMAZON_AFFILIATE_TAG}
            url_parts = list(urlparse.urlparse(url))
            # Make the querystrings into the dict
            query = dict(urlparse.parse_qsl(url_parts[4]))
            # updating the querystring with the parameters
            query.update(params)
            url_parts[4] = urlencode(query)
            #Appending the updated querystring into the url
            affiliate_url = urlparse.urlunparse(url_parts)"""
        # Deep Links Monetization CJ/PJ/LINKSHARE
        if skimlinks_enabled and is_extension_request == False and not affiliate_url and url:
            skim_link_id = getattr(settings, 'SKIMLINKS_PRICE_COM')
            if is_mobile_request:
                skim_link_id = getattr(settings, 'SKIMLINKS_PRICE_COM_APP')
            skimlink_base_url = "https://go.redirectingat.com/?id={}&".format(skim_link_id)
            if user_id:
                xcust = user_id
            else:
                xcust = ''
            data = {'url': url, 'xcust': xcust}
            url_params = urllib.urlencode(data)
            affiliate_url = skimlink_base_url + url_params
        if viglinks_enabled:
            aff_url = get_viglink_url(url)
            if aff_url: return aff_url

    if not affiliate_url:
        affiliate_url = purchase_url  # Default
    return affiliate_url
