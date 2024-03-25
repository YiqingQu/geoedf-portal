import json
import os
import uuid
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from tempfile import TemporaryDirectory
from wsgiref.util import FileWrapper

import pika
import requests
from django.contrib.auth.models import AnonymousUser

from django.http import HttpResponseBadRequest, HttpResponse
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from globus_portal_framework import get_subject
from rest_framework import status, permissions, serializers
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from myportal import settings
from myportal.constants import GLOBUS_INDEX_NAME, RMQ_NAME, RMQ_USER, RMQ_PASS, RMQ_HOST
from myportal.models import Resource
from myportal.utils import verify_cilogon_token, get_resource_id_list, get_resource_list_by_id, app_search_client


class GetResourceSchemaorg(APIView):
    permission_classes = (permissions.AllowAny,)

    @swagger_auto_schema()
    def get(self, request, uuid):
        """
            Retrieve the Schema.Org metadata for a resource by its UUID.
        """
        print(f"[GetResourceSchemaorg] user={request.user}")
        if not has_valid_cilogon_token(request.headers):
            return Response(
                data={"status": "Please log in first"},
                status=status.HTTP_200_OK,
            )

        subject = get_subject(GLOBUS_INDEX_NAME, uuid, AnonymousUser())
        print(f"[GetResourceSchemaorg] subject={subject}")
        try:
            endpoint = subject['all'][0]
        except KeyError:
            return Response(
                data={"status": "UUID does not exist"},
                status=status.HTTP_200_OK,
            )
        schemaorg_json = endpoint['schemaorgJson']
        return Response(
            data={"status": "OK", "schemaorg": schemaorg_json},
            status=status.HTTP_201_CREATED,
        )


class GetResourceSchemaorgListRequest(serializers.Serializer):
    id_list = serializers.ListField(help_text='The list of resource UUIDs')

    class Meta:
        swagger_schema_fields = {
            "example": {
                "id_list": ["62b507fb-f69b-4e7c-a112-4302dd269146", "6bead1d9-7383-4676-9cef-9190f5e74064"],
            }
        }


class GetResourceSchemaorgList(APIView):
    permission_classes = (permissions.AllowAny,)

    @swagger_auto_schema()
    def get(self, request):
        """
            Retrieve the list of UUIDs for all resources. (todo: Pagination)
        """
        if not has_valid_cilogon_token(request.headers):
            return Response(
                data={"status": "Please log in first"},
                status=status.HTTP_200_OK,
            )
        list = get_resource_id_list()
        return Response(
            data={"list": list, "total": len(list)},
            status=status.HTTP_200_OK,
        )
        # serializer = GetResourceSchemaorgListRequest(data=request.data)
        # if serializer.is_valid():
        #     subject = get_subject(GLOBUS_INDEX_NAME, request.id_list, request.user)  # todo
        #     print(f"[ListResourceSchemaorg] subject={subject}")
        #     try:
        #         endpoint = subject['all'][0]
        #     except KeyError:
        #         return Response(
        #             data={"status": "UUID does not exist"},
        #             status=status.HTTP_200_OK,
        #         )
        #     schemaorg_json = endpoint['schemaorgJson']
        #     return Response(
        #         data={"status": "OK", "schemaorg_list": [schemaorg_json]},
        #         status=status.HTTP_201_CREATED,
        #     )
        # return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GetResourceListByUserRequest(serializers.Serializer):
    page = serializers.IntegerField(min_value=1, required=False, help_text="Page number for pagination")
    page_size = serializers.IntegerField(min_value=1, max_value=100, required=False,
                                         help_text="Number of items per page")

    class Meta:
        swagger_schema_fields = {
            "example": {
                "page": 1,
                "page_size": 10,
            }
        }


