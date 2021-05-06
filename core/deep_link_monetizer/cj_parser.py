from PriceIT.models import LinkMonetizer
import urlparse
from urllib import urlencode
from django.conf import settings
PRICE_CJ_AFFILIATE_ID = settings.PRICE_CJ_AFFILIATE_ID

def generate_cj_deep_link(link_monetizer, purchase_url, user_id):
    """
    Format : http://<cj-root-domain>/click-<your-pid>-<advertiser-link-id>?url=<url-encoded-redirect-link>&sid=<user_id>
    Ex: http://www.jdoqocy.com/click-1245-10888587?url=http%3A%2F%2Fwww.jewelry.com%2Fdaily-deal.shtml&sid=<user_id>

    <advertiser-link-id> --> merchant_id
    <your-pid> --> PRICE_CJ_AFFILIATE_ID
    """
    if not link_monetizer.merchant_id:
        return None
    if link_monetizer.base_url:
        base_url = link_monetizer.base_url
    else:
        base_url = "http://www.jdoqocy.com"
    # format base_url
    base_url = "%s/click-%s-%s" %(base_url, PRICE_CJ_AFFILIATE_ID, link_monetizer.merchant_id)
    print base_url
    # Append params and generate new link
    params = {'url': purchase_url, "sid": user_id}
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
