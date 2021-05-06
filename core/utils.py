import tldextract
from tld import get_tld
import re
import urllib
import urlparse

from core.amazon.utils import get_asin_from_url


def get_top_level_domain_from_url(url):
    """
    @param url : puchase_url
    @output    : top level domain
    @error     : None
    """
    tdl = tldextract.extract(url)
    return tdl.domain.lower()


def get_top_level_domain_from_url_v2(product_url):
    """
    To get the top level store name
    @param url : product_url
    @output    : top level domain
    @error     : None
    """
    if not product_url.startswith("http"):
        product_url = "http://%s" %(product_url)
    tdl = get_tld(product_url, as_object=True)
    print "STORE", tdl.domain
    return tdl.domain


def get_normalized_amazon_url(url):
    """method to get normalized amazon url"""

    asin = get_asin_from_url(url)
    if asin:
        url = 'https://www.amazon.com/dp/{}'.format(asin)
    return url


def get_registered_domain_from_url(url):
    """
    @param url : puchase_url
    @output    : top level domain
    @error     : None
    """
    tdl = tldextract.extract(url)
    return tdl.registered_domain.lower()


def remove_tag_from_amazon(purchase_url):
    u = urlparse.urlparse(purchase_url)
    query = urlparse.parse_qs(u.query)
    query.pop('tag', None)
    u = u._replace(query=urllib.urlencode(query, True))
    url = urlparse.urlunparse(u)
    normalized_url = get_normalized_amazon_url(url)
    return normalized_url


def get_amazon_redirect_url(purchase_url):
    """
    convert https://www.amazon.com/gp/slredirect/picassoRedirect.html/ref=sspa_dk_detail_1?ie=UTF8&adId=A0011491MPXY3AZP5C2D&qualifier=1510227878&id=3576553017276595&widgetName=sp_detail&url=%2Fdp%2FB01J73A7JE%2Fref%3Dsspa_dk_detail_1%3Fpsc%3D1
    to https://www.amazon.com/dp/2FB01J73A7JE
    """
    purchase_url = urllib.unquote(purchase_url)
    parsed_uri = urlparse.urlparse(purchase_url)
    if 'url' in urlparse.parse_qs(parsed_uri.query) and urlparse.parse_qs(parsed_uri.query)['url']:
        sub_url = urlparse.parse_qs(parsed_uri.query)['url'][0]
        if sub_url:
            if sub_url.startswith("http"):
                return sub_url
            amazon_actual_url = '{uri.scheme}://{uri.netloc}{sub_url}'.format(uri=parsed_uri, sub_url=sub_url)
            return amazon_actual_url
    return purchase_url

import subprocess
def get_redirected_url_using_curl(url):
    """
    Get the redirected URL

    @params URL : URL which has the affilate URL with redirection
    ex: http://www.upcitemdb.com/norob/alink/?id=v2o263t2w203f484s2&tid=1&seq=1478848676&plt=90a9ebaef943854a09b5d03774c1a64a

    @output actual purchase url
    ex: https://www.neweggbusiness.com/Product/Product.aspx?Item=9SIV0JC3EJ6966&nm_mc=afc-cjb2b&cm_mmc=afc-cjb2b-_-Mac+-+iPad-_-Apple-_-9SIV0JC3EJ6966&utm_medium=affiliates&utm_source=afc-cjb2b-Priceviewer
    """
    try:
        command = 'curl -Ls -m 3 -o /dev/null -w %{url_effective} "' + url + '"'  # timeout set to 3 sec param -m
        p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        if out.startswith("http"): return out
    except Exception, e:
        print url
        print "EXCEPTION IN get_redirected_url", e
    return url


def get_walmart_redirect_url(url, meth=False):
    """
    Method returns walmart url from the redirect walmart ur
    There is 2 types of redirections
    1. single layer: https://wrd.walmart.com/track?rd=https%3A%2F%2Fwww.walmart.com%2Fip%2FProctor-Silex-2-Slice-Toaster-Model-22612
                    %2F41884128%3FfindingMethod%3Dwpa%26tgtp%3D2
    2. 2 layer: https://wrd.walmart.com/track?rd=https%3A%2F%2Fcat.hlserve.com%2Fb%2Fgk1zyOlbBka6FrGaHMSJ5Q%3Fdest%3Dhttps%253A%252F%252Fwww
                .walmart.com%252Fip%252FNutriBullet-Max-Silver%252F54055999%253F
    :param url: walmart purchase url to process
    :param meth: default :False
                          set True if get_redirected_url_using_curl to be called
    :return:walmart url
    """

    if url.startswith('https://www.walmart.') or url.startswith('http://www.walmart.'):
        return url
    if meth:
        base_walmart = get_redirected_url_using_curl(url)
        return base_walmart

    purchase_url = urllib.unquote(url)
    parsed_uri = urlparse.urlparse(purchase_url)

    # https://wrd.walmart.com/track?rd=https%3A%2F%2Fwww.walm redirect stuct
    if 'rd' in parsed_uri.query:
        try:
            base_walmart = urlparse.parse_qs(parsed_uri.query)['rd'][0]
        except:
            return url
        # ex url:  https://wrd.walmart.com/track?rd=https%3A%2F%2Fwww.walmart.com%2Fip%...
        # if we get walmart url [1 layer redirection]
        if base_walmart.startswith('https://www.walmart.') or base_walmart.startswith('http://www.walmart.'):
            return base_walmart

        # ex url: https://wrd.walmart.com/track?rd=https%3A%2F%2Fcat.hlserve.com%2Fb%2Fgk1zyOlbBka6FrGaHMSJ5Q%3Fdest%3Dhttps%253A%252F%252Fwww.walmart.com
        # [2 layer redirection]

        parsed_uri = urlparse.urlparse(base_walmart)
        base_walmart = urlparse.parse_qs(parsed_uri.query).get('dest', [url])[0]
        if base_walmart.startswith('https://www.walmart.') or base_walmart.startswith('http://www.walmart.'):
            return base_walmart
    return


def get_url_from_string(text):
    url = None
    try:
        url = re.search("(?P<url>https?://[^\s]+)", text).group("url")
        return url
    except:
        pass
    try:
        url = re.search("(?P<url>www.[^\s]+)", text).group("url")
        return url
    except:
        pass
    return text


def get_ip_from_request(request):
    """
    Extracts ip address from incoming request.

    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')

    if x_forwarded_for:
        ipaddress = x_forwarded_for.split(',')[-1].strip()
    else:
        ipaddress = request.META.get('REMOTE_ADDR')

    return ipaddress
