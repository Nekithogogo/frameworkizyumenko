from django.urls import path

from . import views

app_name = "domains"

urlpatterns = [
    path("", views.domains, name="list"),
    path("<int:domain_id>/", views.domain_detail, name="detail"),
]
