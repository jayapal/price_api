import hashlib
from django.utils.encoding import force_bytes, force_text, iri_to_uri
from PriceIT.models import (PriceappCacheTable, DealsFeedType,
                            PriceappCacheTableSupportedStores, Request)
from django.http import Http404
from django.shortcuts import HttpResponse, render, redirect
import json
import urlparse
from django.core.cache import cache
from BrandFavourite.models import ProductsV2
from django.contrib.auth.models import User
from price_dashboard.models import CacheVersion


def generate_cache_key_for_url(url, method="GET", headerlist=[], key_prefix=""):
    """Returns a cache key for the URL."""
    ctx = hashlib.md5()
    if '/v2/item-details/' in url:
        print "YES ITS ITEM DETAILS API"
        try:
            key_prefix = get_item_details_prefix(url)
            print "KEY PREFIX", key_prefix
        except:
            pass
    elif '/v2/price/item-details-similar' in url:
        print "YES ITS ITEM SIMILAR API"
        try:
            key_prefix = get_item_similar_details_prefix(url)
            print "KEY PREFIX", key_prefix
        except:
            pass
    elif '/v3/similar/' in url:
        print "YES ITS ITEM SIMILAR API /v3/similar/"
        try:
            key_prefix = get_item_similar_details_prefix(url)
            print "KEY PREFIX", key_prefix
        except:
            pass
    elif '/v2/check/supported/sites' in url:
        print "YES ITS SUPPORTED SITES"
        try:
            key_prefix = get_item_supported_sites_prefix(url)
            print "KEY PREFIX", key_prefix
        except:
            pass

    '''for header in headerlist:
        value = request.META.get(header, None)
        if value is not None:
            ctx.update(force_bytes(value))'''
    url = hashlib.md5(force_bytes(iri_to_uri(url)))
    cache_key = 'views.decorators.cache.cache_page.%s.%s.%s.%s' % (
        key_prefix, method, url.hexdigest(), ctx.hexdigest())
    return "%s.%s" %(cache_key, "en-us")


def get_item_details_prefix(url):
    """
    method used to get Prefix of Item Detail API
    """
    parsed_uri = urlparse.urlparse(url)
    params = urlparse.parse_qs(parsed_uri.query)
    request_id = params.get('request_id','')
    user_id = params.get('user_id','')
    item_id = ''
    prefix = ''
    request_obj = ''
    # if we have request_id in params
    if request_id:
        request_id = request_id[0]
    if user_id:
        user_id = user_id[0]
    # get the item_id and get the equivalent request_id
    if not request_id:
        for val in parsed_uri.path.split('/'):
            try:
                item_id = int(val)
                break
            except:
                pass
    print "item_id", item_id
    print "re_id", request_id
    print "u_id", user_id
    if request_id:
        try:
            request_obj = Request.objects.get(pk=request_id)
        except Exception as e:
            print e
            pass
    if not request_obj and user_id and item_id:
        request_obj = Request.objects.filter(product__id=item_id,
            request_from=user_id).order_by('-id').first()
    if request_obj:
        prefix = "ITEM-DETAILS-{}-{}".format(request_obj.pk, request_obj.api_version)
    print prefix
    return prefix


def get_item_similar_details_prefix(url):
    """
    method used to get Prefix of Item Similar Detail API
    """
    parsed_uri = urlparse.urlparse(url)
    params = urlparse.parse_qs(parsed_uri.query)
    request_id = params.get('request_id','')
    user_id = params.get('user_id','')
    item_id = ''
    prefix = ''
    request_obj = ''
    # if we have request_id in params
    if request_id:
        request_id = request_id[0]
    if user_id:
        user_id = user_id[0]
    # get the item_id and get the equivalent request_id
    if not request_id:
        for val in parsed_uri.path.split('/'):
            try:
                item_id = int(val)
                break
            except:
                pass
    print "item_id", item_id
    print "re_id", request_id
    print "u_id", user_id
    if request_id:
        try:
            request_obj = Request.objects.get(pk=request_id)
        except Exception as e:
            print e
            pass
    if not request_obj and user_id and item_id:
        request_obj = Request.objects.filter(product__id=item_id,
            request_from=user_id).order_by('-id').first()
    if request_obj:
        prefix = "ITEM-SIMILAR-DETAILS-{}-{}".format(request_obj.pk, request_obj.similar_api_version)
    print prefix
    return prefix


def get_item_supported_sites_prefix(url):
    """
    method used to get Prefix of Supported site API
    """
    cache_version, created = CacheVersion.objects.get_or_create(view_name="supported_sites")
    prefix = "SUPPORTED_STORES-{}".format(cache_version.version)
    print prefix
    return prefix
