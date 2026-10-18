from datetime import date

from django.conf import settings
from django.shortcuts import render

from certificates.views import make_certificate_row
from models.certificates import (
    get_current_certificate,
    get_domain_certificates,
    sort_certificates_by_expiry,
)
from models.domains import find_domain_by_id, sort_domains
from storage import load_data


def make_domain_row(domain, certificates, today):
    """Подготовить домен и его текущий сертификат для шаблона."""
    current = get_current_certificate(certificates, domain, today)
    return {
        "domain": domain,
        "row": make_certificate_row(current, today) if current else None,
        "is_protected": current is not None and current.is_valid_on(today),
    }


def domains(request):
    _, domains_list, certificates_list = load_data(settings.DATA_DIR)
    today = date.today()
    context = {
        "domain_rows": [
            make_domain_row(domain, certificates_list, today)
            for domain in sort_domains(domains_list)
        ],
    }
    return render(request, "domains/domain_list.html", context)


def domain_detail(request, domain_id):
    _, domains_list, certificates_list = load_data(settings.DATA_DIR)
    domain = find_domain_by_id(domains_list, domain_id)
    context = {"domain": domain}
    if domain is not None:
        today = date.today()
        history = sort_certificates_by_expiry(
            get_domain_certificates(certificates_list, domain)
        )
        context["item"] = make_domain_row(domain, certificates_list, today)
        context["history"] = [
            make_certificate_row(certificate, today)
            for certificate in history
        ]
    return render(
        request,
        "domains/domain_detail.html",
        context,
        status=404 if domain is None else 200,
    )
