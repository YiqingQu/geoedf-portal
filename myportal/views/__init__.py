from django.urls import path, include, re_path
from myportal.views import api_account, api_resource
from myportal.views.file_manager_views import FileManager, delete_file, download_file, upload_file, save_info, \
    create_directory, publish_file
from myportal.views.views import temp_view, file_detail, mysearch, GetAccountProfile
from globus_portal_framework.urls import register_custom_index

register_custom_index('custom_search', ['schema-org-index'])



urlpatterns = [
    # Provides the basic search portal
    path('resource/<uuid>', file_detail, name='resource'),
    path('<custom_search:index>/', mysearch, name='search'),

    path('accounts/', include('allauth.urls')),
    path('accounts/profile/', GetAccountProfile.as_view(), name='account-profile'),
    path('callback/', temp_view, name='temp-view'),

    path('api/resource/get/<uuid>', api_resource.GetResourceSchemaorg.as_view(), name='api-resource-get'),
    path('api/resource/list/', api_resource.GetResourceSchemaorgList.as_view(), name='api-resource-list'),
    path('api/resource/publish/', api_resource.PublishResource.as_view(), name='api-resource-publish'),
    path('api/resource/download/<uuid>', api_resource.DownloadResource.as_view(), name='api-resource-download'),
    path('api/resource/status/<uuid>', api_resource.GetResourceStatus.as_view(), name='api-resource-status'),
    path('api/resource/update/', api_resource.UpdateResource.as_view(), name='api-resource-update'), # update resource info
    path('api/resource/list-user/', api_resource.GetResourceListByUser.as_view(), name='user-resource-list'),

    path('api/accounts/token/verify/', api_account.VerifyToken.as_view(), name='token-verify'),
    path('api/accounts/token/code/', api_account.GetCode.as_view(), name='get-code'),
    path('api/accounts/token/get/', api_account.GetToken.as_view(), name='token-get'),
    path('api/accounts/token/refresh/', api_account.GetToken.as_view(), name='token-refresh'),
    path('api/accounts/profile/', api_account.VerifyToken.as_view(), name='user-profile'),

    path('file/manage/', FileManager.as_view(), name='file-manage'),
    re_path(r'^file/manage/(?P<directory>.*)?/$', FileManager.as_view(), name='file-manage'),
    path('file/delete/<str:file_path>/', delete_file, name='delete_file'),
    path('file/download/<str:file_path>/', download_file, name='download_file'),
    path('file/upload/', upload_file, name='upload_file'),
    path('file/update/<str:file_path>/', save_info, name='save_info'),
    path('file/create-directory/', create_directory, name='create_directory'),
    path('file/publish/', publish_file, name='publish_file'),
]
