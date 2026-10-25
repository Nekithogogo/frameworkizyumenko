from datetime import date

from django.shortcuts import render

from db.queries import fetch_all, fetch_one
from models.certificates import CERTIFICATE_TYPES
from models.validity import MAX_VALIDITY_DAYS


def get_int_param(request, name, default, min_value, max_value):
    """Прочитать целое число из GET-параметра с проверкой диапазона."""
    try:
        value = int(request.GET.get(name, default))
    except ValueError:
        return default
    return min(max(value, min_value), max_value)


def certificates(request):
    context = {
        "certificates": fetch_all(
            "certificate_list", {"today": date.today().isoformat()}
        ),
    }
    return render(request, "certificates/certificate_list.html", context)


def certificate_detail(request, certificate_id):
    certificate = fetch_one(
        "certificate_detail",
        {"id": certificate_id, "today": date.today().isoformat()},
    )
    context = {"certificate": certificate}
    if certificate is not None:
        context["cert_type_title"] = CERTIFICATE_TYPES[
            certificate["cert_type"]
        ]
    return render(
        request,
        "certificates/certificate_detail.html",
        context,
        status=404 if certificate is None else 200,
    )


def expiring_certificates(request):
    """Сертификаты, истекающие в ближайшие ?days= дней."""
    days = get_int_param(request, "days", 30, 1, MAX_VALIDITY_DAYS)
    context = {
        "days": days,
        "certificates": fetch_all(
            "expiring_certificates",
            {"today": date.today().isoformat(), "days": days},
        ),
    }
    return render(request, "certificates/expiring.html", context)


def statistics(request):
    """Статистика по статусам, типам и организациям."""
    today = date.today().isoformat()
    min_domains = get_int_param(request, "min_domains", 2, 1, 100)
    context = {
        "summary": fetch_one("summary"),
        "status_counts": fetch_all("status_counts", {"today": today}),
        "type_statistics": fetch_all("type_statistics"),
        "organization_statistics": fetch_all(
            "organization_statistics", {"today": today}
        ),
        "min_domains": min_domains,
        "large_organizations": fetch_all(
            "large_organizations", {"min_domains": min_domains}
        ),
    }
    return render(request, "certificates/statistics.html", context)