class GetResourceListByUser(APIView):
    permission_classes = (permissions.AllowAny,)

    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter('Authorization', openapi.IN_HEADER, description='Authentication token',
                          type=openapi.TYPE_STRING, required=True, ),
        openapi.Parameter('page', openapi.IN_QUERY, description='Page number of the results to retrieve',
                          type=openapi.TYPE_INTEGER),
        openapi.Parameter('page_size', openapi.IN_QUERY, description='Number of results per page',
                          type=openapi.TYPE_INTEGER),
    ],
    )
    def get(self, request):
        """
            Retrieve the list of UUIDs for all resources.
        """
        user_id = get_jupyter_username(request.headers)
        if user_id is None:
            return Response(
                data={"status": "Please log in first"},
                status=status.HTTP_200_OK,
            )

        resources = get_resource_list_by_id(user_id)  # Make sure this function accepts a user_id parameter

        def fetch_task_data(resource):
            try:
                if resource.status == "SUCCESS":
                    return
                else:
                    globus_sdk_client = app_search_client()
                    res = globus_sdk_client.get_task(resource.task_id)
                    resource.status = res.get('state')
                    resource.save()
                return {
                    "title": resource.publication_name,
                    "status": res.get('state'),
                    "state_description": res.get('state_description'),
                    "completion_date": res.get('completion_date'),
                    "modified_time": resource.modified_time,
                }
            except Exception as e:
                print(f"Error obtaining task for resource {resource.task_id}: {e}")
                return None

        # Use ThreadPoolExecutor to fetch task data in parallel
        tasks = []
        with ThreadPoolExecutor(max_workers=10) as executor:  # Adjust max_workers as needed
            for resource in resources:
                if resource.task_id is None:
                    continue
                tasks.append(executor.submit(fetch_task_data, resource))

        # Collect results from futures
        results = [task.result() for task in as_completed(tasks) if task.result() is not None]
        # print(f"request. {request.query_params}: {e}")

        paginator = PageNumberPagination()
        result_page = paginator.paginate_queryset(results, request)
        return paginator.get_paginated_response({"list": result_page, "total": len(results)})


def has_valid_cilogon_token(headers):
    authorization_header = headers.get('Authorization')
    if not authorization_header or not authorization_header.startswith('Bearer '):
        return HttpResponseBadRequest('Invalid Authorization header')
    access_token = authorization_header[len('Bearer '):]
    if verify_cilogon_token(access_token) is None:
        return False
    return True


def get_jupyter_username(headers):
    token = headers.get('Authorization')
    if not token:
        return HttpResponseBadRequest('Invalid Authorization header')

    url = f"{JUPYTERHUB_URL}/user"
    headers = {
        'Authorization': f'token {token}',
    }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Error fetching user info: {response.status_code}")
        return None
    user_info = response.json()
    username = user_info.get('name', None)  # Default to 'Unknown' if not found
    return username


# Replace these variables with your actual JupyterHub URL and API token
JUPYTERHUB_URL = 'https://geoedf-jupyter.anvilcloud.rcac.purdue.edu/hub/api'
API_TOKEN = '2ae8ff01aec74a5d9662691ebb2f2d54'


class PublishResourceRequest(serializers.Serializer):
    RESOURCE_TYPE_CHOICES = [
        ('single', 'Single'),
        ('list', 'List'),
        ('multiple', 'Multiple'),
    ]
    PUBLICATION_TYPE_CHOICES = [  # todo refine capital letters
        ('Geospatial Files', 'Geospatial Files'),
        ('Workflow', 'Workflow'),
        ('Other Files', 'Other Files'),
    ]

    publication_name = serializers.CharField(
        required=False,
        help_text='The name of the publication.',
    )
    resource_type = serializers.ChoiceField(
        choices=RESOURCE_TYPE_CHOICES,
        required=False,
        help_text='The type of resource being published. Must be one of "single", "list", or "multiple".',
    )
    path = serializers.CharField(
        required=False,
        help_text='The path to the resource. Only valid if resource_type is "single" or "multiple".',
    )
    path_list = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text='A list of paths to the resources being published. Only valid if resource_type is "list".',
    )

    publication_type = serializers.ChoiceField(
        choices=PUBLICATION_TYPE_CHOICES,
        required=False,
        help_text='The type of publication. Must be one of "Geospatial Files", "Workflow", or "Other Files".',
    )
    description = serializers.CharField(
        required=False,
        help_text='The description of the publication.',
    )
    keywords = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text='The keywords of the publication.',
    )

    class Meta:
        swagger_schema_fields = {
            "example": {
                "publication_name": "Riv2",
                "resource_type": "multiple",
                "path_list": ["data/files/Riv2", "data/files/wrfinput_d0x.nc"],
            }
        }
        # example for jupyter app:
        # {
        #     'publication_name': '1',
        #     'description': '123',
        #     'keywords': ['123132'],
        #     'publication_type': 'Workflow',
        #     'staging_path': '/staging/20240311085349'
        # }


# class PublishResourceResponseSerializer():
#     # id = serializers.IntegerField()
#     filepath = serializers.CharField()


