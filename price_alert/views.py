from django.http import JsonResponse
from django.forms import ModelForm
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
