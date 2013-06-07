from django.conf import settings

#from django.db import models
#from django.db.models.fields import CharField

from ldapdb import models
from ldapdb.models.fields import CharField

#class Guest(models.Model):
class Guest(models.Model):
    """
    Class for representing an Guest in the Feide system.
    """
    # LDAP meta-data
    base_dn = settings.LDAP_GUEST_BASE_DN
    object_classes = ['inetOrgPerson', 'organizationalPerson', 'person', 'top', 'eduPerson', 'norEduPerson']


    # all these fields, except mail, are computed by three attributes:
    # username, given name and surname. These are combined to create
    # the attributes in the LDAP tree. To do this transparently we
    # use django properties and getters and setters.
    uid = CharField(db_column='uid', verbose_name='username', primary_key=True, unique=True, null=False, max_length=256)
    mail = CharField(db_column='mail', verbose_name='mail', unique=True, null=True, max_length=256)
    userPassword = CharField(db_column='userPassword', verbose_name='password', null=False, max_length=256)
    eduPersonPrincipalName = CharField(db_column='eduPersonPrincipalName', verbose_name='realm', null=False, max_length=256)
    givenName = CharField(db_column='givenName', verbose_name='given name', null=False, max_length=256)
    sn = CharField(db_column='sn', verbose_name='surname', null=False, max_length=256)
    cn = CharField(db_column='cn', verbose_name='common name', null=False, max_length=256)
    displayName = CharField(db_column='displayName', verbose_name='display name', null=False, max_length=256)

    def save(self, *args, **kwargs):
        self.eduPersonPrincipalName = self.uid + '@' + settings.GUEST_REALM
        fullName = u'%s %s' % (self.givenName, self.sn)
        self.cn = fullName
        self.displayName = fullName
        super(Guest, self).save(*args, **kwargs)

    def __str__(self):
        return u'%s, %s, %s' % (self.uid, self.mail, self.displayName)

    def __unicode__(self):
        return u'%s, %s, %s' % (self.uid, self.mail, self.displayName)
