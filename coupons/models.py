from django.db import models

from brand_favourite.models import Stores, Source


class FmtcCoupon(models.Model):
    #API Fields
    CouponID = models.CharField(unique=True, max_length=255, db_index=True, blank=True, null=True)
    MerchantID = models.CharField(max_length=500, db_index=True, blank=True, null=True)
    Brands = models.TextField(blank=True, null=True)
    Merchant = models.CharField(max_length=500, db_index=True, blank=True, null=True)
    MasterMerchantID = models.CharField(max_length=500, db_index=True, blank=True, null=True)
    Network = models.CharField(max_length=500, db_index=True, blank=True, null=True)
    ProgramID = models.CharField(max_length=500, db_index=True, blank=True, null=True)
    Label = models.CharField(max_length=500, db_index=True, blank=True, null=True)
    Code = models.CharField(max_length=500, db_index=True, blank=True, null=True)
    Image =  models.URLField(max_length=1000, blank=True, null=True)
    StartDate = models.DateTimeField(blank=True, null= True)
    EndDate = models.DateTimeField(blank=True, null= True)
    AffiliateURL = models.URLField(max_length=1000, blank=True, null=True)
    SkimlinksURL =  models.URLField(max_length=1000, blank=True, null=True)
    FreshReachURL =  models.URLField(max_length=1000, blank=True, null=True)
    DirectURL =  models.URLField(max_length=1000, blank=True, null=True)
    FMTCURL = models.CharField(max_length=500, blank=True, null=True)
    SubAffiliateURL = models.URLField(max_length=1000, blank=True, null=True)
    PixelHTML = models.CharField(max_length=500,  blank=True, null=True)
    Restrictions = models.TextField(blank=True, null=True)
    Categories = models.TextField(blank=True, null=True)
    CategoriesV2 = models.TextField(blank=True, null=True)
    Types = models.CharField(max_length=500, db_index=True, blank=True, null=True)
    Status = models.CharField(max_length=500, db_index=True, blank=True, null=True)
    Created = models.DateTimeField(blank=True, null= True)
    LastUpdated = models.DateTimeField(blank=True, null= True)
    SalePrice = models.FloatField(blank=True, null=True)
    Discount = models.FloatField(blank=True, null=True)
    WasPrice = models.FloatField(blank=True, null=True)
    DollarsOff = models.CharField(max_length=500,  blank=True, null=True)
    Percent = models.CharField(max_length=500, blank=True, null=True)
    Threshold = models.CharField(max_length=500, blank=True, null=True)
    Rating = models.FloatField(blank=True, null=True)
    Starred = models.BooleanField(default=False)
    LinkID = models.CharField(max_length=500, blank=True, null=True)
    Local = models.CharField(max_length=500, blank=True, null=True)
    #Custom Field
    store = models.ForeignKey(Stores, on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)


class Coupon(models.Model):
    TYPE_CHOICES = (
        ('subscription', 'subscription'),
        ('revshare', 'revshare'),
    )

    name = models.CharField(max_length=100)
    store = models.ForeignKey(Stores)
    source = models.ForeignKey(Source)
    code = models.CharField(max_length=100, db_index=True, blank=True, null=True)
    description = models.CharField(max_length=750, blank=True, null= True)
    network_label = models.CharField(max_length=100, db_index=True, blank=True, null=True)
    code_url = models.URLField(max_length=1000, blank=True, null=True)
    location_url = models.URLField(max_length=1000, blank=True, null=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(blank=True, null= True)
    valid = models.BooleanField(default=True)
    #rank = models.IntegerField(blank=True, null=True)
    rating = models.FloatField(blank=True, null=True)
    coupon_id = models.IntegerField(db_index=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True, db_index=True)
    token_type = models.CharField(null=True, blank=True, max_length=50,
        choices=TYPE_CHOICES)

    class Meta:
        unique_together = (('source', 'coupon_id'),)
