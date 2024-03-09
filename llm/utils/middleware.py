from django.http import Http404
from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework import status
from llm.models import Organization
from logging import basicConfig, INFO, getLogger

basicConfig(level=INFO)
logger = getLogger()


class CustomMiddleware:
    @staticmethod
    def current_organization(request):
        api_key = request.headers.get("Authorization")
        if not api_key:
            return None

        try:
            return Organization.objects.get(api_key=api_key)
        except Organization.DoesNotExist:
            return None

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.
        logger.info("routing request via the middleware")

        org = CustomMiddleware.current_organization(request)

        if not org:
            return JsonResponse(
                {"error": "Invalid API key"},
                status=status.HTTP_404_NOT_FOUND,
            )

        request.org = org
        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        return response
