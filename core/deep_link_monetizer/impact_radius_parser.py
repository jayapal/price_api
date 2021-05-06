from PriceIT.models import LinkMonetizer
import urlparse
from urllib import urlencode
from django.conf import settings

def generate_impact_radius_deep_link(link_monetizer, purchase_url, user_id):
    """
    Format: <retail base url>?u=<product page url>

    Example (diapers.com)
    Base URL: http://diapers.7eer.net/c/11061/83376/2052
    Product URL: https://www.diapers.com/p/manhattan-toy-winkel-6679?sku=MA-006&qid=2573941871&sr=1-1
    Output : http://diapers.7eer.net/c/11061/83376/2052?u=https://www.diapers.com/p/manhattan-toy-winkel-6679?sku=MA-006&qid=2573941871&sr=1-1

    """

    if not link_monetizer.base_url:
        return None
    # Append params and generate new link
    params = {
        "u": purchase_url,
        "subId1": user_id
    }
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
