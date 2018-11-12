from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic.base import RedirectView

urlpatterns = [
    path('', RedirectView.as_view(pattern_name="embed:demo"), name='home'),
    path('auth/', include(('jepostule.auth.urls', 'auth'))),
    path('embed/', include(('jepostule.embed.urls', 'embed'))),
    path('', include(('jepostule.pipeline.urls', 'pipeline'))),
    path('admin/', admin.site.urls),
]

# For now, we serve static assets from django. Yes, we know it's bad.
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
