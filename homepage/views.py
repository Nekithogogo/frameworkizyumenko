from datetime import date

from django.conf import settings
from django.http import HttpResponse
from django.utils.html import escape

from models.certificates import STATUSES, get_expiring_certificates
from storage import load_data


def page(title, content):
    """Собрать HTML-документ с общим каркасом всех страниц проекта."""
    bootstrap = (
        "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3"
        "/dist/css/bootstrap.min.css"
    )
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{title}</title>
    <link rel="stylesheet" href="{bootstrap}">
</head>
<body>
    <nav class="nav bg-dark mb-4 px-3">
        <a class="nav-link text-white fw-bold" href="/">CertHub</a>
        <a class="nav-link text-white-50" href="/domains/">Домены</a>
        <a class="nav-link text-white-50" href="/certificates/">Сертификаты</a>
    </nav>
    <main class="container">{content}</main>
</body>
</html>"""


def index(request):
    organizations, domains, certificates = load_data(settings.DATA_DIR)
    today = date.today()
    counts = ""
    for code, title in STATUSES.items():
        number = sum(1 for c in certificates if c.get_status(today) == code)
        counts += f'<li class="list-group-item">{title}: {number}</li>'
    expiring = ""
    for certificate in get_expiring_certificates(certificates, today):
        expiring += f"""
        <li class="list-group-item">
            <a href="/certificates/{certificate.id}/">
                {escape(certificate.domain.name)}
            </a>
            — осталось дней: {certificate.days_left(today)}
        </li>
        """
    if not expiring:
        expiring = '<li class="list-group-item">Таких сертификатов нет</li>'
    content = f"""
    <h1 class="display-5">CertHub</h1>
    <p class="lead">Сервис управления SSL-сертификатами.</p>
    <p>
        Учет организаций, их доменов и SSL-сертификатов
        с контролем сроков действия.
    </p>
    <p>
        Организаций: {len(organizations)}, доменов: {len(domains)},
        сертификатов: {len(certificates)}.
    </p>
    <div class="row g-3 mb-4">
        <div class="col-md-6">
            <h2 class="h5">Сертификаты по статусам</h2>
            <ul class="list-group">{counts}</ul>
        </div>
        <div class="col-md-6">
            <h2 class="h5">Требуют продления</h2>
            <ul class="list-group">{expiring}</ul>
        </div>
    </div>
    <p>Основные разделы:</p>
    <a href="/domains/" class="btn btn-primary me-2">Домены</a>
    <a href="/certificates/" class="btn btn-secondary">Сертификаты</a>
    """
    return HttpResponse(page("CertHub", content))


def page_not_found(request, exception):
    content = """
    <h1 class="text-danger">404 – страница не найдена</h1>
    <p>Проверьте адрес или вернитесь на главную.</p>
    <a href="/" class="btn btn-primary">На главную</a>
    """
    return HttpResponse(
        page("404 – страница не найдена", content),
        status=404,
    )
