import requests

from core.shopyourlikes import config
from core.utils import get_registered_domain_from_url

from django.apps import apps

def get_affiliate_url(purchase_url):
    """
    Method to return affiliate url for Shopyourlikes Stores
    :param purchase_url:
    :return: affiliate url
    """
    generate_link_url = 'http://api.shopyourlikes.com/api/link/generate?url={}&publisherId={}&apiKey={}'.format(
                                        purchase_url, config.publisherId, config.apiKey)
    domain = get_registered_domain_from_url(purchase_url)
    ShopyourlikesMerchant = apps.get_model('PriceIT', 'ShopyourlikesMerchant')
    shop_merchant = ShopyourlikesMerchant.objects.filter(
        registered_domain=domain)
    if shop_merchant:
        try:
            affiliate_link = requests.get(generate_link_url).json()['link']
            return affiliate_link
        except Exception, e:
            print Exception
            pass
    return ''

