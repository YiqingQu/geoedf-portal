import os

from django.apps import AppConfig


# from django.contrib.sites.models import Site


class MyportalConfig(AppConfig):
    name = 'myportal'

    def ready(self):
        print("myportal is ready！")

        # site = Site.objects.first()
        # host = os.environ.get("SITE_HOST", default="localhost:8000")
        # #
        # # site.domain = host
        # # site.name = host
        # site.save()
