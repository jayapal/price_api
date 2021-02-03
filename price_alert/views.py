import datetime, requests, urllib
from django.conf import settings
from django.core.mail import EmailMessage
from django.http import JsonResponse
from django.forms import ModelForm
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt

from price_alert.models import Alert


class AlertForm(ModelForm):
    class Meta:
        model = Alert
        fields = ["product_url", "vendor_name", "object_id", "sku", "price_alert", "user", "current_offer_price"]


@csrf_exempt
def alert_create(request):
    alert_form = AlertForm(request.POST)
    if not alert_form.is_valid():
        result = {'result': alert_form.errors}
        return JsonResponse(result, status=400)
    # form valid
    user_id = request.POST.get('user').strip()
    object_id = request.POST.get('object_id').strip()
    price_alert = request.POST.get('price_alert').strip()
    current_offer_price = request.POST.get('current_offer_price')
    try:
        instance = Alert.objects.get(user__id=user_id, object_id=object_id, active=False)
        instance.active = True
        instance.price_alert = price_alert
        if current_offer_price:
            instance.current_offer_price = current_offer_price
        instance.save()
        data = {'result': {
            'created': True,
        }}
        return JsonResponse(data)
    except Exception as e:
        print(e)
        # No inactive Records
        # But we may have another active records
    try:
        alert_form.save()
        data = {'result': {
            'created': True,
        }}
        return JsonResponse(data)
    except Exception as e:
        result = {'error': {'unique_together': "Duplicate entry"}}
        return JsonResponse(result, status=400)


def alert_list(request):
    try:
        user_id = int(request.GET.get('user_id'))
    except Exception as e:
        message = "Invalid User"
        return JsonResponse({'alerts': [], 'message': message}, status=200)

    qs = Alert.objects.filter(user__id=user_id)
    data = []
    for each in qs:
        row = {}
        row["object_id"] = each.object_id
        row["user_id"] = each.user.id
        row["product_url"] = each.product_url
        row["sku"] = each.sku
        row["vendor_name"] = each.vendor_name
        row["price_alert"] = each.price_alert
        row["active"] = each.active
        row["created_on"] = each.created_on
        row["updated_on"] = each.updated_on
        row["notified_timestamp"] = each.notified_timestamp
        row["notified_price"] = each.notified_price
        row["current_offer_price"] = each.current_offer_price
        data.append(row)
    return JsonResponse({'alerts': data}, status=200)


def get_email_content(instance):
    try:
        api_url = "https://matchos.price.com/apiv2/match_recommend?partner=5b960a4ade2962062eeb1f4a&url={}".format(
            urllib.parse.quote(instance.product_url)
        )
        data = requests.get(api_url).json()[0]
        print(api_url)
    except Exception as e:
        data = {}
    count_stats = {}
    for each in data.get("matches", []):
        if each["skuCondition"]+"_count" not in count_stats.keys():
            count_stats[each["skuCondition"]+"_count"] = 1
            count_stats[each["skuCondition"]+"_lowest_price"] = each["salePrice"]
        else:
            count_stats[each["skuCondition"]+"_count"] += 1
            if each["salePrice"] < count_stats[each["skuCondition"]+"_lowest_price"]:
                count_stats[each["skuCondition"]+"_lowest_price"] = each["salePrice"]
    result = {}
    result['Count'] = count_stats
    result["current_price"] = data.get("recommendation", {}).get("salePrice")

    result["product"] = data.get("recommendation")
    result["alert"] = instance
    try:
        result["you_save"] = instance.current_offer_price - instance.notified_price
    except:
        result["you_save"] = None

    print("result", result)
    # get title, image_url
    try:
        api_url = "https://matchos.price.com/apiv2/item?partner=5b960a4ade2962062eeb1f4a&url={}".format(
            urllib.parse.quote(instance.product_url)
        )
        data = requests.get(api_url).json()[0]
    except Exception as e:
        data = []
    if data:
        result["title"] = data.get("productName")
        result["image_url"] = data.get("imageUrl")
    alt_title = result["product"].get("productName")
    alt_image_url = result["product"].get("imageUrl")
    if not result.get("title"):
        result["title"] = alt_title
    if not result.get("image_url"):
        result["image_url"] = alt_image_url
    return result


def mark_as_inactive(request):
    status_code = 400
    updated = False
    message = None
    uuid = request.GET.get('uuid', '').strip()
    notified_price = request.GET.get('notified_price', '').strip()
    try:
        instance = Alert.objects.get(pk=uuid)
    except Exception as e:
        instance = None
        message = str(e)
    try:
        notified_price = float(notified_price)
    except Exception as e:
        message = "Invalid Price"
    if not notified_price:
        return JsonResponse({'updated': updated, 'message': "notified_price missing"}, status=400)
    if not message and instance:
        if instance.active:
            instance.active = False
            instance.notified_price = notified_price
            instance.notified_timestamp = datetime.datetime.now()
            result = get_email_content(instance)
            instance.save()
            message = "Marked as Inactive"
            updated = True
            status_code = 200
            subject = "Price Drop on {}".format(result["title"][:40])
            content = render_to_string("webapp/PriceAlert/email.html", {'result': result})
            from_email = settings.DEFAULT_FROM_EMAIL
            # html_content = htmly.render(data)
            to_email = [instance.user.email]
            #to_email = ["team@price.com", "test@price.com", "rj@price.com", "jayapal@price.com", "vasco@price.com"]
            msg = EmailMessage(subject, content, from_email, to_email)
            msg.content_subtype = "html"  # Main content is now text/html
            if instance.notified_price:
                msg.send()

            #return render(request, 'webapp/PriceAlert/email.html', {'result': result})

        else:
            message = "Already marked as Inactive"
    return JsonResponse({'updated': updated, 'message': message}, status=200)
