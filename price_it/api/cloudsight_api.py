import urllib
import base64
import requests

from django.http import JsonResponse
from core.cloudsight.image_metadata import get_image_metadata_from_file

from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def get_image_details(request):
    """
    API to fetch image metadata from image url.
    """
    url = ''
    cropped_image = ''

    if request.method == "GET":
        url = request.GET.get('url', '')
        if not url:
            return JsonResponse({'error': 'Please pass a url'})
    elif request.method == "POST":
        cropped_image = str(request.POST.get('cropped_image', '')).strip()
        if not cropped_image:
            return JsonResponse({'error': 'Please pass a cropped_image'})
    else:
        return JsonResponse({'error': 'Invalid request'})

    if cropped_image:
        # Converting base64 to image.
        encoded_image = cropped_image.split(',')[-1]
        imgdata = ''
        try:
            print("shoooo")
            imgdata = base64.standard_b64decode(encoded_image)
        except Exception as err:
            # Incase of encoding error.
            print("encodingGG")
            image_details = {}
            image_details['success'] = False
            image_details['message'] = str(err)
        if imgdata:
            image_details = get_image_metadata_from_file(imgdata)
        '''# Sending base64 to get image url
        response = convert_base64_to_image(cropped_image)
        # Checking for success.
        if not response['success']:
            # Returning error message.
            return JsonResponse(response)
        # On success extracting url.
        url = response['url']'''
    if url:
        img_url = url.strip()
        img_url = urllib.parse.unquote(urllib.parse.unquote(img_url))
        print("img_url", img_url)
        imgdata = get_image_data_from_url(img_url)
        image_details = {}
        if imgdata:
            image_details = get_image_metadata_from_file(imgdata)

        #image_details = get_image_metadata(img_url)
    return JsonResponse(image_details)


def get_image_url_details(url):
    """API to fetch image details from image url.
    """
    if not url:
        return ''
    img_url = url.strip()
    img_url =  urllib.unquote(urllib.unquote(img_url))
    print "img_url", img_url
    imgdata = get_image_data_from_url(img_url)
    image_details = {}

    if imgdata:
        image_details = get_image_metadata_from_file(imgdata)

    if image_details:
        if str(image_details.get('status', '')) == 'completed':
            return str(image_details.get('name', ''))

    return image_details


def get_image_data_from_url(url):
    try:
        response = requests.get(url, timeout=10)
        content = response.content
    except Exception as e:
        print("E", e)
        content = ''
    return content
