import json
import urllib2
import uuid
import xlrd
import urlparse
import re
import requests
import glob
import csv
import os
from StringIO import StringIO
from xlrd import open_workbook

from rest_framework.authtoken.models import Token
from django.views.decorators.cache import cache_page
from django.core.mail import EmailMessage, send_mail
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template import loader
from django.contrib.auth.models import User
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Q
from django.views.generic.edit import UpdateView, FormView
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import logout
from django.shortcuts import HttpResponse, HttpResponseRedirect, render, render_to_response
from django.http import HttpResponsePermanentRedirect
from django.utils.encoding import smart_str, smart_unicode
from django.contrib.auth import authenticate, login
from django.views.generic import ListView
from django.views.generic.edit import View
from django.db.models import Count
from django.conf import settings
from django.http import JsonResponse
from django.contrib.contenttypes.models import ContentType
from django.template import RequestContext
from django.core.files.base import File
from django.views.generic.edit import CreateView
from django.core.urlresolvers import reverse_lazy , reverse
from django.core.validators import URLValidator
from django.views.generic.list import InvalidPage, Http404, _
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render
from .models import *
from .forms import ItemDashboardModelForm, FavouriteCreateForm,\
                ProductPhotoUploadForm,UploadFileForm, BotRequestForm,\
                BotRequestUpdateForm,EmailRegistrationForm,\
                SetPasswordForm, PasswordResetRequestForm,\
                DeviceTokenCreateForm,WatchProductsCreateForm,\
                SimilarItemsForm
from .tasks import excel_upload_for_api, excel_upload_for_apiv2,\
                   excel_upload_for_apiv2_csv

from image_deduplicator import get_image_hash_from_url

from Klutterapp.models import UserProfile
from Klutterapp.utils import AjaxableResponseMixin
from Klutterapp.views.webapp import download_image_save
from Klutterapp.views.webapp import get_uuid, ajax_auth, user_details
from Klutterapp.utils import add_login_user_activity

from BrandDashboard.models import UserAnalytics

from amazonproduct import API
from bs4 import BeautifulSoup
from xlsxwriter.workbook import Workbook
from pyunpack import Archive as extract

from PriceIT.models import *

from PriceIT.utils import get_source_from_request
from core.utils import get_ip_from_request

CACHES_TIME_SECONDS = settings.CACHES_TIME_SECONDS

@csrf_exempt
def login_user(request):
    try:
        print request.POST, "]]]]]]]]]]]]]]"
        if request.method == 'POST':
            email = request.POST.get('email')
            password = request.POST.get('password')
            # source = request.POST.get('source','').strip()

            # Getting activty source.
            # Extension as default source.
            activity_source = get_source_from_request(request, default='ANDROID')

            try:
                username = User.objects.get(email=email).username
            except:
                username = ''
                return HttpResponse(json.dumps({'Error': 'Invalid request',
                     'status': 'fail' }), content_type="application/json")
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
                            login(request,user)
                    """total_requests = Request.objects.filter(request_from=user_id,
                      url__isnull=False,is_deleted=False).values('url').distinct().count()"""
                    total_requests = 0
                    token,created= Token.objects.get_or_create(user=user)
                    data = {'ids': user_id, 'token': token.key,'requests':total_requests}
                    ip_address = get_ip_from_request(request)
                    """try:
                        add_login_user_activity(user, activity_source, ip_address)
                    except Exception, e:
                        print "exception in login user", e"""
                    return HttpResponse(json.dumps(data),
                        content_type="application/json")
        return HttpResponse(json.dumps({'Error': 'Invalid request',
                'status': 'fail' }), content_type="application/json")
    except Exception as e:
        print e
        return HttpResponse(str(e))

