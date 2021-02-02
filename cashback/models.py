from django.db import models
from django.contrib.auth.models import User

from brand_favourite.models import Stores
from price_it.models import WhitelistedDomain


class CashbackTransaction(models.Model):
    PENDING = 'Pending'
    APPROVED = 'Approved'
    CANCELLED = 'Cancelled'
    STATUS_CHOICES = (
        (PENDING, PENDING),
        (APPROVED, APPROVED),
        (CANCELLED, CANCELLED)
    )

    transaction_id = models.CharField(max_length=100)
    network = models.CharField(max_length=10, choices=WhitelistedDomain.NETWORK_CHOICES)
    user_id = models.IntegerField(max_length=100, blank=True, null=True)
    price_user = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE)
    retailer = models.CharField(max_length=100, blank=True, null=True)
    network_user_id = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING)
    card_number = models.CharField(max_length=10, blank=True, null=True)
    merchant = models.ForeignKey(Stores, blank=True, null=True, on_delete=models.CASCADE)
    cashback = models.FloatField(blank=True, null=True)
    commission_earned = models.FloatField(blank=True, null=True)
    commission_type = models.CharField(max_length=100, blank=True, null=True)
    productUrl = models.URLField(max_length=1000, blank=True, null=True)
    salePrice = models.FloatField(blank=True, null=True)
    purchased_on = models.DateTimeField(blank=True, null=True)
    approved_on = models.DateTimeField(blank=True, null=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_on = models.DateTimeField(auto_now_add=True)
    sent_email_is_pending = models.BooleanField(default=False)
    sent_email_is_approved = models.BooleanField(default=False)
