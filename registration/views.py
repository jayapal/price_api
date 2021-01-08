from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.shortcuts import HttpResponse, HttpResponseRedirect
from django.http.response import HttpResponseBadRequest
from django.views.generic.edit import FormView
from django.views.generic import View
from django.core.paginator import InvalidPage
from django.template.loader import render_to_string
from django.contrib.auth import logout
from django.http import Http404
from django.conf import settings
from django.views.generic import ListView
from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives
from django.contrib.sites.models import Site
from django.template.defaultfilters import truncatewords as truncate_words
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import redirect
from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives
from django.contrib.auth.models import User , Group
from django.db.models import Q
from django.contrib.auth import authenticate, login
from django.core.urlresolvers import reverse_lazy , reverse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.template import Context
from urlparse import urlparse
from django.utils import timezone
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from Klutterapp.models import UserProfile, SubscribedUser, UserSignUp
from mailchimp import utils
from core.ebay.ebay_new import get_ebay_new_top_rated_products
import json,datetime, tldextract
from PriceIT.models import *
from PriceIT.forms import (ManulBestPriceForm, SimilarProductForm,
                           SimilarProductFormSet, RequestProductCouponForm,
                           RequestProductCouponFormset)
from PriceIT.push_notification import send_urbanairship_push_notification

from priceapp_diffbot import get_market_place_id
from BrandFavourite.models import (ProductsV2, ProductsV2Photo, Stores,
                                   Brand, FavouriteV2, Archive, AdminEmails,
                                   BetaUser, ProductCoupons)
from PriceIT.push_notification import send_refresh_push_notification

from coupons.models import Coupon
from Klutterapp.views.webapp import get_uuid
from Klutterapp.models import UserProfile
from image_deduplicator import get_image_hash_and_content_from_url
from BrandFavourite.tasks import save_image_from_content
from .tasks import (save_products, save_actual_product, get_total_saved,
                            save_actual_product_using_upc, crawl_all_products,
                            do_we_need_to_mark_request_as_under_review_wrapper,
                            save_product_min_max_price, save_title_desc_from_algolia)

from .product_utils import check_exisiting_purchase_url
from .push_notification import send_push_notification

from django.core.serializers.json import DjangoJSONEncoder
from Klutterapp.models import UserProfile

from PriceIT.twotap_api import create_cart_and_get_status_for_purchase_url_list

from notifications.models import NotificationType, UserNotification, send_price_drop_push_notification
from notifications.utils import add_notification
from Klutterapp.utils import add_login_user_activity
from PriceIT.tasks import error_mail_notification, save_request_params_to_algolia, save_price_category_using_categorization
from PriceIT.pubnub_utils import send_pubnub_coupon_notification
from PriceIT.coupons_email import send_coupon_email
from mypubnub import send_done_processing_publish_message

from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from mixpanel_analytics import mixpanel_coupons_found_track

from core.utils import get_ip_from_request
from core.zinrello.award_points import do_award_price_point

from PriceIT.price_point_history_utils import create_price_point_history
from core.semantics3_api.semantics3_best_price import \
    get_best_price_from_semantics3_api
from core.semantics3_api.item_lookup_using_upc import \
    get_product_details_from_semantic

from core.indix.indix_best_price import \
   get_best_price_from_indix_api
from core.indix.item_lookup_using_upc import \
   get_product_details_from_indix_using_upc
import urllib

from push_notification import send_referral_push_notification
from BrandFavourite.views_productsv2 import get_domain_name
from core.get_sku.driver import url_to_sku
import requests
import logging
from algoliasearch import algoliasearch
from django.contrib.sites.models import Site
import eventlet
from eventlet.green import urllib2

logger = logging.getLogger('scraping')


