import json
import os

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.contrib.sites.models import Site
from django.http import HttpResponseBadRequest, JsonResponse, HttpResponse, Http404
from django.views import View
from globus_portal_framework.apps import get_setting
from globus_portal_framework.gsearch import post_search, get_search_query, get_search_filters, get_template, \
    get_subject
from django.contrib.sites.shortcuts import get_current_site
from django.utils.functional import SimpleLazyObject

from myportal.constants import GLOBUS_INDEX_NAME
from django.shortcuts import render


def mysearch(request, index):
    query = get_search_query(request)
    # print(f'[mysearch]{query}')
    filters = get_search_filters(request)
    print(f"[mysearch] user={AnonymousUser()}")

    search_result = post_search(GLOBUS_INDEX_NAME, query, filters, AnonymousUser(),
                                request.GET.get('page', 1))
    print(f'[mysearch]search_result = {search_result}')
    context = {'search': search_result}
    return render(request, get_template(index, 'schema-org-index/components/search-results.html'), context)


def file_detail(request, uuid):
    index = GLOBUS_INDEX_NAME
    subject = get_subject(index, uuid, AnonymousUser())
    print(f"[file_detail] subject={subject}")
    try:
        endpoint = subject['all'][0]
    except KeyError:
        context = {
            "error": {
                "code": 500,
                "msg": "Unable to fetch the resource. Please check if the resource id exists."
            }
        }
        return render(request, get_template(index, 'error.html'), context)

    schemaorg_json = endpoint['schemaorgJson']

    detail = {'id': schemaorg_json['@id'],
              # 'subject': subject['subject'],
              'size_bytes': subject['size_bytes'],
              'date_published': schemaorg_json.get('datePublished', ''),
              'date_modified': schemaorg_json.get('dateModified', ''),
              'keywords': schemaorg_json['keywords'],
              }

    if 'creator' in schemaorg_json and schemaorg_json['creator'] is not None:
        detail['creator'] = schemaorg_json['creator']['@list'][0]['email']
    if 'spatialCoverage' in schemaorg_json:
        if schemaorg_json['spatialCoverage'] is not None:
            if schemaorg_json['spatialCoverage']['@type'] == 'Place':
                detail['spatial_coverage'] = schemaorg_json['spatialCoverage']
                detail['spatial_coverage_values'] = schemaorg_json['spatialCoverage']['geo']['box']
    if 'temporalCoverage' in schemaorg_json:
        detail['temporal_coverage'] = schemaorg_json['temporalCoverage']

    # print(f"[file_detail] detail={detail}")

    title = schemaorg_json['name']

    context = {'title': title,
               'detail': detail,
               'schemaorg_json': json.dumps(schemaorg_json, indent=4)
               }

    return render(request, get_template(index, 'schema-org-index/detail-overview.html'), context)


def update_site_domain():
    # Site = apps.get_model("sites", "Site")
    try:
        site = Site.objects.get(id=1)
        # host = getattr(settings, "SITE_NAME", None)
        host = os.environ.get('SITE_NAME', 'localhost:8000')
        print(f"[update_site_domain] host={host}")
        site.domain = host
        site.name = host
        site.save()

    except:
        pass


def update_social_app():
    try:
        site = Site.objects.get(id=1)
        # host = getattr(settings, "SITE_NAME", None)
        host = os.environ.get('SOCIAL_APP_cilogon', 'localhost:8000')
        print(f"[update_social_app] host={host}")
        site.domain = host
        site.name = host
        site.save()

    except:
        pass


def set_django_configurations():
    update_site_domain()
    update_social_app()


set_django_configurations()


def index_selection(request):
    print(f"[index_selection] request={request}")

    context = {
        'search_indexes': get_setting('SEARCH_INDEXES'),
        'allowed_groups': getattr(settings,
                                  'SOCIAL_AUTH_GLOBUS_ALLOWED_GROUPS', [])
    }
    return render(request, 'index-selection.html',
                  context)


def temp_view(request):
    return render(request, 'schema-org-index/detail-overview.html', {})


def site(request):
    return {
        'site': SimpleLazyObject(lambda: get_current_site(request)),
    }


class GetDomainName(View):
    def get(self, request, *args, **kwargs):
        site = Site.objects.get(id=1)
        print(f"[GetDomainName] site.domain={site.domain}")
        data = {'domain': site.domain}
        return JsonResponse(data)


class GetAccountProfile(View):
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return render(request, 'error.html', {})
        user = request.user
        # print(f"[GetAccountProfile] user={user.socialaccount_set}")
        # cilogon_account = request.user.socialaccount_set.filter(provider='cilogon').first()

        # cilogon_access_token = cilogon_account.socialtoken_set.filter(token_type='access_token').first().token
        # cilogon_refresh_token = cilogon_account.socialtoken_set.filter(token_type='refresh_token').first().token
        # print(f"[GetAccountProfile] cilogon_access_token={cilogon_access_token}")
        # print(f"[GetAccountProfile] cilogon_refresh_token={cilogon_refresh_token}")

        context = {'username': request.user}
        return render(request, 'account/profile.html', context)
