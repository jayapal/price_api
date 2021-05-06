import json, datetime, requests, urllib
from django.utils.text import Truncator
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import (HttpResponse, HttpResponseRedirect,
                              render, render_to_response)
from django.conf import settings
from django.contrib.auth.models import User
# from .models import (Source,SimilarItems,ItemUrls,RowLog,Uploads)
# from .forms import BotRequestForm
from PriceIT.models import Request, Processing, FbBotUsers, UserRequest, DealsFeedType
from PriceIT.product_utils import check_exisiting_purchase_url, check_exisiting_sku
import logging
from core.amazon.utils import RoundFloat
from core.utils import remove_tag_from_amazon, get_amazon_redirect_url, get_walmart_redirect_url, get_url_from_string

from django.db.models import Q
from brand_favourite.models import ProductsV2Stats
import datetime
import time
from datetime import timedelta
from core.algolia.search_by_field import *
from price_it.models import get_affiliate_url
from coupons.models import Coupon
from core.utils import get_top_level_domain_from_url

default_pic = settings.DEFAULT_IMAGE_PATH
FACEBOOK_BOT_KEY = getattr(settings, 'FACEBOOK_BOT_KEY',
                           "EAAITb8FHdPwBADQYAj92uuuce1s9ktSLzOcPdFt9ZBcnjuRlg32zmNabGB4EQU5iqV4eSbcCjx40FW981abmq1fkY0ZBQ2XoNot5ZAiretSwDp2ri29uRdvXux9NPXIRBV30s7k4tLxiRmxdwy66yBRzQ1ygAZBfLzckQXpUkwZDZD")


def priceit_matchos(url):
    """
    New Matchos PriceIT API
    """
    url = urllib.quote(url)
    priceit_api = "https://matchos.price.com/apiv2/item?partner=5b960a4ade2962062eeb1f4a&url={}".format(url)
    print
    priceit_api
    resp = requests.get(priceit_api).json()
    if not resp:
        return False
    product = resp[0]
    product_url = product.get("productUrl")
    store = product.get("retailer")
    title = product.get("productName")
    price = product.get("basePrice")
    # if all([product_url, store, title, price]):
    if product_url:
        pdp_url = "https://price.com/v2/pdp?urls={}".format(url)
        return (pdp_url, title, product.get("imageUrl"))
    return False


def push_match_os_resp(pdp_url, sender):
    url = "{}?utm_source=facebook&utm_medium=chatbot&utm_campaign=fb_chatbot".format(pdp_url)
    headers = {
        'Content-Type': 'application/json',
    }

    data = {
        "recipient": {
            "id": sender
        },
        "message": {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "button",
                    "text": "What do you want to do next?",
                    "buttons": [
                        {
                            "type": "web_url",
                            "url": url,
                            "title": "Compare Deals"
                        },
                    ]
                }
            }}}
    data = json.dumps(data)
    print
    "going to push to fb bot"
    r = requests.post('https://graph.facebook.com/v2.6/me/messages?access_token=%s' % (FACEBOOK_BOT_KEY),
                      headers=headers, data=data)
    print
    r.text
    return HttpResponse(True)


# sample fb bot request
'''{"object":"page","entry":[{"id":272875546382859,"time":1463053386361,"messaging":
[{"sender":{"id":1085729411469984},"recipient":{"id":272875546382859},"timestamp":
1463053355669,"message":{"mid":"mid.1463053355550:ad256c5b11ed0c6652","seq":1872,
"text":"http://www.amazon.in/Apple-iPad-Gold-64GB-WiFi/dp/B00OTWPEBK/ref=sr_1_1?s=electronics&ie=UTF8&qid=1463054936&sr=1-1&keywords=ipad+air+2"}}]}]}'''

logger = logging.getLogger('facebook')


def push_response_to_chatfuel(user_request_obj):
    request_obj = user_request_obj.request
    data = request_obj.get_algolia_params()
    # data['pdp_url'] = "http://staging12.getpriceapp.com/v2/price/request/{}/".format(str(request_obj.pk))
    data = json.dumps(data)
    endpoint = "https://api.chatfuel.com/bots/59f22529e4b0640c0ae1965e/users/{}/send?chatfuel_token=vnbqX6cpvXUXFcOKr5RHJ7psSpHDRzO1hXBY8dkvn50ZkZyWML3YdtoCnKH7FSjC&chatfuel_block_id=59f32571e4b0640c105eb625".format(
        user_request_obj.request_from)
    requests.post(endpoint, data, headers={'Content-type': 'application/json'}).text