@csrf_exempt
def get_user_with_email(request):
    """
    Get a user if email already exists or else add a new user
    """
    from django.core.validators import validate_email
    from django.core.exceptions import ValidationError
    from core.utils import get_ip_from_request
    if request.method == 'GET':
        data = {'error': 'Invalid Entry.','result': False}
        return HttpResponse(json.dumps(data),
                content_type="application/json")
    email = request.POST.get('email')
    password = request.POST.get('password')
    source = request.POST.get('source', 'android').strip()
    if source == '':
        source = "APP"
    activity_source = Request.MOBILE_APP
    source = str(source).upper()
    print source
    print email
    print type(email)
    try:
        validate_email(email)
    except ValidationError as e:
        print "e", e
        return HttpResponse(json.dumps(["Email not valid"]))
    if email and password:
        try:
            user = User.objects.get(Q(username=email)|Q(email=email))
            if not user.password:
                user.set_password(password)
                user.save()
        except User.DoesNotExist:
            user, created = User.objects.get_or_create(username=email[:30],
                email=email)
            if created:
                user.set_password(password)
            user.is_active = True
            user.save()
        if source == "EXTENSION":
            signup_source = UserSignUp.CHROME_EXTENSION
            activity_source = Request.CHROME_EXTENSION
        elif source == "IOS":
            signup_source = UserSignUp.MOBILE_APP_IOS
            activity_source = Request.MOBILE_APP_IOS
        elif source == "ANDROID":
            signup_source = UserSignUp.MOBILE_APP_ANDROID
            activity_source = Request.MOBILE_APP_ANDROID
        elif source == "PRICE.COM_WEB":
            signup_source = UserSignUp.PRICE_DOT_COM_WEB
            activity_source = Request.PRICE_DOT_COM_WEB
        elif source == "PRICE.COM_MOBILE":
            signup_source = UserSignUp.PRICE_DOT_COM_MOBILE
            activity_source = Request.PRICE_DOT_COM_MOBILE
        else:
            signup_source = UserSignUp.MOBILE_APP_ANDROID
            activity_source = Request.MOBILE_APP_ANDROID

        ip_address = get_ip_from_request(request)

        '''# Check user already exists
        user_signup = UserSignUp.objects.filter(user=user, source=signup_source)
        if not user_signup :
            # Add user's ip
            UserSignUp.objects.create(user=user, source=signup_source, ip=ip_address)'''

        if user.is_active:
            user_obj, created = UserProfile.objects.get_or_create(user=user)
            # user referral code
            if created and 'referral_code' in request.POST:
                referral_code = request.POST.get('referral_code', '').strip()
                if referral_code and referral_code.lower() != "null":
                    user_obj.referral_code=referral_code
                    user_obj.save()
            if created and 'referral_from' in request.POST:
                referral_from = request.POST.get('referral_from', '').strip()
                if referral_from and referral_code.lower() != "null":
                    user_obj.referral_source=referral_from
                    user_obj.save()
            # This store referred by which user
            """if created and 'referred_by' in request.POST:
                referred_by = request.POST.get('referred_by', '').strip()
                if referred_by:
                    try:
                        referred_by = User.objects.get(pk=referred_by)
                        user_obj.referred_by=referred_by
                        user_obj.save()

                        # Increment referrer price points by 50.
                        user_profile_obj = UserProfile.objects.get(user=referred_by)
                        try:
                            create_price_point_history(referred_by, 
                                    user_profile_obj.price_points, 
                                    settings.REFERRAL_POINTS, "referral_sign_up")
                        except Exception as e:
                            pass
                        user_profile_obj.price_points += 50
                        user_profile_obj.save()
                        if referred_by.email:
                            email = referred_by.email

                            # Add award price point to zinrello
                            try:
                                do_award_price_point(email, 50, "referral_sign_up")
                            except Exception as e:
                                print e
                            sent_referral_email_to_reffered_by_user(email)
                            send_referral_push_notification(referred_by, dev=False)
                    except Exception as e:
                        print e
                        pass"""

            user_id = user.id
            '''user_login = authenticate(username = user.username, password = password)
            if user_login is not None:
                login(request, user_login)
            else:
                data = {'error': 'Invalid Entry.','result': False}
                return HttpResponse(json.dumps(data),
                     content_type="application/json")'''
            token,created= Token.objects.get_or_create(user=user)
            """if created:
                domain = Site.objects.get_current().domain
                print ("--", domain)
                urls = [ #"{}{}?u={}".format(domain, "/v6/ceo-welcome-email/", user_obj.id),
                         "{}{}?u={}".format(domain, "/v6/ebates_member_create/", user_obj.id)]
                http_host = request.META.get("HTTP_REFERER", "")
                print "http_host", http_host
                logger.info("REMOTE {}".format(request.META.get('HTTP_REFERER') ))
                if http_host and http_host.startswith("https://staging.price.com"):
                #if "@price.com" in user.email:
                    urls.append("{}{}?u={}&temp=1".format(domain, "/v6/ebates_welcome_email/", user_obj.id))
                    #urls.append("{}{}?u={}&temp=2".format(domain, "/v6/ebates_welcome_email/", user_obj.id))
                    #urls.append("{}{}?u={}&temp=3".format(domain, "/v6/ebates_welcome_email/", user_obj.id))
                print (urls)
                pool = eventlet.GreenPool()
                for body in pool.imap(fetch, urls):
                      print "got body", body
                print "------------------------"
                user_obj.refresh_from_db()
                user_obj.is_ebates_day_1_email_sent = True
                user_obj.save()"""
            token = token.key
            if created or source not in user.groups.values_list('name',flat=True):
                group ,created= Group.objects.get_or_create(name=source)
                try:
                    group.user_set.add(user)
                except:
                    pass
                user.set_password(password)
                # if ('price.com' in user.email.lower() or
                #     'tfbnw.net' in user.email.lower() or
                #     'westagilelabs.com' in user.email.lower()):

                # Modifing above if condition and added extra terms
                if any(test_email in user.email.lower() for test_email in [
                    'price.com', 'tfbnw.net', 'westagilelabs.com', 'labglo.com',
                    '.labglo']):
                    group ,created= Group.objects.get_or_create(name="TESTER")
                    try:
                        group.user_set.add(user)
                    except:
                        pass
                user.save()

                # Check user already exists
                user_signup = UserSignUp.objects.filter(user=user, source=signup_source)
                if not user_signup :
                    # Add user's ip
                    try:
                        UserSignUp.objects.create(user=user, source=signup_source, ip=ip_address)
                    except:
                        pass
                total_requests = Request.objects.filter(request_from=user_id,
                  source=Request.SOURCE_TYPE_OPTIONS[Request.CHROME_EXTENSION-1][0],is_deleted=False).count()
                data = {'ids': user_id, 'token': token,
                        'requests':total_requests, 'result': True}
                # Below line is commented because:
                # No need to create login entry for user signup activity.
                # try:
                #     add_login_user_activity(user, activity_source)
                # except Exception, e:
                #     print "exception in login user", e

                return HttpResponse(json.dumps(data),
                    content_type="application/json")

            data = {'present': True, 'token':token, 'result': False}
            return HttpResponse(json.dumps(data),
                    content_type="application/json")
    data = {'error': 'Invalid Entry.','result': False}
    return HttpResponse(json.dumps(data),
                content_type="application/json")
