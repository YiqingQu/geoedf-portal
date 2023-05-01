from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import path, include, re_path
from django.views.generic import RedirectView
from rest_framework import permissions

from .views import urlpatterns as views_urlpatterns
from myportal.sitemap import GeoFileSitemap
from myportal.views.views import index_selection
from drf_yasg import openapi
from drf_yasg.views import get_schema_view


sitemaps = {
    'geo_file': GeoFileSitemap,
}

schema_view = get_schema_view(
    openapi.Info(
        title="GeoEDF API",
        default_version="v1.0.2",
        description="Generated by Swagger",
        public=True,
        # permission_classes=[permissions.AllowAny],
    ),
    public=True,
)

urlpatterns = [
    path('', include(views_urlpatterns)),

    path('index/selection/', index_selection, name='index-selection-p'),
    path('', RedirectView.as_view(url="/schema-org-index/")),
    path('', include('globus_portal_framework.urls')),
    path('', include('social_django.urls', namespace='social')),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('admin/', admin.site.urls),

    # display page
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

