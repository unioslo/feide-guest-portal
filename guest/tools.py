from hashlib import sha1
from base64 import b64encode, b64decode
from django.conf import settings

from guest.models import Guest

import os
import ldap

# function to generate SSHA salted and hashed passwords
# for LDAP. Reference:
# http://www.openldap.org/faq/data/cache/347.html
def ssha(secret):
    secret = unicode(secret).encode('utf-8')
    salt = os.urandom(13) # 13 bytes of salt
    m = sha1(secret + salt)
    return '{SSHA}' + b64encode(m.digest() + salt)

def bind(user, pwd):
    settings_dict = settings.DATABASES['default']
    try:
        connection = ldap.initialize(settings_dict['NAME'])                                                                                                   
        connection.simple_bind_s(user,pwd) 
        return True
    except ldap.INVALID_CREDENTIALS:
        return False
