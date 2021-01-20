import json

from django.conf import settings
from django.core.cache import caches
from django.shortcuts import HttpResponse
from django.views.decorators.cache import cache_page

from brand_favourite.api.cache_delete import generate_cache_key_for_url
from price_it.models import WhitelistedDomain

CACHES_TIME_SECONDS = settings.CACHES_TIME_SECONDS

cache = caches['bigData']

@cache_page(CACHES_TIME_SECONDS)
def get_category_list(request):
    """
       This method returns list of categories from cashback enabled  stores.
    """

    # Extracting unique category name
    category_list = WhitelistedDomain.CATEGORY_CHOICES

    # Excluding none types
    category_list_data = [category[1] for category in category_list]

    result = {'data': category_list_data}

    return HttpResponse(
        json.dumps(result),
        content_type="application/json"
    )


def get_tracking_affil_url(affiliate_url, network, user_id):
    if network == WhitelistedDomain.CJ:
        try:
            index = affiliate_url.find('/http')
            if index:
                return affiliate_url[:index]+"/sid/{}".format(user_id) + affiliate_url[index:]
        except:
            pass
    id_tags = {
        WhitelistedDomain.PJ: "sid",
        WhitelistedDomain.CJ: "sid",
        WhitelistedDomain.LS: "u1",
        WhitelistedDomain.ImpactRadius: "subId1",
        WhitelistedDomain.ShareASale: "afftrack",
        WhitelistedDomain.FlexOffers: "fobs",
        WhitelistedDomain.Ebay: "customid",
        WhitelistedDomain.Awin: "p1",
        WhitelistedDomain.Viglink: "cuid",
    }
    params = {id_tags[network]:user_id}
    url_parts = list(urlparse.urlparse(affiliate_url))
    # Make the querystrings into the dict
    query = dict(urlparse.parse_qsl(url_parts[4]))
	# updating the querystring with the parameters
    query.update(params)
    url_parts[4] = urlencode(query)
    #Appending the updated querystring into the url
    deep_link = urlparse.urlunparse(url_parts)
    print "deep_link", deep_link
    return deep_link


def cash_back_stores_list(request):
    """
    API which return cash back enabled Stores
    from WhitelistedDomain model. This API supports
    sort_by as well.

    @params sort_by:  aplhabetical/max_cashback/order
    """
    cache_key = generate_cache_key_for_url(url=request.build_absolute_uri(), key_prefix='CASHBACK_STORESV3')
    if cache.has_key(cache_key):
        print "CACHED"

        # Yeah we have cached data
        data = cache.get(cache_key)
        return HttpResponse(data,
             content_type="application/json")

    cash_back_stores = WhitelistedDomain.objects.filter(
        cashback_enabled=True)
    sort_by = request.GET.get("sort_by", "").strip().lower()
    user_id = request.GET.get("user_id", "").strip()
    category = request.GET.get("category", "").strip().lower()
    show_by = request.GET.get("show_by", "").strip().lower()
    page = request.GET.get("page", "").strip()
    retailers = request.GET.get("retailers", [])
    featured = request.GET.get("featured", False)

    next_page = None
    current_page = None
    total_page = None

    if show_by and not page:
        page = 0

    try:
        page = int(page) + 1
    except:
        page = ""
    print ("sort_by", sort_by)

    if 'cashback' in sort_by:
        cash_back_stores  = cash_back_stores.extra(
            {'cashback_display_int': "CAST(cashback_display_name as UNSIGNED)"})
    if featured:
        cash_back_stores = cash_back_stores.filter(is_featured=True)
        sort_by="order"
    # Lets apply order of results
    if sort_by and sort_by == "aplhabetical":
        cash_back_stores = cash_back_stores.order_by("name")
    elif sort_by and sort_by == "max_cashback":
        print ("sort_by", sort_by)
        cash_back_stores = cash_back_stores.order_by("-commission")
    elif sort_by and sort_by == "min_cashback":
        cash_back_stores = cash_back_stores.order_by("cashback_display_int")
    elif sort_by and sort_by == "order":
        cash_back_stores = cash_back_stores.annotate(
            null_position=Count('order')).order_by('-null_position',"order")
    if category:
        # Filter by category
        cash_back_stores = cash_back_stores.filter(category__contains=category)

    if retailers:
        retailers = [ x.strip() for x in retailers.split(",")]
        print retailers
        cash_back_stores = cash_back_stores.filter(name__in=retailers)
    total_retailers = cash_back_stores.count()
    if show_by:
        try:
            show_by = int(show_by)
            if page:
                try:
                    # Slicing data based on page number and show_by count.
                    page = int(page)
                    current_page = page -1
                    print (current_page, page)

                    start = show_by * (page - 1)
                    end = show_by * page

                    total_page = int(round(total_retailers/show_by) + 1)
                    if end > total_retailers:
                        next_page = None
                        current_page = None
                    else:
                        next_page = page

                    cash_back_stores = cash_back_stores[start:end]
                except Exception as e:
                    print ("ddddddd", e)
                    cash_back_stores = cash_back_stores[:show_by]
            else:
                cash_back_stores = cash_back_stores[:show_by]
        except Exception as e:
            print ("eeeeeeeeee", e)
            pass

    stores_list = []
    for supported in cash_back_stores:
        store_logo = ""
        image_square = ''

        if supported.logo:
            store_logo = str(settings.AWS_CLOUDFRONT_URL)+str(supported.logo)
        if supported.image_square:
            image_square = str(settings.AWS_CLOUDFRONT_URL) + str(supported.image_square)
        affil_url = supported.affiliate_url or supported.domain
        if user_id and supported.cashback_enabled:
            affil_url = get_tracking_affil_url(supported.affiliate_url, supported.network, user_id)
        output = {
            'store_logo': store_logo,
            'store_domain': supported.domain,
            'store_url': affil_url,
            'name': supported.name,
            'store_display_name': supported.name_display or supported.name,
            'order': supported.order,
            'network': supported.network or '',
            'category': supported.category or '',
            'cashback_enabled': supported.cashback_enabled,
            'cashback_value': float(round(supported.commission)) if supported.commission else '',
            'commission_type': supported.commission_type or '',
            'coupon_enabled': supported.coupon_enabled,
            'number_of_coupons': supported.number_of_coupons,
            'image_square': image_square,
        }
        stores_list.append(output)
    pagination = {
        'current_page': current_page,
        'next_page': next_page,
        'total_page':total_page,
        'total_retailers': total_retailers
    }
    result = {'data': stores_list}
    result["pagination"] = pagination
    result = json.dumps(result)
    cache.set(cache_key, result, 604800)
    return HttpResponse(result, content_type="application/json")
