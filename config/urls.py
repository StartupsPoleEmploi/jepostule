from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic.base import RedirectView
from django.views.static import serve as static_serve

urlpatterns = [
    path('', RedirectView.as_view(pattern_name="embed:demo"), name='home'),
    path('auth/', include(('jepostule.auth.urls', 'auth'))),
    path('embed/', include(('jepostule.embed.urls', 'embed'))),
    path('', include(('jepostule.pipeline.urls', 'pipeline'))),
    path('admin/', admin.site.urls),
]

# For now, we serve static assets from django. Yes, we know it's bad.
urlpatterns += [
    re_path(
        r'^%s(?P<path>.*)$' % settings.STATIC_URL.lstrip('/'),
        static_serve, kwargs={'document_root': settings.STATIC_ROOT}
    ),
]