class PublishResource(APIView):
    permission_classes = (permissions.AllowAny,)

    @swagger_auto_schema(request_body=PublishResourceRequest,
                         manual_parameters=[
                             openapi.Parameter('Authorization', openapi.IN_HEADER, description='Authentication token',
                                               type=openapi.TYPE_STRING, required=True, ),
                         ],
                         responses={
                             status.HTTP_200_OK: openapi.Response('Success message',
                                                                  schema=openapi.Schema(type='object')),
                             status.HTTP_400_BAD_REQUEST: openapi.Response('Error message',
                                                                           schema=openapi.Schema(type='object')),
                         },
                         )
    def post(self, request):
        """
            Calling this API will create a Resource object in database and publish it.
            Upon successful creation, a message will be sent to a RabbitMQ queue named 'geoedf-all'. The message will
            then be consumed by a metadata extractor.
        """
        print(f"[PublishResource] user={request.user}")
        # recover login check
        user_id = get_jupyter_username(request.headers)
        if not has_valid_cilogon_token(request.headers) and user_id is None:
            return Response(
                data={"status": "Please log in first"},
                status=status.HTTP_200_OK,
            )
        print(f"[PublishResource] user from token={user_id}")

        serializer = PublishResourceRequest(data=request.data)
        if serializer.is_valid():
            file_uuid = str(uuid.uuid4())
            resource = Resource(uuid=file_uuid,
                                user_id=user_id)
            if 'resource_type' in serializer.validated_data:
                resource.resource_type = serializer.validated_data['resource_type']
            if 'publication_type' in serializer.validated_data:
                resource.resource_type = 'multiple'
            if 'publication_name' in serializer.validated_data:
                resource.publication_name = serializer.validated_data['publication_name']
            if 'path' in serializer.validated_data:
                path = serializer.validated_data['path']
                if user_id is not None:
                    try:
                        path = f"/staging/{user_id}/{path.split('/')[-1]}"
                    except Exception:
                        pass
                resource.path = path
            if 'path_list' in serializer.validated_data:
                resource.path = str(serializer.validated_data['path_list'])[1:-1]

            if 'description' in serializer.validated_data:
                resource.description = serializer.validated_data['description']
            if 'keywords' in serializer.validated_data:
                resource.keywords = serializer.validated_data['keywords']
            resource.save()
            print(f"[PublishResource] resource={resource.__str__()}")

            publish_to_globus_index(resource)
            task_id = get_globus_index_submit_taskid(resource)
            resource.task_id = task_id
            resource.save()
            return Response(
                data={"status": "Submitted", "uuid": file_uuid,
                      "path": resource.path,
                      "task_id": task_id,
                      },
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def publish_to_globus_index(resource):
    credentials = pika.PlainCredentials(RMQ_USER, RMQ_PASS)
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RMQ_HOST, port=5672, virtual_host='/', credentials=credentials))

    channel = connection.channel()

    channel.queue_declare(queue=RMQ_NAME)

    publish_data = {
        "uuid": resource.uuid,
        "publication_name": resource.publication_name,
        "type": resource.resource_type,
        "path": resource.path,
        "user_id": resource.user_id,
        "description": resource.description,
        "keywords": resource.keywords,  # todo
        "publication_type": resource.publication_type,
        # "resource_type": "multiple",
    }
    if resource.description is not None:
        publish_data['description'] = resource.description
    if resource.task_id is not None:
        publish_data['task_id'] = resource.task_id
    if resource.extra_info is not None:
        publish_data['extra_info'] = resource.extra_info

    print(f'[publish_to_globus_index] publish_data={publish_data}')

    # Send the message to the queue
    message = json.dumps(publish_data)
    # todo get task id

    channel.basic_publish(exchange='',
                          routing_key=RMQ_NAME,
                          body=message.encode("utf-8"))
    # body=json.dumps(message).encode("utf-8"))

    # Close the connection
    connection.close()


def get_globus_index_submit_taskid(resource):
    # "d03eb370-49a9-4d59-8791-5bcf9635d65a"
    return uuid.uuid4()


