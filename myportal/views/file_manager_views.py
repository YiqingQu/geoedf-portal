import csv
import datetime
import json
import os
import uuid

import requests
from allauth.socialaccount.models import SocialToken, SocialAccount
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.contrib.sites.models import Site
from django.http import HttpResponseBadRequest, JsonResponse, HttpResponse, Http404
from django.views import View
from drf_yasg import openapi
from globus_portal_framework import gsearch
from globus_portal_framework.apps import get_setting
from globus_portal_framework.gsearch import post_search, get_search_query, get_search_filters, get_template, \
    get_subject, get_index
from django.shortcuts import render, redirect
from django.contrib.sites.shortcuts import get_current_site
from django.utils.functional import SimpleLazyObject
from rest_framework import permissions

from myportal.constants import GLOBUS_INDEX_NAME, FILES_ROOT
from myportal.models import Resource
from myportal.utils import generate_nested_directory
from django.shortcuts import render, redirect
from django.core.files.storage import FileSystemStorage

from myportal.views.api_resource import has_valid_cilogon_token, publish_to_globus_index, get_globus_index_submit_taskid


class FileManager(View):
    permission_classes = (permissions.AllowAny,)

    def get_breadcrumbs(self, request):
        path_components = [component for component in request.path.split("/") if component]
        breadcrumbs = []
        url = ''

        for component in path_components:
            url += f'/{component}'
            if component == "file-manager":
                component = "media"
            breadcrumbs.append({'name': component, 'url': url})

        return breadcrumbs

    def convert_csv_to_text(self, csv_file_path):
        with open(csv_file_path, 'r') as file:
            reader = csv.reader(file)
            rows = list(reader)

        text = ''
        for row in rows:
            text += ','.join(row) + '\n'

        return text

    def get_files_from_directory(self, directory_path):
        files = []
        directories = []
        for filename in os.listdir(directory_path):
            file_path = os.path.join(directory_path, filename)
            if os.path.isfile(file_path):
                try:
                    # print(' > file_path ' + file_path)
                    _, extension = os.path.splitext(filename)
                    if extension.lower() == '.csv':
                        csv_text = self.convert_csv_to_text(file_path)
                    else:
                        csv_text = ''

                    last_modified_time = os.path.getmtime(file_path)
                    file_size = os.path.getsize(file_path)
                    # print("os.sep" + os.sep)
                    files.append({
                        'file': file_path.split(os.sep + 'media' + os.sep)[1],
                        'filename': filename,
                        'file_path': file_path,
                        'visibility': 'private',
                        'last_modified_time': datetime.datetime.fromtimestamp(last_modified_time),
                        'size': file_size,
                        'csv_text': csv_text
                    })
                    continue
                except Exception as e:
                    print(' > ' + str(e))
            if os.path.isdir(file_path):
                try:
                    last_modified_time = os.path.getmtime(file_path)
                    # file_size = os.path.getsize(file_path)
                    # print("os.sep" + os.sep)
                    directories.append({
                        'dir': file_path.split(os.sep + 'media' + os.sep)[1],
                        'dirname': filename,
                        'dir_path': file_path,
                        'visibility': 'private',
                        'last_modified_time': datetime.datetime.fromtimestamp(last_modified_time),
                    })
                    continue
                except Exception as e:
                    print(' > ' + str(e))

        return files, directories

    def get(self, request, directory=settings.MEDIA_ROOT, *args, **kwargs):
        print(request.user)

        user = SocialAccount.objects.get(user=request.user)
        email = user.extra_data["email"]
        # print(f'user= {user.extra_data["email"]}')

        personal_media_path = os.path.join(settings.MEDIA_ROOT, email)
        print(f'personal_media_path= {personal_media_path}')

        if not os.path.exists(personal_media_path):
            os.makedirs(personal_media_path)
        directories = generate_nested_directory(personal_media_path, personal_media_path)
        selected_directory = directory

        files = []
        dirs = []
        selected_directory_path = os.path.join(personal_media_path, selected_directory)
        if os.path.isdir(selected_directory_path):
            files, dirs = self.get_files_from_directory(selected_directory_path)

        breadcrumbs = self.get_breadcrumbs(request)
        context = {
            'directories': directories,
            'files': files,
            'dirs': dirs,
            'selected_directory': selected_directory,
            'segment': 'file_manager',
            'breadcrumbs': breadcrumbs
        }
        print(context)
        return render(request, 'file-management/file-manager.html', context)


