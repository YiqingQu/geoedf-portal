import os
import uuid

import globus_sdk
import requests
from django.contrib.auth.models import AnonymousUser
from django.contrib.sites.models import Site
from globus_portal_framework import post_search
from globus_portal_framework.apps import get_setting
from globus_sdk.scopes import SearchScopes

from myportal.models import Resource


def verify_cilogon_token(access_token):
    userinfo = requests.post(
        'https://cilogon.org/oauth2/userinfo',
        data={
            'access_token': access_token,
        },
    )

    if not userinfo.ok:
        return None
    return userinfo.json()


def get_domain_name():
    site = Site.objects.get(id=1)
    return site.domain


def get_resource_id_list():
    query = get_setting('DEFAULT_QUERY')
    id_list = []

    page = 1
    has_more = True
    while has_more:
        search_result = post_search('list-search-index', query, [], AnonymousUser(),
                                    page)
        for subject_data in search_result['search_results']:
            id_list.append(subject_data['subject'])
        if len(search_result['pagination']['pages']) > page:
            page += 1
        else:
            has_more = False

    print(f'[get_resource_id_list] id_list={id_list}')
    return id_list


def get_resource_list_by_id(user_id):
    resource = Resource.objects.filter(user_id=user_id)
    return resource


def generate_nested_directory(root_path, current_path):
    directories = []
    for name in os.listdir(current_path):
        if os.path.isdir(os.path.join(current_path, name)):
            unique_id = str(uuid.uuid4())
            nested_path = os.path.join(current_path, name)
            nested_directories = generate_nested_directory(root_path, nested_path)
            directories.append({'id': unique_id, 'name': name, 'path': os.path.relpath(nested_path, root_path), 'directories': nested_directories})
    return directories


def app_search_client(authenticated=True):
    # CLIENT_ID = "ed8b9705-b6d4-44d5-aab5-5f0dc6d73dc5"
    # CLIENT_SECRET = "7/K6vfoUo7ONioH6QNedfyOq0mnHJocOnedtJGGggHA="

    # service account MetadataExtractor token
    CLIENT_ID = "0f657343-4e07-4c37-b203-ff3eec9d4b9f"
    CLIENT_SECRET = "MZi3nwu5tmK4XZhqazQDRYuAlFPVC18iZkTrSvpQKOc="

    client = globus_sdk.ConfidentialAppAuthClient(CLIENT_ID, CLIENT_SECRET)
    # scopes = "urn:globus:scopes:search.api.globus.org:all"
    scopes = SearchScopes.all
    cc_authorizer = globus_sdk.ClientCredentialsAuthorizer(client, scopes)
    return globus_sdk.SearchClient(authorizer=cc_authorizer, app_name="geoedf-portal")


