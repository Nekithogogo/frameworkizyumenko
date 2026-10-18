from datetime import date

from django.conf import settings
from django.http import HttpResponse
from django.utils.html import escape

from homepage.views import page
from models.certificates import (
    CERTIFICATE_TYPES,
    find_certificate_by_id,
    sort_certificates_by_expiry,
)
from storage import load_data

BADGES = {
    "pending": "bg-info",
    "active": "bg-success",
    "expiring": "bg-warning text-dark",
    "expired": "bg-danger",
    "revoked": "bg-secondary",
}


def status_badge(certificate, today):
    """Сформировать HTML бейджа статуса сертификата."""
    css = BADGES[certificate.get_status(today)]
    title = certificate.get_status_title(today)
    return f'<span class="badge {css}">{title}</span>'


def certificates(request):
    _, _, certificates_list = load_data(settings.DATA_DIR)
    today = date.today()
    rows = ""
    for certificate in sort_certificates_by_expiry(certificates_list):
        rows += f"""
        <tr>
            <td>
                <a href="/certificates/{certificate.id}/">
                    {escape(certificate.serial_number)}
                </a>
            </td>
            <td>{certificate.cert_type}</td>
            <td>
                <a href="/domains/{certificate.domain.id}/">
                    {escape(certificate.domain.name)}
                </a>
            </td>
            <td>{escape(certificate.organization.name)}</td>
            <td>{certificate.validity}</td>
            <td>{status_badge(certificate, today)}</td>
        </tr>
        """
    content = f"""
    <h1>Сертификаты</h1>
    <div class="table-responsive">
        <table class="table table-hover align-middle">
            <thead>
                <tr>
                    <th>Серийный номер</th><th>Тип</th><th>Домен</th>
                    <th>Организация</th><th>Срок действия</th><th>Статус</th>
                </tr>
            </thead>
            <tbody>{rows}</tbody>
        </table>
    </div>
    """
    return HttpResponse(page("CertHub – сертификаты", content))


def certificate_detail(request, certificate_id):
    _, _, certificates_list = load_data(settings.DATA_DIR)
    certificate = find_certificate_by_id(certificates_list, certificate_id)
    if certificate is None:
        content = """
        <h1 class="text-danger">Сертификат не найден</h1>
        <a href="/certificates/" class="btn btn-outline-secondary">
            ← к списку сертификатов
        </a>
        """
        return HttpResponse(
            page("Сертификат не найден", content),
            status=404,
        )

    today = date.today()
    validity = certificate.validity
    organization = certificate.organization
    cert_type = CERTIFICATE_TYPES[certificate.cert_type]
    content = f"""
    <div class="card mb-3">
        <div class="card-body">
            <h1 class="card-title h3">
                Сертификат {escape(certificate.serial_number)}
            </h1>
            <p class="card-text">
                <strong>Тип:</strong> {cert_type}
            </p>
            <p class="card-text">
                <strong>Домен:</strong>
                <a href="/domains/{certificate.domain.id}/">
                    {escape(certificate.domain.name)}
                </a>
            </p>
            <p class="card-text">
                <strong>Организация:</strong> {escape(str(organization))}
            </p>
            <p class="card-text">
                <strong>Срок действия:</strong> {validity}
                ({validity.days_total} дн.)
            </p>
            <p class="card-text">
                <strong>Осталось дней:</strong>
                {max(certificate.days_left(today), 0)}
            </p>
            <p class="card-text">
                <strong>Статус:</strong> {status_badge(certificate, today)}
            </p>
        </div>
    </div>
    <a href="/certificates/" class="btn btn-outline-secondary">
        ← к списку сертификатов
    </a>
    """
    return HttpResponse(
        page(f"Сертификат {escape(certificate.serial_number)}", content),
        status=200,
    )
