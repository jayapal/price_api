from django.db import models
from django.contrib.auth.models import User
import uuid
from django.core.validators import MinValueValidator


# Create your models here.

class Alert(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    object_id = models.CharField(max_length=200, db_index=True)
    product_url = models.URLField(max_length=2000, blank=True, null=True)
    sku = models.CharField(max_length=200, db_index=True, blank=True, null=True)
    vendor_name = models.CharField(max_length=200, blank=True, null=True)
    price_alert = models.FloatField(max_length=20, validators=[MinValueValidator(0.1)])
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    active = models.BooleanField(default=True, db_index=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    notified_timestamp = models.DateTimeField(blank=True, null=True)
    notified_price = models.FloatField(max_length=20, blank=True, null=True, validators=[MinValueValidator(0.1)])
    current_offer_price = models.FloatField(max_length=20, blank=True, null=True, validators=[MinValueValidator(0.1)])
    last_seen = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = (('user', 'object_id', 'active'),)
