from PriceIT.models import LinkMonetizer
import urlparse
from urllib import urlencode

def generate_avantlinks_deep_link(link_monetizer, purchase_url, user_id):
    """
    Format : http://www.avantlink.com/click.php?tt=cl&mi=10060&pw=216969&url=<purchase_url>

    ctc=YOURSID
    <purchase_url> --> purchase_url
    """

    if not all([link_monetizer.base_url]):
        return None
    # Append params and generate new link
    params = {
        "url": purchase_url,
        "ctc": user_id #
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