class GetResourceStatus(APIView):
    permission_classes = (permissions.AllowAny,)

    @swagger_auto_schema(manual_parameters=[], )
    def get(self, request, uuid):
        """
            Retrieve the basic infomation for a resource by its UUID.
        """
        print(f"[GetResourceStatus] user={request.user}")
        # if not has_valid_cilogon_token(request.headers):
        #     return Response(
        #         data={"status": "Please log in first"},
        #         status=status.HTTP_200_OK,
        #     )

        # file_uuid = str(uuid.uuid4())
        # uuid = serializer.validated_data['uuid']
        print(f"[GetResourceStatus] uuid={uuid}")
        try:
            resource = Resource.objects.get(uuid=uuid)
        except Exception as e:
            return Response(
                data={"msg": f"Error info = {e}"},
                status=status.HTTP_200_OK,
            )

        return Response(
            data={"status": "OK",
                  "uuid": resource.uuid,
                  "file_path": resource.path,
                  # "file_path": serializer.validated_data['path'],
                  "task_id": resource.task_id,
                  "task_status": "tasks completed successfully",
                  },
            status=status.HTTP_201_CREATED,
        )


class UpdateResourceRequest(serializers.Serializer):
    uuid = serializers.IntegerField()
    publication_name = serializers.CharField(
        required=False,
        help_text='The name of the publication.',
    )
    # resource_type = serializers.ChoiceField(
    #     choices=RESOURCE_TYPE_CHOICES,
    #     help_text='The type of resource being published. Must be one of "single", "list", or "multiple".',
    # )
    path = serializers.CharField(
        required=False,
        help_text='The path to the resource. Only valid if resource_type is "single" or "multiple".',
    )
    path_list = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text='A list of paths to the resources being published. Only valid if resource_type is "list".',
    )
    user_id = serializers.CharField()

    class Meta:
        swagger_schema_fields = {
            "example": {
                "publication_name": "Riv2",
                "resource_type": "multiple",
                "path_list": ["data/files/Riv2", "data/files/wrfinput_d0x.nc"],
            }
        }


class UpdateResource(APIView):
    permission_classes = (permissions.AllowAny,)

    @swagger_auto_schema(request_body=UpdateResourceRequest,
                         responses={
                             status.HTTP_200_OK: openapi.Response('Success message',
                                                                  schema=openapi.Schema(type='object')),
                             status.HTTP_400_BAD_REQUEST: openapi.Response('Error message',
                                                                           schema=openapi.Schema(type='object')),
                         }, )
    def post(self, request):
        """
            Calling this API will update the existed Resource object in database.
            Mainly used to update the status queried from Globus Index submission task.
        """
        print(f"[UpdateResource] user={request.user}")

        if not has_valid_cilogon_token(request.headers):
            return Response(
                data={"status": "Please log in first"},
                status=status.HTTP_200_OK,
            )
        serializer = UpdateResourceRequest(data=request.data)
        if serializer.is_valid():
            resource = Resource.objects.get(uuid=serializer.validated_data['uuid'])
            resource.task_id = serializer.validated_data['task_id']
            resource.user_id = serializer.validated_data['user_id']
            resource.save()
            print(f"[UpdateResource] resource={resource.__str__()}")

            return Response(
                data=json.dumps(resource),
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DownloadResource(APIView):
    permission_classes = (permissions.AllowAny,)

    @swagger_auto_schema(manual_parameters=[
    ], )
    def get(self, request, uuid):
        """
            Download a resource by its UUID.
        """

        resource_dir = os.path.join('/persistent', uuid)
        # resource_dir = os.path.join(settings.MEDIA_ROOT)
        print(f"[DownloadResource] resource_dir={resource_dir}")

        if not os.path.exists(resource_dir):
            return Response(
                data={"status": "Resource not found"},
                status=status.HTTP_200_OK,
            )

        files = os.listdir(resource_dir)
        if not files:
            return Response(
                data={"status": "No files to download for this resource"},
                status=status.HTTP_200_OK,
            )

        if len(files) == 1 and os.path.isfile(os.path.join(resource_dir, files[0])):
            # Serve the single file directly
            file_path = os.path.join(resource_dir, files[0])
            file = open(file_path, 'rb')
            response = Response(FileWrapper(file), content_type='application/octet-stream')
            response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
            return response
        else:
            # Zip and serve multiple files
            with TemporaryDirectory() as temp_dir:
                zip_name = f"{uuid}.zip"
                zip_path = os.path.join(temp_dir, zip_name)

                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(resource_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            zipf.write(file_path, arcname=os.path.relpath(file_path, start=resource_dir))

                with open(zip_path, 'rb') as file:
                    response = HttpResponse(FileWrapper(file), content_type='application/zip')
                    response['Content-Disposition'] = f'attachment; filename="{zip_name}"'
                    return response