def push_best_used_product(user_request_obj):
    request_obj = user_request_obj.request
    upc = request_obj.upc or request_obj.product.upc
    if upc:
        used_count = 0
        try:
            upc = str(int(upc))
        except:
            # If upc has 0 but its alphanumeric then
            if upc.startswith('0'):
                upc = upc[1:]
            pass
        used_product = None
        processing_obj, created = Processing.objects.get_or_create(request=request_obj)
        best_product = processing_obj.get_best_price()
        if best_product:
            best_offer_price = best_product.price_sold
            used_products = processing_obj.used.filter(
                upc__icontains=upc, price_sold__lt=best_offer_price).order_by('-price_sold')
            used_count = used_products.count()
        payload = []
        pilot_data = []
        headers = {
            'Content-Type': 'application/json',
        }

        if used_count == 0:
            return None

        if used_count % 2 != 0 and used_count in [1, 3]:
            for used_product in used_products:
                if str(used_product.store.name).lower() == 'ebay':
                    used_product_affiliate_url = used_product.purchase_url
                else:
                    used_product_affiliate_url = used_product.get_purchase_url_with_affiliate_params(
                        encode=True)
                payload.append({
                    "type": "web_url",
                    "title": "Best Used Option",
                    "url": str(used_product_affiliate_url)
                })

            data = {
                "recipient": {
                    "id": user_request_obj.request_from
                },
                "message": {
                    "attachment": {
                        "type": "template",
                        "payload": {
                            "template_type": "button",
                            "text": "We also found a used product option to help you save even more.",
                            "buttons": payload
                        }
                    }
                }
            }
        else:
            for used_product in used_products[:4]:
                if str(used_product.store.name).lower() == 'ebay':
                    used_product_affiliate_url = used_product.purchase_url
                else:
                    used_product_affiliate_url = used_product.get_purchase_url_with_affiliate_params(
                        encode=True)
                payload.append({
                    "title": str(used_product.title),
                    "image_url": used_product.get_primary_medium_photo(),
                    "default_action": {
                        "type": "web_url",
                        "url": str(used_product_affiliate_url),
                        "webview_height_ratio": "COMPACT"
                    }
                })

            pilot_data = {
                "recipient": {
                    "id": user_request_obj.request_from
                },
                "message": {
                    "text": "We also found a great used alternative to help you save even more.",
                }
            }

            data = {
                "recipient": {
                    "id": user_request_obj.request_from
                },
                "message": {
                    "attachment": {
                        "type": "template",
                        "payload": {
                            "template_type": "list",
                            "top_element_style": "compact",
                            "elements": payload,
                        }
                    }
                }
            }

        if pilot_data:
            pilot_data = json.dumps(pilot_data)
            r = requests.post('https://graph.facebook.com/v2.6/me/messages?access_token=%s' % (FACEBOOK_BOT_KEY),
                              headers=headers, data=pilot_data)

        if data:
            data = json.dumps(data)
            print
            "going to push to fb bot"
            r = requests.post('https://graph.facebook.com/v2.6/me/messages?access_token=%s' % (FACEBOOK_BOT_KEY),
                              headers=headers, data=data)
            print
            r.text


def check_productv2_stats(product, count=1):
    '''
    This method checks whether the productsv2stats object is recently updated
    or not.
    If true: then returns the min price, max price and avg price
    else: wait for 30 sec and check again if the object is updated recently.

    '''
    try:
        stat_obj = ProductsV2Stats.objects.get(product=product)
    except:
        print
        "No stat instance. Waiting..."
        stat_obj = ''
        return None, None, None

    lastHourDateTime = datetime.datetime.now() - timedelta(hours=5)

    if all([stat_obj, stat_obj.min_price, stat_obj.max_price, stat_obj.avg_price]):
        return stat_obj.min_price, stat_obj.max_price, stat_obj.avg_price

    '''if stat_obj and stat_obj.updated_on >= lastHourDateTime:
        print "Got data"
        # Recently updated. 
        if stat_obj.min_price and stat_obj.max_price:
            return stat_obj.min_price, stat_obj.max_price, stat_obj.avg_price
        else:
            return None, None, None'''
    if stat_obj and stat_obj.status == ProductsV2Stats.COMPLETED:
        return stat_obj.min_price, stat_obj.max_price, stat_obj.avg_price
    else:
        '''# Expired data.
        print "data expired.."
        time.sleep(1)
        if count == 18:
            print "RETURNing"
            return None, None, None
        count += 1
        print "count", count
        return check_productv2_stats(product, count)'''
        return None, None, None


def image_recognition_and_response(image_url, sender):
    from PriceIT.tasks import get_image_details_from_image_url
    headers = {
        'Content-Type': 'application/json',
    }
    data = {
        "recipient": {
            "id": sender
        },
        "message": {
            "text": "Got it! I'm analyzing the image, and I'll send you a message as soon as I've found something."
        }
    }
    data = json.dumps(data)
    r = requests.post('https://graph.facebook.com/v2.6/me/messages?access_token=%s' % (FACEBOOK_BOT_KEY),
                      headers=headers, data=data)
    get_image_details_from_image_url.delay(image_url, sender, FACEBOOK_BOT_KEY)
    return HttpResponse(True)


