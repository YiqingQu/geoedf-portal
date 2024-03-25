from django.http import HttpResponseBadRequest
from django.shortcuts import render
from django.views import View
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.response import Response
from rest_framework import status, permissions, serializers
from rest_framework.views import APIView
import requests

from myportal.utils import get_domain_name


class GetTokenRequest(serializers.Serializer):
    header_token = serializers.CharField()
    pass


class GetToken(APIView):
    permission_classes = (permissions.AllowAny,)

    @swagger_auto_schema(request_body=GetTokenRequest, )
    def post(self, request):
        """
        Return the Access Token
        """
        return Response(
            data={"status": "OK", "token": "bearer access token"},
            status=status.HTTP_200_OK,
        )


class VerifyToken(APIView):
    permission_classes = (permissions.AllowAny,)

    @swagger_auto_schema(manual_parameters=[
    ], )
    def get(self, request):
        """
            Verify the Access Token
        """
        authorization_header = request.headers.get('Authorization')
        if not authorization_header or not authorization_header.startswith('Bearer '):
            return HttpResponseBadRequest('Invalid Authorization header')
        access_token = authorization_header[len('Bearer '):]
        userinfo = requests.post(
            'https://cilogon.org/oauth2/userinfo',
            data={
                'access_token': access_token,
            },
        )

        if not userinfo.ok:
            return HttpResponseBadRequest('Failed to verify token')

        userinfo_data = userinfo.json()
        print(f"[GetResourceSchemaorg] userinfo_data={userinfo_data}")

        return Response(
            data={"status": "OK", "userinfo": userinfo_data},
            status=status.HTTP_200_OK,
        )


class GetCode(APIView):
    permission_classes = (permissions.AllowAny,)

    @swagger_auto_schema()
    def get(self, request):
        domain = get_domain_name()
        return Response({
                            "url": "https://cilogon.org/authorize?response_type=code&client_id=cilogon:/client_id/34d8b8c1560547fa1023ceacc000dd96&redirect_uri=https://" + domain + "/accounts/cilogon/login/callback/&scope=openid+profile+email+org.cilogon.userinfo+edu.uiuc.ncsa.myproxy.getcert"})
