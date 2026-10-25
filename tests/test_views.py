"""Проверка маршрутов и страниц Django-приложения."""
import os

import django
import pytest

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "certhub.settings")
django.setup()

from django.test import Client, override_settings  # noqa: E402


pytestmark = pytest.mark.usefixtures("sqlite_db")


@pytest.fixture
def client() -> Client:
    return Client(HTTP_HOST="localhost")


@pytest.mark.parametrize("url", [
    "/",
    "/domains/",
    "/domains/1/",
    "/certificates/",
    "/certificates/1/",
    "/domains/unprotected/",
    "/domains/unprotected/?date=2026-10-25",
    "/certificates/expiring/",
    "/certificates/expiring/?days=abc",
    "/certificates/statistics/",
    "/certificates/statistics/?min_domains=3",
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


def test_pages_use_base_template_and_static(client):
    content = client.get("/certificates/").content.decode()
    assert "/static/homepage/css/style.css" in content
    assert "/static/homepage/img/logo.png" in content
    assert "/static/homepage/js/main.js" in content
    assert 'href="/domains/"' in content


def test_home_page_shows_status_summary(client):
    content = client.get("/").content.decode()
    assert "Сертификаты по статусам" in content
    assert "Требуют продления" in content


def test_unprotected_domains_page_uses_date_parameter(client):
    content = client.get("/domains/unprotected/?date=2026-10-25").content
    content = content.decode()
    assert "mail.techno.com" in content
    assert "ivanov-blog.ru" in content
    assert "shop.example.ru" not in content


def test_unprotected_domains_page_rejects_bad_date(client):
    content = client.get("/domains/unprotected/?date=31.12").content.decode()
    assert "Укажите дату" in content


def test_statistics_page_shows_aggregates(client):
    content = client.get("/certificates/statistics/").content.decode()
    assert "По типам сертификатов" in content
    assert "АО «Техно»" in content
    assert "7812345678" in content


def test_pages_show_data_from_sqlite(client, sqlite_db):
    import sqlite3

    conn = sqlite3.connect(sqlite_db)
    conn.execute("UPDATE domains SET name = ? WHERE id = ?",
                 ("renamed.example.ru", 1))
    conn.commit()
    conn.close()
    content = client.get("/domains/").content.decode()
    assert "renamed.example.ru" in content
