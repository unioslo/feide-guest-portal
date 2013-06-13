from django.conf import settings

def languages_context_processor(request):
    return {'LANGUAGES': settings.LANGUAGES}
