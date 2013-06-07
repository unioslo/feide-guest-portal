from django.contrib import admin
from guest.models import Guest

class GuestAdmin(admin.ModelAdmin):
    fields = ('uid', 'mail', 'givenName', 'sn', 'userPassword')

admin.site.register(Guest, GuestAdmin)