def register_price_drop_event(user_request_id):
    try:
        user_request_obj = UserRequest.objects.get(pk=user_request_id)
    except:
        return None
    product_title = Truncator(user_request_obj.request.product.title).chars(30)
    if user_request_obj.is_price_drop_alert_registered:
        msg = "Alerts have been activated already for {}".format(product_title)
    else:
        user_request_obj.is_price_drop_alert_registered = True
        user_request_obj.save()
        msg = "Alerts have been activated for {}".format(product_title)
    headers = {
        'Content-Type': 'application/json',
    }
    data = {
        "recipient": {
            "id": user_request_obj.request_from
        },
        "message": {
            "text": msg
        }
    }
    data = json.dumps(data)
    r = requests.post('https://graph.facebook.com/v2.6/me/messages?access_token=%s' % (FACEBOOK_BOT_KEY),
                      headers=headers, data=data)
    return HttpResponse(True)


def push_buying_tips(user_request_id, is_automated=False):
    user_request_obj = UserRequest.objects.get(pk=user_request_id)
    request_obj = user_request_obj.request
    product_title = Truncator(request_obj.product.title).chars(30)
    # Push  message to facebook
    print
    "going to push buying tips"
    msg = ""
    best_price = None
    push_tips = True
    # min_price = request_obj.product.min_price
    # max_price = request_obj.product.max_price
    # avg_price = request_obj.product.get_avg_price()
    min_price, max_price, avg_price = check_productv2_stats(request_obj.product)
    print
    min_price, max_price, avg_price
    processing_obj, created = Processing.objects.get_or_create(request=request_obj)
    best_product = processing_obj.get_best_price()

    if best_product:
        best_price = best_product.price_sold
        print
        "best_price", best_price
    if min_price and max_price and avg_price and best_price:
        min_price = RoundFloat(min_price, places=2)
        max_price = RoundFloat(max_price, places=2)
        avg_price = RoundFloat(avg_price, places=2)
        best_price = RoundFloat(best_price, places=2)
        if int(best_price) == int(avg_price):
            msg = "Great Deal! The best price on {} is currently ${}.  Go ahead and buy!".format(product_title,
                                                                                                 best_price)
        elif int(best_price) > int(avg_price):
            msg = "Wait to buy. {} is usually ${}.  Ask us again tomorrow!".format(product_title, avg_price)
        elif int(best_price) <= int(min_price):
            msg = "Buy now! The best price on {} is currently ${}, and this is the lowest price of the last 30 days!".format(
                product_title, best_price)
        elif int(best_price) < int(avg_price) and int(best_price) > int(min_price):
            msg = "Good deal. The best price on {} is currently ${}. In the last 30 days, it's had a low price of ${} but an average price of ${}.".format(
                product_title, best_price, min_price, avg_price)
        else:
            print
        "NO LOGIC"

    if not msg:
        msg = "No buying tips available at this time. Please check again later."
        user_request_obj.is_buying_tips_registered = True
        user_request_obj.save()
        if is_automated: push_tips = False

    headers = {
        'Content-Type': 'application/json',
    }
    data = {
        "recipient": {
            "id": user_request_obj.request_from
        },
        "message": {
            "text": msg
        }
    }
    if user_request_obj.is_price_drop_alert_registered == False:
        data = {
            "recipient": {
                "id": user_request_obj.request_from
            },
            "message": {
                "attachment": {
                    "type": "template",
                    "payload": {
                        "template_type": "button",
                        "text": msg,
                        "buttons": [{
                            "type": "postback",
                            "title": "Set Price Drop Alert",
                            "payload": str(user_request_obj.pk)
                        }]
                    }
                }
            }
        }
    print
    "---", data
    data = json.dumps(data)
    if msg:
        if push_tips:
            r = requests.post('https://graph.facebook.com/v2.6/me/messages?access_token=%s' % (FACEBOOK_BOT_KEY),
                              headers=headers, data=data)
            if is_automated:
                user_request_obj.is_buying_tips_pushed = True
                user_request_obj.save()
            print
            "user_request_obj.is_buying_tips_pushed", user_request_obj.is_buying_tips_pushed
        if is_automated == False:
            push_best_used_product(user_request_obj)
    print
    "PUSHED"
    return True


