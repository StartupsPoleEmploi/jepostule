from django.conf import settings

def template_settings(request):
    return {
        'GOOGLE_ANALYTICS_TRACKING_ID': settings.GOOGLE_ANALYTICS_TRACKING_ID,
        'HOTJAR_SITE_ID': settings.HOTJAR_SITE_ID,
    }
