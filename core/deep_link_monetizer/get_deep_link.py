from core.utils import get_top_level_domain_from_url_v2
from PriceIT.models import LinkMonetizer
from core.deep_link_monetizer.pepperjam_parser import generate_pj_deep_link
from core.deep_link_monetizer.cj_parser import generate_cj_deep_link
from core.deep_link_monetizer.linkshare_parser import generate_linkshare_deep_link
from core.deep_link_monetizer.impact_radius_parser import generate_impact_radius_deep_link
from core.deep_link_monetizer.share_a_sale_parser import generate_share_a_sale_deep_link
from core.deep_link_monetizer.avantlinks_parser import generate_avantlinks_deep_link
from core.shopyourlikes.get_deep_link import get_affiliate_url


def generate_deep_link(purchase_url, user_id, product_id=None, is_extension_request=False, build="production"):
    """
    To generate Deep Link Monetization
    @param purchase_url : Product URL
    @parms user_id : User ID
    @output        : Affiliate Link CJ/PJ/LinkShare
    """
    if not purchase_url:
        return None
    if not user_id:
        user_id = ''

    # Need to check if we have affiliation for Shopyourlikes network
    shop_your_likes = get_affiliate_url(purchase_url)
    if shop_your_likes:
        return shop_your_likes

    if product_id:
        user_id = "%s_%s" %(product_id, user_id)
        print "user_id", user_id
    # get store name
    retailer_name = get_top_level_domain_from_url_v2(purchase_url)
    if retailer_name:
        # get link monetizer data based on store.
        link_monetizer = LinkMonetizer.objects.filter(retailer_name=retailer_name, enable=True).first()
        if link_monetizer:
            # For Extension request, we need to disable Links
            if (is_extension_request and build == "production" and
                link_monetizer.network in 
                [LinkMonetizer.LINKSHARE, LinkMonetizer.SHARE_A_SALE]):
                return purchase_url
            # Get Deep Link based on the Network
            if link_monetizer.network == LinkMonetizer.PJ:
                return generate_pj_deep_link(link_monetizer, purchase_url, user_id)
            elif link_monetizer.network == LinkMonetizer.CJ:
                return generate_cj_deep_link(link_monetizer, purchase_url, user_id)
            elif link_monetizer.network == LinkMonetizer.LINKSHARE:
                return generate_linkshare_deep_link(link_monetizer, purchase_url, user_id)
            elif link_monetizer.network == LinkMonetizer.IMPACT_RADIUS:
                return generate_impact_radius_deep_link(link_monetizer, purchase_url, user_id)
            elif link_monetizer.network == LinkMonetizer.SHARE_A_SALE:
                return generate_share_a_sale_deep_link(link_monetizer, purchase_url, user_id)
            elif link_monetizer.network == LinkMonetizer.AVANTLINKS:
                return generate_avantlinks_deep_link(link_monetizer, purchase_url, user_id)
