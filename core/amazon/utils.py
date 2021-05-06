import re


def get_asin_from_url(url):
    """
       Code for extracting ASIN from amazon urls.
    """
    asin_regex = r'/([A-Z0-9]{10})'
    # asin_regex = r'\W([A-Z0-9]{10})\W?'
    asin = re.search(asin_regex, url)
    if asin:
        asin = asin.group()
        asin = asin.replace('/', '')
        asin = asin.replace('?', '')
        if len(asin) > 10:
            return asin[:10]
        return asin
    return False


class RoundFloat(float):
    """
    Float sub class to display two decimal places and
    rounding to nearest float
    """
    def __new__(cls, value=0, places=2):
        return float.__new__(cls, value)
    def __init__(self, value=0, places=2):
        self.places = str(places)
    def __repr__(self):
        return ("%." + self.places + "f") % self
    __str__ = __repr__

