"""Проверка маршрутов и страниц Django-приложения."""
import os

import django
import pytest

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "certhub.settings")
django.setup()

from django.test import Client, override_settings  # noqa: E402


@pytest.fixture
def client() -> Client:
    return Client(HTTP_HOST="localhost")


@pytest.mark.parametrize("url", [
    "/",
    "/domains/",
    "/domains/1/",
    "/certificates/",
    "/certificates/1/",
])
def test_pages_open(client, url):
    assert client.get(url).status_code == 200


@pytest.mark.parametrize("url, text", [
    ("/domains/999/", "Домен не найден"),
    ("/certificates/999/", "Сертификат не найден"),
])
def test_missing_objects_return_404(client, url, text):
    response = client.get(url)
    assert response.status_code == 404
    assert text in response.content.decode()


def test_domain_page_shows_owner_and_certificates(client):
    content = client.get("/domains/3/").content.decode()
    assert "api.techno.com" in content
    assert "АО «Техно»" in content
    assert "CH-000003" in content
    assert "CH-000004" in content


def test_certificate_page_shows_linked_objects(client):
    content = client.get("/certificates/1/").content.decode()
    assert "CH-000001" in content
    assert "example.ru" in content
    assert "7701234567" in content


def test_custom_404_page(client):
    with override_settings(DEBUG=False):
        response = client.get("/nonexistent/")
    assert response.status_code == 404
    assert "страница не найдена" in response.content.decode()
