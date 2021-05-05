# import cloudsight
# from django.conf import settings
# import uuid
import requests


def get_image_metadata_from_file(imagedata):
    """
    Method to get image metadata from image string.
    """
    try:
        url = 'https://matchos.price.com/apiv2/visualsearch'
        params = {'partner': '5ee01047b94463669b196af5', "format": "raw"}# "Content-Type": "application/x-binary"}
        resp = requests.post(url, params=params, data=imagedata)
    except Exception as e:
        return {'error': str(e)}
    return resp.json()

