from django.urls import path

from . import views

app_name = "certificates"

urlpatterns = [
    path("", views.certificates, name="list"),
    path("<int:certificate_id>/", views.certificate_detail, name="detail"),
]
