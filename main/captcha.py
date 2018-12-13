import configparser
import json
import urllib.request as urllib2
import os
from flask import current_app


def checkRecaptcha(response):
    conf = configparser.ConfigParser()
    conf.read(os.path.join(current_app.instance_path, 'config.ini'))

    url = 'https://google.com/recaptcha/api/siteverify?'
    url += 'secret=' + str(conf['captcha']['captcha_privatekey'])
    url += '&response=' + str(response)

    jsonobj = json.loads(urllib2.urlopen(url).read())
    print(jsonobj['success'])
    if jsonobj['success']:
        return True
    else:
        return False

    
