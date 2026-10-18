from datetime import date

from django.conf import settings
from django.shortcuts import render

from models.certificates import (
    CERTIFICATE_TYPES,
    find_certificate_by_id,
    sort_certificates_by_expiry,
)
from storage import load_data


def make_certificate_row(certificate, today):
    """Подготовить сертификат и его статус на дату today для шаблона."""
    return {
        "certificate": certificate,
        "status": certificate.get_status(today),
        "status_title": certificate.get_status_title(today),
        "days_left": max(certificate.days_left(today), 0),
    }


def certificates(request):
    _, _, certificates_list = load_data(settings.DATA_DIR)
    today = date.today()
    context = {
        "rows": [
            make_certificate_row(certificate, today)
            for certificate in sort_certificates_by_expiry(certificates_list)
        ],
    }
    return render(request, "certificates/certificate_list.html", context)


def certificate_detail(request, certificate_id):
    _, _, certificates_list = load_data(settings.DATA_DIR)
    certificate = find_certificate_by_id(certificates_list, certificate_id)
    context = {"certificate": certificate}
    if certificate is not None:
        context["row"] = make_certificate_row(certificate, date.today())
        context["cert_type_title"] = CERTIFICATE_TYPES[certificate.cert_type]
    return render(
        request,
        "certificates/certificate_detail.html",
        context,
        status=404 if certificate is None else 200,
    )
