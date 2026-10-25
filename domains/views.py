from datetime import date

from django.shortcuts import render

from db.queries import fetch_all, fetch_one


def domains(request):
    context = {
        "domains": fetch_all(
            "domain_list", {"today": date.today().isoformat()}
        ),
    }
    return render(request, "domains/domain_list.html", context)


def domain_detail(request, domain_id):
    params = {"id": domain_id, "today": date.today().isoformat()}
    domain = fetch_one("domain_detail", params)
    context = {"domain": domain}
    if domain is not None:
        context["certificates"] = fetch_all("domain_certificates", params)
    return render(
        request,
        "domains/domain_detail.html",
        context,
        status=404 if domain is None else 200,
    )


def unprotected_domains(request):
    """Домены без действующего сертификата на дату из параметра ?date=."""
    check_date = request.GET.get("date", "")
    error = ""
    domains_list = []
    if check_date:
        try:
            date.fromisoformat(check_date)
        except ValueError:
            error = "Укажите дату в формате ГГГГ-ММ-ДД"
        else:
            domains_list = fetch_all(
                "unprotected_domains", {"date": check_date}
            )
    context = {
        "check_date": check_date,
        "error": error,
        "domains": domains_list,
    }
    return render(request, "domains/unprotected.html", context)
