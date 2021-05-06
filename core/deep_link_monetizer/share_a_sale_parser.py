from PriceIT.models import LinkMonetizer
import urlparse
from urllib import urlencode
from django.conf import settings

def generate_share_a_sale_deep_link(link_monetizer, purchase_url, user_id):
    """
    Format: <retail base url>?urllink=<product page url>

    Example (wayfair)
    Base URL: http://www.shareasale.com/r.cfm?u=1272520&b=65867&m=11035&afftrack=&urllink=
    Product URL: https://www.wayfair.com/Rachael-Ray-Bubble-and-Brown-Bakeware-10-Oz.-Ramekin-RRY3067.html
    Output: http://www.shareasale.com/r.cfm?u=1272520&b=65867&m=11035&afftrack=&urllink=https://www.wayfair.com/Rachael-Ray-Bubble-and-Brown-Bakeware-10-Oz.-Ramekin-RRY3067.html

    """

    if not link_monetizer.base_url:
        return None
    # Append params and generate new link
    params = {
        "urllink": purchase_url,
        "afftrack": user_id
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
