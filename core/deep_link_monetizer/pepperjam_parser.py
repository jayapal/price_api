from PriceIT.models import LinkMonetizer
from core.utils import get_encoded_url
import urlparse
from urllib import urlencode

def generate_pj_deep_link(link_monetizer, purchase_url, user_id):
    print "purchase", purchase_url
    params = {'url': purchase_url, "sid": user_id}
    if not link_monetizer.base_url:
        return None
    url_parts = list(urlparse.urlparse(link_monetizer.base_url))
    # Make the querystrings into the dict
    query = dict(urlparse.parse_qsl(url_parts[4]))
	# updating the querystring with the parameters
    query.update(params)
    url_parts[4] = urlencode(query)
    #Appending the updated querystring into the url
    deep_link = urlparse.urlunparse(url_parts)
    print "deep_link", deep_link
    return deep_link
