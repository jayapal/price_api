from PriceIT.models import LinkMonetizer
import urlparse
from urllib import urlencode
from django.conf import settings
PRICE_LINKSHARE_AFFILIATE_ID = settings.PRICE_LINKSHARE_AFFILIATE_ID

def generate_linkshare_deep_link(link_monetizer, purchase_url, user_id):
    """
    Format : http://click.linksynergy.com/deeplink?id=<affiliate id>&mid=<merchant id>&murl=<urlencoded target url>&u1=<user_id>


    <merchant id> --> merchant_id
    <affiliate id> --> PRICE_LINKSHARE_AFFILIATE_ID
    """

    if not all([link_monetizer.merchant_id]):
        return None
    base_url = "http://click.linksynergy.com/deeplink"
    # Append params and generate new link
    params = {
        "murl": purchase_url,
        "mid": link_monetizer.merchant_id,
        "id": PRICE_LINKSHARE_AFFILIATE_ID,
        "u1": user_id}
    url_parts = list(urlparse.urlparse(base_url))
    # Make the querystrings into the dict
    query = dict(urlparse.parse_qsl(url_parts[4]))
	# updating the querystring with the parameters
    query.update(params)
    url_parts[4] = urlencode(query)
    #Appending the updated querystring into the url
    deep_link = urlparse.urlunparse(url_parts)
    print "deep_link", deep_link
    return deep_link
