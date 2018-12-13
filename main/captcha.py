import configparser
import json
import urllib.request
import os
from flask import current_app


def checkRecaptcha(response):
    conf = configparser.ConfigParser()
    conf.read(os.path.join(current_app.instance_path, 'config.ini'))

    url = 'https://google.com/recaptcha/api/siteverify?'
    url += 'secret=' + str(conf['captcha']['captcha_secretkey'])
    url += '&response=' + str(response)

    res_body = urllib.request.urlopen(url).read()
    jsonobj = json.loads(res_body.decode("utf-8"))
    
    # print(jsonobj['success'])
    if jsonobj['success']:
        return True
    else:
        return False

    