def delete_file(request, file_path):
    path = file_path.replace('%slash%', '/')
    absolute_file_path = os.path.join(settings.MEDIA_ROOT, path)
    os.remove(absolute_file_path)
    print("File deleted", absolute_file_path)
    return redirect(request.META.get('HTTP_REFERER'))


def download_file(request, file_path):
    path = file_path.replace('%slash%', '/')
    absolute_file_path = os.path.join(settings.MEDIA_ROOT, path)
    print("[download_file]", absolute_file_path)

    if os.path.exists(absolute_file_path):
        with open(absolute_file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(absolute_file_path)
            return response
    raise Http404


def upload_file(request):
    if request.method == 'POST' and request.FILES['file']:
        if 'file' in request.FILES:
            uploaded_file = request.FILES['file']
        else:
            return JsonResponse({'error': 'file not in FILES'}, status=400)

        directory = request.POST.get('directory')

        fs = FileSystemStorage(
            location=os.path.join(settings.MEDIA_ROOT, directory))  # saves to the 'files' directory under MEDIA_ROOT
        filename = fs.save(uploaded_file.name, uploaded_file)
        file_url = fs.url(filename)  # You can get the file URL if needed

    # return JsonResponse({'message': 'File uploaded successfully!'})
    return redirect(request.META.get('HTTP_REFERER'))


def create_directory(request):
    if request.method == 'POST':
        print("create_directory", request)

        # Get the current directory and the name of the new directory from the POST data
        selected_directory = request.POST.get('current_directory')
        directory_name = request.POST.get('directory_name')

        # Sanitize and validate the input (very important)
        if not directory_name or '..' in directory_name or '/' in directory_name:
            # Return an error response or redirect with an error message
            return HttpResponse("Invalid directory name", status=400)

        # Construct the full path of the new directory
        new_directory_path = os.path.join(settings.MEDIA_ROOT, selected_directory, directory_name)

        # Create the directory
        os.makedirs(new_directory_path, exist_ok=True)

        return redirect(request.META.get('HTTP_REFERER'))

    # If the request method is not POST, redirect or return an error
    return HttpResponse("Method not allowed", status=405)


def save_info(request, file_path):
    path = file_path.replace('%slash%', '/')
    # if request.method == 'POST':
    #     FileInfo.objects.update_or_create(
    #         path=path,
    #         defaults={
    #             'info': request.POST.get('info')
    #         }
    #     )

    return redirect(request.META.get('HTTP_REFERER'))


def publish_file(request):
    user_id = "qu112@purdue.edu"
    publication_name = request.POST.get('publication_name')
    # path = request.POST.get('path')
    path = "data/files/user/wrfinput_private.nc"
    description = request.POST.get('description')
    keywords = request.POST.get('keywords')
    file_uuid = str(uuid.uuid4())
    resource = Resource(uuid=file_uuid,
                        path=path,
                        resource_type="single",
                        user_id=user_id)

    resource.save()
    print(f"[PublishResource] resource={resource.__str__()}")

    publish_to_globus_index(resource)
    task_id = get_globus_index_submit_taskid(resource)
    resource.task_id = task_id
    resource.save()

    resp = {
        "status": "Submitted",
        "uuid": file_uuid,
        "path": path,
        "task_id": task_id,
    }

    return redirect(request.META.get('HTTP_REFERER'))
