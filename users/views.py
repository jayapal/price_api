import json

from django.conf import settings
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.views.decorators.cache import cache_page
from django.shortcuts import (HttpResponse, HttpResponseRedirect,
                              render, render_to_response)

from Klutterapp.models import Category, UserProfile
from BrandFavourite.models import BrandNavigation, Brand, ProductsV2
from notifications.models import UserNotification, NotificationType
from Subscriptions.models import SubscribedUsers

from rest_framework.decorators import api_view
from rest_framework.authtoken.models import Token
from django.utils.crypto import get_random_string


@api_view()
def user_details(request, user_id):
    """

        METHOD: GET

        URL: http://%(site)s/get/user/details/{{user_id}}

        Example :
           http://%(site)s/get/user/details/5/

        @output: JSON Response

        @JSON Response:
         [
            {
            priced_it_count: 0,
            name: "Peter Boboff",
            price_points: 0,
            total_saved: 0,
            favourites: 0,
            email: "pboboff@hotmail.com"
            }
        ]
    """
    print request.META
    print request.META.get('HTTP_AUTHORIZATION')
    from PriceIT.models import Request, UserRequest
    from django.db.models import Sum
    from BrandFavourite.models import FavouriteV2
    user_dict = {}
    user = get_object_or_404(UserProfile, user__id=user_id)


    #user_favourites = FavouriteV2.objects.filter(user=user.user, is_active=True).count()

    user_dict['favourites'] = 0
    user_dict['ebtoken'] = user.ebtoken if user.ebtoken else get_random_string(length=32)
    user_dict['ebates_id'] = user.ebates_id
    user_dict['admin'] = user.user.is_superuser
    """if not user_dict['admin']:
        if user.user.groups.filter(name='TESTER').exists():
            user_dict['admin'] = True"""
    if user.user.first_name or user.user.last_name:
        user_dict['name'] = '%s %s'%(user.user.first_name,user.user.last_name)
    if user.gender:
        user_dict['gender'] = user.gender
    user_dict['email'] = user.user.email
    if user.location:
        user_dict['location'] = user.location
    if user.likes:
        user_dict['likes'] = user.likes
    if user.profile_pic:
        user_dict['profile_pic'] = user.profile_pic.url
    user_dict['price_points'] = 0
    if user.price_points:
        user_dict['price_points'] = user.price_points
    user_dict['total_saved'] = 0
    user_dict['priced_it_count'] = 0
    user_dict['price_points']  = 0
    user_dict['you_earned_notification'] = False
    """total_saved = Request.objects.filter(request_from=user_id,
                    is_deleted=False).aggregate(Sum('total_saved'))

    total_saved_userrequest = UserRequest.objects.filter(request_from=user_id,
                    is_deleted=False).aggregate(Sum('request__total_saved'))

    if not total_saved['total_saved__sum']:
        # sometimes we get None
        total_saved['total_saved__sum'] = 0
    u_re_total = total_saved_userrequest.get('request__total_saved__sum', 0.0)
    if u_re_total:
        total_saved['total_saved__sum'] = u_re_total
    user_dict['total_saved'] = total_saved['total_saved__sum']
    from PriceIT.models import Request

    # please add UserProfile field priced_it_count, i am not sure of proper way
    user_dict['priced_it_count'] = UserRequest.objects.filter(
        Q(user_type = Request.EMAIL)|Q(user_type = Request.USER_ID),(
        Q(request_from=user_id)|Q(request_from=user.user.email)),
        is_deleted=False).exclude(request__product__isnull=True).values_list(
        'request__product__purchase_url',flat=True).distinct().count()

    user_dict['price_points'] = user.price_points
    user_content = []
    user_dict['you_earned_notification'] = user.you_earned_notification

    base_notifications = UserNotification.objects.filter(user=user.user, is_hidden=False)
    products_list = base_notifications.values_list('product__pk', flat=True).distinct()
    not_id = [UserNotification.objects.filter(product__id=x)[0].pk for x in products_list]
    notifications = base_notifications.filter(
        Q(id__in=not_id) | Q(product__isnull=True)).order_by('-pk')

    #notification_count = 0
    notification_count = notifications.count()
    '''for notification in notifications:
        data_dict = {}
        if notification.notification_type.notification_type == NotificationType.DROP:
            data_dict['reduction'] = notification.get_reduction_percentage()
        if 'reduction' in data_dict:
            reduction = float(data_dict['reduction'])
            # To remove reduction  when it is a negative value,if the price increases than original price
            if reduction <= 0:
                continue
        notification_count += 1'''

    user_dict['unread_notifications'] = notification_count
    if int(user_id) == 16257:
        # Harcode for hello@price.com
        user_dict['price_points'] = 25923 
        user_dict['total_saved'] = 3105
        user_dict['priced_it_count'] = 408  
        user_dict['admin'] = False
    user_dict['subscribed'] = SubscribedUsers.objects.filter(user=user.user).exists()"""
    token,created= Token.objects.get_or_create(user=user.user)
    user_dict['unread_notifications'] = 0
    user_dict['subscribed'] = False
    user_dict['token'] = token.key
    user_content = []
    user_content.append(user_dict)
    return HttpResponse(json.dumps(user_content),
                    content_type="application/json")
