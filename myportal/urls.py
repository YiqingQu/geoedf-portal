from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import path, include
from django.views.generic import RedirectView
from globus_portal_framework.urls import register_custom_index

from myportal import views
from myportal.sitemap import GeoFileSitemap
from myportal.views import mysearch, file_detail, temp_view, index_selection

from drf_yasg import openapi
from drf_yasg.views import get_schema_view

register_custom_index('custom_search', ['schema-org-index'])

sitemaps = {
    'geo_file': GeoFileSitemap,
}

schema_view = get_schema_view(
    openapi.Info(
        title="GeoEDF API",
        default_version="v1.0.0",
        description="Generated by Swagger",
    ),
    public=True,
)
urlpatterns = [
    # Provides the basic search portal
    path('<custom_search:index>/resource/<uuid>', file_detail, name='resource'),
    path('<custom_search:index>/', mysearch, name='search'),

    path('api/resource/get/<uuid>', views.GetResourceSchemaorg.as_view(), name='api-resource-get'),
    path('api/resource/list/', views.GetResourceSchemaorgList.as_view(), name='api-resource-list'),
    path('api/accounts/verify/', views.VerifyToken.as_view(), name='account-verify'),

    # path('', index_selection, name='index-selection-p'),
    path('', RedirectView.as_view(url="/schema-org-index/")),
    path('', include('globus_portal_framework.urls')),
    path('', include('social_django.urls', namespace='social')),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('admin/', admin.site.urls),

    # display page
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    path('accounts/', include('allauth.urls')),
    path('accounts/profile/', views.GetAccountProfile.as_view(), name='account-profile'),
    path('callback/', temp_view, name='temp-view'),


] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

