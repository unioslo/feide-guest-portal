## Feide Guest Account Management System.
Created by Morten Olsen Lysgaard @ Uninett, summer 2013

## Install
### Dependencies

* `django 1.4.5`
* `python-ldap` - depends on: `python-dev libldap2-dev libsasl2-dev libssl-dev`
* `django-ldapdb`

The django version used is `django 1.4.5` installed from `Debian wheezy`.

You need the `python-ldap` library because this app and `django-ldapdb` uses it to interface with a LDAP tree.
`python-ldap` has several dependencies for C header files, they are contained in the Debian packages: `python-dev libldap2-dev libsasl2-dev libssl-dev`

Feide Guest depends on python-ldapdb found on: (https://github.com/chronossc/django-ldapdb)
You need it installed in your python path. On the development server this was done the following way:

    git clone git://github.com/chronossc/django-ldapdb.git
    cd django-ldapdb
    sudo pip install

If you don't have pip you can use the standard `python setup.py` method instead.

## Setup
### guest/settings_local.py
Copy `guest/settings_local.py.template` to `guest/settings_local.py` and edit it to fit your installation.

### guest/wsgi.py
Edit `guest/wsgi.py`.
Add the absolute root path of the project to `sys.path` so that imports work correctly.

### mail:
Follow the [django mail guide](https://docs.djangoproject.com/en/dev/topics/email/) to setup a correct mail backend.

### logging:
The application uses logging to warn about potential errors and strange user behaviour. Follow the [django logging guide](https://docs.djangoproject.com/en/dev/topics/logging/)
to setup a correct loggin backend. I suggest that errors are mailed to the server administrator so that he can react on potential problems.

### LDAP:
The application uses LDAP as its user backend. Before you start it you need to configure a correct LDAP database with the correct schema.

* uri for the server
* user
* password
* path for the database

Once this is done the application will hook intoo the database and let users create Feide users with it.
