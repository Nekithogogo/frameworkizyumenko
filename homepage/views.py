from datetime import date

from django.conf import settings
from django.shortcuts import render

from certificates.views import make_certificate_row
from models.certificates import STATUSES, get_expiring_certificates
from storage import load_data


def index(request):
    organizations, domains, certificates = load_data(settings.DATA_DIR)
    today = date.today()
    statuses = [c.get_status(today) for c in certificates]
    context = {
        "organizations": organizations,
        "domains": domains,
        "certificates": certificates,
        "status_counts": [
            {"title": title, "count": statuses.count(code)}
            for code, title in STATUSES.items()
        ],
        "expiring": [
            make_certificate_row(certificate, today)
            for certificate in get_expiring_certificates(certificates, today)
        ],
    }
    return render(request, "homepage/index.html", context)


def page_not_found(request, exception):
    return render(request, "homepage/404.html", status=404)
