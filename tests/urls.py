"""
URL configuration for django-flex-menus tests.
"""

from django.contrib import admin
from django.http import HttpResponse
from django.urls import path


def dummy_view(request, *args, **kwargs):
    return HttpResponse("ok")


urlpatterns = [
    path("admin/", admin.site.urls),
    path("products/<int:pk>/", dummy_view, name="product-detail"),
]
