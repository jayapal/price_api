import json

from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.shortcuts import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.authtoken.models import Token

from core.utils import get_ip_from_request
from users.models import UserProfile


@csrf_exempt
def login_user(request):
    try:
        print(request.POST, "]]]]]]]]]]]]]]")
        if request.method == 'POST':
            email = request.POST.get('email')
            password = request.POST.get('password')
            # source = request.POST.get('source','').strip()

            # Getting activty source.
            # Extension as default source.

            try:
                username = User.objects.get(email=email).username
            except:
                username = ''
                return HttpResponse(
                    json.dumps({'Error': 'Invalid request', 'status': 'fail'}),
                    content_type="application/json"
                )
            user = authenticate(username=username, password=password)
            if user:
                if user.is_active:
                    user_obj, created = UserProfile.objects.get_or_create(user=user)
                    user_id = user.id
                    # merging RJ account. Since he got two acount.
                    # 47 is main account
                    if user.email == 'rljain@umich.edu':
                        user_id = 47
                    if 'source' in request.POST:
                        if request.POST.get("source") == "WEBSITE":
                            login(request, user)
                    """total_requests = Request.objects.filter(request_from=user_id,
                      url__isnull=False,is_deleted=False).values('url').distinct().count()"""
                    total_requests = 0
                    token, created = Token.objects.get_or_create(user=user)
                    data = {'ids': user_id, 'token': token.key, 'requests': total_requests}
                    ip_address = get_ip_from_request(request)
                    """try:
                        add_login_user_activity(user, activity_source, ip_address)
                    except Exception, e:
                        print "exception in login user", e"""
                    return HttpResponse(
                        json.dumps(data),
                        content_type="application/json"
                    )
        return HttpResponse(
            json.dumps({'Error': 'Invalid request', 'status': 'fail'}),
            content_type="application/json"
        )
    except Exception as e:
        print(e)
        return HttpResponse(str(e))
