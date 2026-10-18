"""Корневая маршрутизация проекта CertHub."""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("homepage.urls")),
    path("domains/", include("domains.urls")),
    path("certificates/", include("certificates.urls")),
]

handler404 = "homepage.views.page_not_found"
