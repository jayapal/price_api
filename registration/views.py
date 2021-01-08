import json, logging

from django.db.models import Q
from django.shortcuts import HttpResponse
from django.contrib.auth.models import Group, User
from django.views.decorators.csrf import csrf_exempt
from rest_framework.authtoken.models import Token

from users.models import UserProfile, UserSignUp
from price_it.models import Request


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
    print(source)
    print(email)
    print(type(email))
    try:
        validate_email(email)
    except ValidationError as e:
        print("e", e)
        return HttpResponse(json.dumps(["Email not valid"]))
    if email and password:
        try:
            user = User.objects.get(Q(username=email)|Q(email=email))
            if not user.password:
                user.set_password(password)
                user.save()
        except User.DoesNotExist:
            user, created = User.objects.get_or_create(
                username=email[:30],
                email=email
            )
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

            user_id = user.id

            token, created = Token.objects.get_or_create(user=user)

            token = token.key
            if created or source not in user.groups.values_list('name',flat=True):
                group, created = Group.objects.get_or_create(name=source)
                try:
                    group.user_set.add(user)
                except:
                    pass
                user.set_password(password)

                if any(test_email in user.email.lower() for test_email in [
                    'price.com', 'tfbnw.net', 'westagilelabs.com', 'labglo.com',
                    '.labglo']):
                    group, created= Group.objects.get_or_create(name="TESTER")
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
                        'requests': total_requests, 'result': True}

                return HttpResponse(json.dumps(data),
                    content_type="application/json")

            data = {'present': True, 'token':token, 'result': False}
            return HttpResponse(json.dumps(data),
                    content_type="application/json")
    data = {'error': 'Invalid Entry.','result': False}
    return HttpResponse(json.dumps(data),
                content_type="application/json")
