from datetime import date

from django.conf import settings
from django.http import HttpResponse
from django.utils.html import escape

from certificates.views import status_badge
from homepage.views import page
from models.certificates import (
    get_current_certificate,
    get_domain_certificates,
    sort_certificates_by_expiry,
)
from models.domains import find_domain_by_id, sort_domains
from storage import load_data


def domains(request):
    _, domains_list, certificates_list = load_data(settings.DATA_DIR)
    today = date.today()
    items = ""
    for domain in sort_domains(domains_list):
        current = get_current_certificate(certificates_list, domain, today)
        if current is None:
            status = '<span class="badge bg-secondary">нет сертификата</span>'
        else:
            status = status_badge(current, today)
        items += f"""
        <a href="/domains/{domain.id}/"
           class="list-group-item list-group-item-action
                  d-flex justify-content-between align-items-center">
            <span>
                <strong>{escape(domain.name)}</strong>
                <small class="text-muted">
                    {escape(domain.organization.name)}
                </small>
            </span>
            {status}
        </a>
        """
    content = f"""
    <h1>Домены</h1>
    <div class="list-group">{items}</div>
    """
    return HttpResponse(page("CertHub – домены", content))


def domain_detail(request, domain_id):
    _, domains_list, certificates_list = load_data(settings.DATA_DIR)
    domain = find_domain_by_id(domains_list, domain_id)
    if domain is None:
        content = """
        <h1 class="text-danger">Домен не найден</h1>
        <a href="/domains/" class="btn btn-outline-secondary">
            ← к списку доменов
        </a>
        """
        return HttpResponse(page("Домен не найден", content), status=404)

    today = date.today()
    current = get_current_certificate(certificates_list, domain, today)
    if current is not None and current.is_valid_on(today):
        protection = (f'<span class="badge bg-success">защищен до '
                      f"{current.validity.valid_to.strftime('%d.%m.%Y')}"
                      "</span>")
    else:
        protection = '<span class="badge bg-danger">не защищен</span>'
    rows = ""
    history = sort_certificates_by_expiry(
        get_domain_certificates(certificates_list, domain)
    )
    for certificate in history:
        rows += f"""
        <li class="list-group-item d-flex justify-content-between">
            <a href="/certificates/{certificate.id}/">
                {escape(certificate.serial_number)}
                ({certificate.cert_type}), {certificate.validity}
            </a>
            {status_badge(certificate, today)}
        </li>
        """
    if not rows:
        rows = '<li class="list-group-item">Сертификаты не выпускались</li>'
    organization = domain.organization
    content = f"""
    <div class="card mb-3">
        <div class="card-body">
            <h1 class="card-title h3">{escape(domain.name)}</h1>
            <p class="card-text"><strong>ID:</strong> {domain.id}</p>
            <p class="card-text"><strong>Зона:</strong> .{domain.zone}</p>
            <p class="card-text">
                <strong>Владелец:</strong> {escape(str(organization))},
                {escape(organization.email)}
            </p>
            <p class="card-text">
                <strong>Защита на сегодня:</strong> {protection}
            </p>
        </div>
    </div>
    <h2 class="h4">Сертификаты домена</h2>
    <ul class="list-group mb-3">{rows}</ul>
    <a href="/domains/" class="btn btn-outline-secondary">
        ← к списку доменов
    </a>
    """
    return HttpResponse(page(escape(domain.name), content), status=200)
