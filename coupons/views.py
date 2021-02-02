import datetime
import json
from collections import OrderedDict

from django.db.models import Count, Q
from django.conf import settings
from django.core.cache import cache
from django.shortcuts import HttpResponse

from brand_favourite.api.cache_delete import generate_cache_key_for_url
from coupons.models import FmtcCoupon
from price_it.models import WhitelistedDomain


def coupon_list(request):
    """
    API which return cash back enabled Stores
    from WhitelistedDomain model. This API supports
    sort_by as well.

    @params sort_by:  aplhabetical/max_cashback/order
    """
    cache_key = generate_cache_key_for_url(url=request.build_absolute_uri(), key_prefix='offers_list')
    if cache_key in cache:
        print("CACHED")
        # Yeah we have cached data
        data = cache.get(cache_key)
        return HttpResponse(data, content_type="application/json")

    cash_back_stores = WhitelistedDomain.objects.filter(
        coupon_enabled=True, number_of_coupons__gt=0
    )
    sort_by = request.GET.get("sort_by", "").strip().lower()
    category = request.GET.get("category", "").strip().lower()
    show_by = request.GET.get("show_by", "").strip().lower()
    page = request.GET.get("page", "").strip()
    retailers = request.GET.get("retailers", [])
    merchants = request.GET.get("merchants", [])
    pdp = request.GET.get("pdp", False)
    if not retailers and merchants:
        retailers = merchants
    next_page = None
    current_page = None
    total_page = None
    print("retailers", retailers)
    if show_by and not page:
        page = 0
    try:
        page = int(page) + 1
    except:
        page = ""

    if 'cashback' in sort_by:
        cash_back_stores = cash_back_stores.extra(
            {'cashback_display_int': "CAST(cashback_display_name as UNSIGNED)"}
        )

    # Lets apply order of results
    if sort_by and sort_by == "aplhabetical":
        cash_back_stores = cash_back_stores.order_by("name")
    elif sort_by and sort_by == "max_cashback":
        cash_back_stores = cash_back_stores.order_by("-cashback_display_int")
    elif sort_by and sort_by == "min_cashback":
        cash_back_stores = cash_back_stores.order_by("cashback_display_int")
    elif sort_by and sort_by == "order":
        cash_back_stores = cash_back_stores.annotate(
            null_position=Count('order')).order_by('-null_position', "order")
    if category:
        # Filter by category
        cash_back_stores = cash_back_stores.filter(category__contains=category)
    if retailers:
        retailers = [x.strip() for x in retailers.split(",")]
        print(retailers)
        cash_back_stores = cash_back_stores.filter(name__in=retailers)
    total_retailers = cash_back_stores.count()
    if show_by:
        try:
            show_by = int(show_by)
            if page:
                try:
                    # Slicing data based on page number and show_by count.
                    page = int(page)
                    current_page = page - 1
                    print(current_page, page)
                    start = show_by * (page - 1)
                    end = show_by * page
                    print("end", end, "total_retailers", total_retailers)
                    total_page = int(round(total_retailers / show_by) + 1)
                    if end > total_retailers:
                        next_page = None
                        current_page = None
                    else:
                        next_page = page
                    cash_back_stores = cash_back_stores[start:end]
                except Exception as e:
                    print(e)
                    cash_back_stores = cash_back_stores[:show_by]
            else:
                cash_back_stores = cash_back_stores[:show_by]
        except:
            pass
    stores_list = OrderedDict()
    for supported in cash_back_stores:
        print(supported.name)
        store_logo = ""
        image_square = ""
        if supported.logo:
            store_logo = str(settings.AWS_CLOUDFRONT_URL) + str(supported.logo)
        if supported.image_square:
            image_square = str(settings.AWS_CLOUDFRONT_URL) + str(supported.image_square)
        output = {
            'retailer_logo': store_logo,
            'retailer_domain': supported.domain,
            'retailer_name': supported.name,
            'order': supported.order,
            'category': supported.category or '',
            'offer_enabled': supported.coupon_enabled,
            'number_of_offers': supported.number_of_coupons,
            'retailer_logo_square': image_square
        }
        coupons = FmtcCoupon.objects.filter(
            EndDate__gte=datetime.datetime.now().date(), is_active=True, store__name=supported.name
        ).annotate(
            null_position=Count("Rating")).order_by('-null_position', "Rating")
        if pdp and pdp.lower() == 'true':
            coupons = coupons.exclude(Code='')
            coupons = coupons.filter(
                Q(Types__icontains='percent') | Q(Types__icontains='coupon') | Q(Types__icontains='dollar') | Q(
                    Types__icontains='offer'))
        if coupons.exists():
            each = coupons[0]
            output["top_rated_offer_url"] = each.AffiliateURL
            output["offer_rating"] = each.Rating
            output["offer_label"] = each.Label
            output["offer_code"] = each.Code
            output["offer_types"] = eval(each.Types)
            output['number_of_offers'] = coupons.count()
            output["offer_expires_at"] = str(each.EndDate) if each.EndDate else None
        else:
            # pass
            continue
        key_name = supported.name
        for r in retailers:
            if r.lower() == supported.name.lower():
                key_name = r
                break
        stores_list[key_name] = output
    result = {'offers': stores_list}

    pagination = {
        'current_page': current_page,
        'next_page': next_page,
        'total_page': total_page,
        'total_retailers': total_retailers
    }
    result["pagination"] = pagination
    result = json.dumps(result)
    cache.set(cache_key, result, 604800)
    return HttpResponse(result, content_type="application/json")