@csrf_exempt
def facebook_bot_webhook(request):
    from PriceIT.tasks import save_actual_product, save_product_min_max_price
    from PriceIT.views import check_purchase_url_has_dot_com_domain
    from django.core.validators import URLValidator
    from django.core.exceptions import ValidationError
    import requests
    sender = ''
    try:
        # logger.debug('Trial 11111')
        hub_challenge = request.GET.get('hub.challenge')
        verify_token = request.GET.get('hub.verify_token')
        print
        request.body
        # return HttpResponse(1)
        # logger.debug('Trial 2222')
        if verify_token == settings.FACEBOOK_BOT_KEY:
            # logger.debug('Trial 33333')
            return HttpResponse(hub_challenge)
        # logger.debug('Trial 44444')
        print
        request.body
        if request.method == "POST":
            # logger.debug('Trial 5555')
            logger.info('')
            logger.info('===================New Request========================')
            logger.info('Request recevied')
            if request.body:
                headers = {
                    'Content-Type': 'application/json',
                }
                request_msg = json.loads(request.body)
                # logger.debug('Request body',request_msg)
                print
                "going to ake dict", request_msg
                # sometime bot send bulk msg, so we need to iterate it 
                # and save in db. this needs to be done...for example
                # http://www.jsoneditoronline.org/?id=04210a57ee9f36b8ed803e5e120a6c93
                messaging = request_msg['entry'][0]['messaging'][0]
                print
                "messaging.keys()", messaging.keys()
                # logger.debug('Trial 77777')
                logger.info('Message = %s' % (messaging))
                if 'delivery' in messaging.keys():
                    print
                    "DELIVERY"
                    # logger.debug('Trial 88888')
                    logger.info("delivery status message")
                    return HttpResponse(True)
                sender = request_msg['entry'][0]['messaging'][0]['sender']['id']
                print
                sender
                # logger.debug('Trial 999999')
                logger.info("Sender id = %s" % (sender))
                timestamp = request_msg['entry'][0]['messaging'][0]['timestamp']
                timestamp_to_datetime = datetime.datetime.fromtimestamp(timestamp / 1e3)
                payload = ""
                flag = 0
                # logger.debug('Trial 10000000')
                data = '''{
                            "recipient":{
                                "id":"1056857894370668"
                            }, 
                            "message":{
                                "text":"What product would you like to buy?
                                 Please enter the purchase link."
                            }
                        }'''
                print
                "111"
                print
                "request_msg", request_msg
                message_dict = request_msg['entry'][0]['messaging'][0]
                if 'postback' in message_dict:
                    postback_title = message_dict['postback'].get('title', '')
                    if str(postback_title) == "Buying Tips":
                        user_req_id = message_dict['postback'].get('payload', '')
                        print
                        "user_req_id", user_req_id
                        push_buying_tips(user_req_id)
                        return HttpResponse(True)

                    if str(postback_title) == "Set Price Drop Alert":
                        user_req_id = message_dict['postback'].get('payload', '')
                        print
                        "user_req_id", user_req_id
                        register_price_drop_event(user_req_id)
                        return HttpResponse(True)

                    postback_title = str(postback_title.decode('unicode_escape'))
                    if str(postback_title) == "Get Started":
                        push_facebook_bot_intro_text(sender)
                    print
                    "postback_title --->>>", postback_title
                if 'postback' in message_dict:
                    payload = message_dict['postback']['payload']
                if payload == "BestPricePrompt":
                    # logger.debug('Trial 11   11   11   11')
                    flag = 1
                    data = {
                        "recipient": {
                            "id": sender
                        },
                        "message": {
                            "text": "What product would you like to buy? Please enter the purchase link."
                        }
                    }

                elif 'message' in message_dict:
                    # logger.debug('Trial 12   12   12  12')
                    flag = 1
                    if request_msg['entry'][0]['messaging'][0]['message']:
                        print
                        "going to validate"
                        # logger.debug('Trial 13    13    13')
                        validate = URLValidator()
                        message_list = request_msg['entry'][0]['messaging'][0]['message']
                        message_type = message_list.get('attachments', [{}])[0].get('type', '')
                        """if str(message_type) == 'image':
                            image_url = str(message_list['attachments'][0]['payload'].get('url',''))
                            image_recognition_and_response(image_url, sender)
                            return HttpResponse(True)"""
                        # if text key is not present,it is not a textmessage oru url
                        # So push message
                        if ('sticker_id' in message_list and
                                message_list['sticker_id'] in [369239263222822, 369239343222814, 369239383222810]):
                            logger.info("sticker message")
                            # to catch THUMBSUP STICKER
                            facebook_push_thumbsup_response(sender)
                            return HttpResponse(True)

                        if str(message_type) == 'image':
                            image_url = str(message_list['attachments'][0]['payload'].get('url', ''))
                            if '.gif' in image_url:
                                facebook_push_invalid_image(sender)
                                return HttpResponse(True)
                            image_recognition_and_response(image_url, sender)
                            return HttpResponse(True)

                        if 'text' not in message_list:
                            # facebook_push_data_dict(sender)
                            print
                            "text not in"
                            logger.info("not a valid text")
                            facebook_push_invalid_url(sender)
                            print
                            "not  a texttttttt"
                        try:
                            if 'text' in message_list:
                                logger.info("message is a valid text = %s" % (message_list))
                                flag = 0
                                url = request_msg['entry'][0]['messaging'][0]['message']['text']
                                try:
                                    url = get_url_from_string(url)
                                except:
                                    pass
                                if url.startswith('www.') and not url.startswith('http'):
                                    print
                                    "startswith www and no http"
                                    url = '%s%s' % ('http://', url)
                                    logger.info("Url not starting with www or http = %s" % (url))
                                # logger.debug('Trial 14   14   14  14')
                                validate(url)

                                url = urllib.unquote(urllib.unquote(url.strip()))
                                if "amazon.com" in url and 'tag' in url:
                                    # We shouldn't store affliation tag
                                    try:
                                        url = remove_tag_from_amazon(url)
                                    except Exception, e:
                                        print
                                        "remove_tag_from_amazon excepton", e
                                        pass

                                if "amazon.com" in url and '/slredirect/' in url and "url=" in url:
                                    # We shouldn't store affliation tag
                                    try:
                                        url = get_amazon_redirect_url(url)
                                    except Exception, e:
                                        print
                                        "remove_tag_from_amazon excepton", e
                                        pass
                                elif 'wrd.walmart.com' in url or "cat.hlserve.com" in url:
                                    try:
                                        url = get_walmart_redirect_url(url)
                                        url = urllib.unquote(url)
                                    except Exception as e:
                                        print
                                        'remove walmart redirect exception URL:', url, e
                                '''
                                try:
                                    req_headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
                                    'Accept': 'text/html,application/xhtml+xml,application/xml,application/json;q=0.9,*/*;q=0.8',
                                    'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
                                    'Accept-Language': 'en-US,en;q=0.8',
                                    'Connection': 'keep-alive'}

                                    # After testing set timeout to 1 or 2second
                                    try:
                                        url_req = requests.get(url, headers=req_headers, timeout=5)
                                    except Exception as e:
                                        # Check rqst alreday exists for the user
                                        request_object = Request.objects.filter(url=url,request_from=sender,
                                            created_on__startswith=datetime.datetime.now().date(),status = Request.FAILED)
                                        if not request_object.exists():
                                            # Create a new request
                                            request_object = Request(url=url, request_from=sender)
                                            request_object.source = Request.FACEBOOK_BOT
                                            request_object.user_type = Request.FACEBOOK_ID
                                            request_object.is_active = False
                                            request_object.status = Request.FAILED
                                            request_object.save()
                                        facebook_push_invalid_url(sender)
                                        return HttpResponse(True)
                                    print "hererer"
                                    if 'html' not in url_req.headers.get('content-type'):
                                         print "url_req.status_code", url_req.status_code
                                         logger.info("first try Url not valid = %s %s" %(url, str(url_req.status_code)))
                                         facebook_push_invalid_url(sender)
                                         return HttpResponse(True)
                                except Exception, e:
                                    logger.info("Url not valid = %s" %(e))
                                    print "status code Exception", e
                                    facebook_push_invalid_url(sender) '''
                                # return HttpResponse(True)

                                message_id = request_msg['entry'][0]['messaging'][0]['message']['mid']
                                print
                                message_id, "message_id"
                                value_dict = {'sender_id': sender, 'timestamp': timestamp_to_datetime,
                                              'message_id': message_id, 'purchase_url': url, 'status': 0}
                                matchos_priceit_resp = priceit_matchos(url)
                                if not matchos_priceit_resp:
                                    facebook_push_invalid_url(sender)
                                    return HttpResponse(True)
                                push_match_os_resp(matchos_priceit_resp[0], sender)
                                return HttpResponse(True)

                                '''
                                """
                                Case 1:
                                    Check the url is already priced and status is completed
                                    if request exists,send already priced result
                                """
                                lastHourDateTime = datetime.datetime.today() - datetime.timedelta(hours = 48)
                                #existing_req = Request.objects.filter(url=url, status = Request.COMPLETED)
                                existing_req, sku = check_exisiting_sku(url)
                                if existing_req:
                                    existing_user_req = UserRequest.objects.filter(request=existing_req,
                                        request_from=sender,
                                        source=Request.FACEBOOK_BOT,
                                        user_type=Request.FACEBOOK_ID).order_by('-id').first()
                                    if not existing_user_req:
                                        existing_user_req = UserRequest.objects.create(request=existing_req, request_from=sender,
                                          source=Request.FACEBOOK_BOT, user_type=Request.FACEBOOK_ID)
                                    save_product_min_max_price.delay(existing_req, user_request=existing_user_req)
                                    print "already priced by the same user after last 48 hours ans completed"
                                    push_best_price_data(existing_user_req, model_name='UserRequest')
                                    return HttpResponse(True)
                                """
                                Case 2:
                                   Check the url is under processing and priced by same user at the same day.
                                   If the object exists,no need to send any response.
                                """
                                processing_request_obj = Request.objects.filter(Q(is_active=True)|Q(status = Request.PROCESSING),
                                        url=url,
                                        request_from=sender,
                                        created_on__startswith=datetime.datetime.now().date())
                                if processing_request_obj.exists():
                                    logger.info("Url valid and going to save DB.id = %s" %(processing_request_obj[0]))
                                    print "not processeddd"
                                    # To avoid same multiple request from same user with same url
                                    # which is not processed.
                                    logger.info("Url already priced today and processing")
                                    print "Url already priced today and processing"
                                    return HttpResponse(True)
                                """
                                Case 3:
                                   Check the url priced aby any user is failed.
                                   If the url is priced again on the same day,push invalid url msg
                                """
                                failed_request_obj = Request.objects.filter(url=url,
                                     created_on__startswith=datetime.datetime.now().date(),status = Request.FAILED)

                                # if priceit is failed,push invalid url
                                if failed_request_obj.exists():
                                    print "url is failed so push invalid url"
                                    facebook_push_invalid_url(sender)
                                    return HttpResponse(True)

                                # Lets create a new object
                                request_object = Request(url=url, request_from=sender)
                                # Need to remove below two lines.
                                if sku:
                                    request_object.sku = sku
                                request_object.source = Request.FACEBOOK_BOT   
                                request_object.user_type = Request.FACEBOOK_ID
                                request_object.save()
                                user_request_obj = UserRequest(request=request_object, request_from=sender)
                                user_request_obj.source = Request.FACEBOOK_BOT
                                user_request_obj.user_type = Request.FACEBOOK_ID
                                user_request_obj.save()
                                # logger.debug('Trial 15   15   15   15')
                                logger.info("url saved ,object id >> %s" %(request_object.id))
                                logger.info("Replying to url")
                                data = {
                                "recipient":{
                                    "id":sender
                                }, 
                                "message":{
                                    "text":" Got it! I'm looking for the best deals, and I'll send you a message as soon as I've found something."
                                }
                                }
                                data = json.dumps(data)
                                r = requests.post('https://graph.facebook.com/v2.6/me/messages?access_token=%s' %(FACEBOOK_BOT_KEY), headers=headers, data=data)
                                is_dot_com_site = check_purchase_url_has_dot_com_domain(request_object)
                                print "is_dot_com_site", is_dot_com_site
                                if not is_dot_com_site:
                                    logger.info("going to push non_supported site reply")
                                    push_non_supported_site_message(user_request_obj)
                                    return HttpResponse(True)
                                logger.info("going to check product already processed")
                                already_processed_url = check_exisiting_purchase_url(request_object)
                                logger.info("already procssed url = %s" %(already_processed_url))

                                if not already_processed_url:
                                    logger.info("going to save product")
                                    # logger.debug('Trial 17   17   17   17')
                                    save_actual_product.delay(url,request_object)
                                else:
                                    logger.info("already proccsed url is True")
                                    logger.info("going to send true")
                                    return HttpResponse(True)
                                    logger.info("returned")'''
                                fb_bot_users, created = FbBotUsers.objects.get_or_create(facebook_id=sender)
                                if created:
                                    user_details = requests.get(
                                        'https://graph.facebook.com/v2.6/%s/?access_token=%s' % (
                                        sender, FACEBOOK_BOT_KEY))
                                    user_data = user_details.text
                                    user_data = json.loads(user_data)
                                    gender = ''
                                    # logger.debug('Trial 16   16   16   16')
                                    logger.info("Fetch user data = %s" % (user_data))
                                    if 'gender' in user_data:
                                        gender = user_data['gender']
                                    if gender == "female":
                                        user_gender = FbBotUsers.FEMALE
                                    else:
                                        user_gender = FbBotUsers.MALE
                                    fb_bot_users, created = FbBotUsers.objects.get_or_create(facebook_id=sender)
                                    fb_bot_users.gender = user_gender

                        except ValidationError, e:
                            logger.info("catched ValidationError = %s" % (e))
                            print
                            "ValidationError,", e
                            # logger.debug('Trial 18   18   18   18')

                            text = request_msg['entry'][0]['messaging'][0]['message']['text']
                            logger.info("message is not a url or sticker = %s" % (text))
                            text = text.lower()
                            intro_text_list = ['hello', 'hello!', 'hi', 'hi!', 'hey', 'hey!']
                            help_text_list = ['?', 'help?', 'help ?', 'help', 'what?',
                                              'what ?', 'what', 'how?', 'how', 'how ?']
                            if text in intro_text_list:
                                logger.info("Replying to introduction message = %s" % (text))
                                flag = 0
                                push_facebook_bot_intro_text(sender)
                            elif text in help_text_list:
                                logger.info("Replying to help text message = %s" % (text))
                                flag = 0
                                facebook_push_data_dict(sender)

                            elif text == "(y)":
                                logger.info("Replying to thumbsup message = %s" % (text))
                                facebook_push_thumbsup_response(sender)

                            elif text == "stop":
                                logger.info("Replying to stop message = %s" % (text))
                                sender_requests = Request.objects.filter(request_from=sender)
                                for req in sender_requests:
                                    req.is_active = False
                                    req.save()

                                flag = 0
                                data = {
                                    "recipient": {
                                        "id": sender
                                    },
                                    "message": {
                                        "text": "I've stopped searching for the best price for this product. If you'd like me to find the best price on another product, just copy the link to the product and paste it into the message box below.",
                                    }
                                }
                                data = json.dumps(data)
                                r = requests.post(
                                    'https://graph.facebook.com/v2.6/me/messages?access_token=%s' % (FACEBOOK_BOT_KEY),
                                    headers=headers, data=data)
                                print
                                r.text
                            else:
                                flag = 0

                                """data = {
                                "recipient":{
                                    "id":sender
                                }, 
                                "message":{
                                "attachment":{
                                  "type":"template",
                                  "payload":{
                                    "template_type":"button",
                                    "text":"Hi! I'm the Price Bot. Send me a link to a product you've found, and I'll search the web for the best price.\nYou can also message us the name of a product or store, and we will find all the best deals for you to browse (note: this feature is in beta).",
                                  }
                                }
                              }
                            }"""
                                # msg = "Announcing the Beta Launch of Chatbot Search! Now you can message us the name of a product or store, and we will find all the best deals for you to browse. Try it out today!"
                                store_name = text.lower().replace(" ", '')
                                deal_lookup_text = text.lower().replace(" ", '')
                                if deal_lookup_text == "topdeals":
                                    deal_lookup_text = "blackfriday"
                                deals_type = DealsFeedType.objects.filter(active=True,
                                                                          feed_type=deal_lookup_text).first()
                                if deals_type:
                                    msg = 'We found you the latest deals for ' + text.title()
                                    button_text = 'See Deals'
                                    button_url = 'https://price.com/deals/' + deals_type.feed_type
                                else:
                                    record = get_object(store_name, 'objectID', 'stores')
                                    store_domain = ''
                                    if record:
                                        store_domain = record.get('store_domain', '')
                                        # store_domain = store_domain.replace('https://', '').replace('http://', '')
                                        storeName = get_top_level_domain_from_url(store_domain)
                                        has_coupon = Coupon.objects.filter(valid=True, store__name=storeName).exists()
                                        if has_coupon:
                                            store_domain = store_domain.replace('https://', '').replace('http://', '')
                                            msg = 'We found you the latest coupons and offers from ' + text.title()
                                            button_text = 'See Deals'
                                            button_url = 'https://price.com/coupons/' + store_domain
                                        else:
                                            store_redirect = get_affiliate_url(store_domain)
                                            msg = 'There are no coupons currently available at {}, but be sure to shop their site for the latest products.'.format(
                                                storeName.title())
                                            button_text = 'Visit ' + storeName.title()
                                            button_url = store_redirect
                                    if not store_domain:
                                        msg = 'This feature is still in beta -- Click here to access all the shopping options for ' + text
                                        msg += '\nFor optimal results, please reply with a copy and paste of the product page URL.'
                                        button_text = "Shop %s" % (Truncator(text).chars(8))
                                        button_url = "https://price.com/search?%s" % (urllib.urlencode({'query': text}))
                                data = {
                                    "recipient": {
                                        "id": sender
                                    },
                                    "message": {
                                        "attachment": {
                                            "type": "template",
                                            "payload": {
                                                "template_type": "button",
                                                "text": msg,
                                                "buttons": [
                                                    {
                                                        "type": "web_url",
                                                        "url": button_url,
                                                        "title": button_text
                                                    },
                                                ]
                                            }
                                        }}
                                }

                                data = json.dumps(data)
                                logger.info("Invalid message.Pushing invalid response")
                                r = requests.post(
                                    'https://graph.facebook.com/v2.6/me/messages?access_token=%s' % (FACEBOOK_BOT_KEY),
                                    headers=headers, data=data)
                                print
                                r.text
                else:
                    print
                    "this is for else"
                    flag = 0
                if flag == 1:
                    # logger.debug('Trial 19   19   19   19')
                    data = json.dumps(data)
                    print
                    data, "datadata"
                    r = requests.post(
                        'https://graph.facebook.com/v2.6/me/messages?access_token=%s' % (FACEBOOK_BOT_KEY),
                        headers=headers, data=data)
                    print
                    r
                    print
                    r.status_code
                    print
                    r.text
                    logger.debug(r.text)
    except Exception, e:
        logger.info("GENERAL EXCEPTION = %s" % (e))
        if sender:
            facebook_push_invalid_url(sender)
        print
        "GENERAL EXCEPTION,", e

    # logger.debug('Trial 20   20   20  20')
    logger.info("True")
    return HttpResponse(True)


