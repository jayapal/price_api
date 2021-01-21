from django.db import models


class CacheVersion(models.Model):
    view_name = models.CharField(unique=True, max_length=250)
    version = models.IntegerField(default=1)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'price_dashboard_cacheversion'
