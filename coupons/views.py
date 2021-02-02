import datetime
import json
from collections import OrderedDict

from django.db.models import Count, Q
from django.conf import settings
from django.core.cache import cache, caches
from django.http import JsonResponse
from django.shortcuts import HttpResponse

from brand_favourite.api.cache_delete import generate_cache_key_for_url
from coupons.models import FmtcCoupon
from price_it.models import WhitelistedDomain

cache = caches['bigData']


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


def get_coupons(retailer, pdp=False):
    deals_type_mapping = OrderedDict()
    deals_type_mapping['Sitewide Sale'] = ['percent', 'coupon', 'dollar', "offer"]
    if not pdp or pdp.lower() == 'false':
        deals_type_mapping['Department Sale'] = ['category-sale', 'category-coupon']
        deals_type_mapping['Free Shipping'] = ['freeshipping']
        deals_type_mapping['Free Gift'] = ['gift']
        deals_type_mapping['Product Deals'] = ['sale', 'product-coupon', 'product-sale']
    coupons_list = OrderedDict()
    for k, v in deals_type_mapping.items():
        coupons_list[k] = []
    coupons = FmtcCoupon.objects.filter(
        EndDate__gte=datetime.datetime.now().date(), is_active=True, store__name=retailer
    ).annotate(null_position=Count("Rating")).order_by('-null_position', "-Rating")
    if pdp and pdp.lower() == 'true':
        coupons = coupons.exclude(Code='')
    for each in coupons:
        output = {}
        try:
            deals_types = eval(each.Types)
        except:
          deals_types = []
        print(each.Types, deals_types)

        matched_department = None
        for ty in deals_types:
            for k, v in deals_type_mapping.items():
                if str(ty).lower() in v:
                     matched_department = k
                     output["matched_deal_type"] = ty
                     break
            if matched_department:
                break
        if not matched_department:
            continue
        output["offer_url"] = each.AffiliateURL
        output["offer_id"] = each.CouponID
        output["offer_rating"] = each.Rating
        output["offer_label"] = each.Label
        output["offer_code"] = each.Code
        output["offer_types"] = eval(each.Types)
        output["offer_expires_at"] = str(each.EndDate)
        output["matched_department"] = matched_department
        if matched_department in coupons_list.keys():
            coupons_list[matched_department].append(output)
        else:
            coupons_list[matched_department] = [output]
    # Modified in Python3
    new_coupons_list = coupons_list.copy()
    for k, v in coupons_list.items():
        if len(v) == 0:
            new_coupons_list.pop(k)
    try:
        retailerHandling = eval(coupons[0].store.retailerHandling)
    except:
        retailerHandling = {}
    result = {'data': new_coupons_list, 'retailerHandling': retailerHandling}
    return result


def coupon_details(request):
    cache_key = generate_cache_key_for_url(url=request.build_absolute_uri(), key_prefix='offers_details')
    if cache_key in cache:
        print("CACHED")
        # Yeah we have cached data
        data = cache.get(cache_key)
        return JsonResponse(data)
    retailer = request.GET.get("retailer", '')
    merchant = request.GET.get("merchant", '')
    pdp = request.GET.get("pdp", '')
    if not retailer and merchant:
        retailer = merchant
    if not retailer:
        return JsonResponse({'error': "Retailer missing"}, status=400)
    result = get_coupons(retailer, pdp)
    cache.set(cache_key, result, 604800)
    return JsonResponse(result)
