# Install
## Dependencies

* django 1.4.5
* python-ldap - depends on: python-dev libldap2-dev libsasl2-dev libssl-dev
* django-ldapdb

The django version used is django 1.4.5 installed from Debian wheezy.

You need the python-ldap library because this app and django-ldapdb uses it to interface with a LDAP tree.
python-ldap has several dependencies for C header files, they are contained in the Debian packages: python-dev libldap2-dev libsasl2-dev libssl-dev

Feide Guest depends on python-ldapdb found on: https://github.com/chronossc/django-ldapdb
You need it installed in your python path. On the development server this was done the following way:

    git clone git://github.com/chronossc/django-ldapdb.git
    cd django-ldapdb
    sudo pip install .

If you don't have pip you can use the standard `python setup.py` method instead.
