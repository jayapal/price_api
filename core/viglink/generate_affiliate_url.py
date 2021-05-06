import urllib
import requests

def get_viglink_url(out):
    """
    function returns the viglink monitized url for the purchase url
    params :
            INPUT: out: purchase_url
            OUTPUT: monitized url if process is success
                    empty string if process fails
    """

    # viglink_api_key = '88ac2a40e081e283ac504d1789d398ac'#'528bc104b8865603b253575ff300af8b'
    viglink_api_key = '8be13336bd655e111d6aca6b800075e8'  # viglink key
    ip_format = 'txt'  # required format by viglink
    loc = 'http://price.com'
    ref = 'http://price.com'
    url = "http://api.viglink.com/api/click"  # api endpoint
    reaf = True
    params = {
        'format': ip_format,
        'key': viglink_api_key,
        'out': out,
        'loc': loc,
        'ref': ref,
        'reaf': reaf
    }

    res = requests.get(url, params=params)
    try:  # excepted when request fails
        if res.content.startswith('http'):
            return res.content
    except Exception:
        pass
    return ''

# out = 'https://www.amazon.com/AmazonBasics-Stainless-Steel-Dog-Bowl/dp/B01DOP5S9K/'
# print(get_viglink_url(out))
