import json
import requests
import urllib

from celery import task

from PriceIT.api.cloudsight_api import get_image_url_details


@task
def get_image_details_from_image_url(image_url, sender, bot_key):
    response = get_image_url_details(image_url)

    headers = {
        'Content-Type': 'application/json',
    }

    if response:
        msg = 'This feature is still in beta -- Click here to access all the shopping options.'
        msg += '\nFor optimal results, please reply with a copy and paste of the product page URL.'
        button_text = "Shop Now"
        button_url = "https://price.com/search?%s" %(urllib.urlencode({'query': response}))
        data = {
                "recipient":{
                    "id": sender
                },
                "message":{
                      "attachment":{
                "type":"template",
                "payload":{
                  "template_type":"button",
                  "text": msg,
                      "buttons":[
                        {
                          "type":"web_url",
                          "url": button_url,
                          "title": button_text
                        },
                    ]
                  }
                  } }
            }
    else:
        msg = ":-( I can't analyze the image you sent. Please send another?"
        data = {
            "recipient":{
                "id": sender
            },
            "message":{
                "text": msg
            }
        }
    data = json.dumps(data)
    r = requests.post('https://graph.facebook.com/v2.6/me/messages?access_token=%s' %(bot_key), headers=headers, data=data)
