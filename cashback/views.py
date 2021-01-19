import json

from django.conf import settings
from django.shortcuts import HttpResponse
from django.views.decorators.cache import cache_page

from PriceIT.models import WhitelistedDomain

CACHES_TIME_SECONDS = settings.CACHES_TIME_SECONDS

@cache_page(CACHES_TIME_SECONDS)
def get_category_list(request):
    '''
       This method returns list of categoroes from cashback enabled  stores.
    '''

    # Extracting unique category name
    category_list = WhitelistedDomain.CATEGORY_CHOICES

    # Excluding none types
    category_list_data = [category[1] for category in category_list]

    result = {'data': category_list_data}

    return HttpResponse(
        json.dumps(result), content_type="application/json")