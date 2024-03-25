import datetime
import time

from django.contrib.auth.models import AnonymousUser
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from globus_portal_framework.apps import get_setting
from globus_portal_framework.gsearch import get_search_query, get_search_filters, post_search

from myportal.utils import get_resource_id_list


class GeoFileSitemap(Sitemap):
    changefreq = 'daily'
    priority = 0.6
    protocol = 'https'

    def items(self):
        return get_resource_id_list()

    def lastmod(self, obj):
        return datetime.datetime.now()

    def location(self, obj):
        # reverse(obj)
        return reverse('resource', kwargs={'uuid': obj})