def facebook_push_data_dict(sender):
    # Push  message to facebook
    print
    "going to push help texttttt"
    headers = {
        'Content-Type': 'application/json',
    }
    data = {
        "recipient": {
            "id": sender
        },
        "message": {
            "text": "I can help you find the best price for any product. Just copy the link to the product and paste it into the message box below."
        }
    }
    data = json.dumps(data)
    r = requests.post('https://graph.facebook.com/v2.6/me/messages?access_token=%s' % (FACEBOOK_BOT_KEY),
                      headers=headers, data=data)
    return HttpResponse(True)


def facebook_push_invalid_url(sender):
    headers = {
        'Content-Type': 'application/json',
    }
    data = {
        "recipient": {
            "id": sender
        },
        "message": {
            "text": ":-( I can't get the link you sent to work. Please send another?"
        }
    }
    data = json.dumps(data)
    r = requests.post('https://graph.facebook.com/v2.6/me/messages?access_token=%s' % (FACEBOOK_BOT_KEY),
                      headers=headers, data=data)
    return HttpResponse(True)


def facebook_push_invalid_image(sender):
    headers = {
        'Content-Type': 'application/json',
    }
    data = {
        "recipient": {
            "id": sender
        },
        "message": {
            "text": ":-( I can't get the gif you sent to work. Please send another image?"
        }
    }
    data = json.dumps(data)
    r = requests.post('https://graph.facebook.com/v2.6/me/messages?access_token=%s' % (FACEBOOK_BOT_KEY),
                      headers=headers, data=data)
    return HttpResponse(True)


def facebook_push_thumbsup_response(sender):
    """
    If user send Thumbsup sticker, we respond with :-)
    """
    headers = {
        'Content-Type': 'application/json',
    }
    data = {
        "recipient": {
            "id": sender
        },
        "message": {
            "text": ":-) (y)"
        }
    }
    data = json.dumps(data)
    r = requests.post('https://graph.facebook.com/v2.6/me/messages?access_token=%s' % (FACEBOOK_BOT_KEY),
                      headers=headers, data=data)
    return HttpResponse(True)


def push_facebook_bot_intro_text(sender):
    """
    If user send any "hello,"help,"hi "
    """

    print
    "going to send intro message"
    headers = {
        'Content-Type': 'application/json',
    }
    data = {
        "recipient": {
            "id": sender
        },
        "message": {
            "text": """Hi, I'm the Price.com Bot. I can help you maximize savings while you shop. Provide one of the things below to get things started.
                1. Paste a product URL from any store
                2. Upload a photo
                3. Message a product name or description"""
        }
    }
    data = json.dumps(data)
    r = requests.post('https://graph.facebook.com/v2.6/me/messages?access_token=%s' % (FACEBOOK_BOT_KEY),
                      headers=headers, data=data)
    return HttpResponse(True)


def push_invalid_url_message_and_delete_request(request_obj):
    '''
    Delete the request and push the invalid url message
    If the actual product is null
    '''
    headers = {
        'Content-Type': 'application/json',
    }
    data = {
        "recipient": {
            "id": request_obj.request_from
        },
        "message": {
            "text": ":-( I can't get the link you sent to work. Please send another?"
        }
    }
    data = json.dumps(data)
    r = requests.post('https://graph.facebook.com/v2.6/me/messages?access_token=%s' % (FACEBOOK_BOT_KEY),
                      headers=headers, data=data)
    request_obj.delete()
    return HttpResponse(True)


def push_non_supported_site_message(user_request_obj):
    '''
    Message for non-supported sites
    '''
    headers = {
        'Content-Type': 'application/json',
    }
    data = {
        "recipient": {
            "id": user_request_obj.request_from
        },
        "message": {
            "text": ":-( I am sorry,  right now we can only price items from US stores. Please send another?"
        }
    }
    data = json.dumps(data)
    r = requests.post('https://graph.facebook.com/v2.6/me/messages?access_token=%s' % (FACEBOOK_BOT_KEY),
                      headers=headers, data=data)
    return HttpResponse(True)
