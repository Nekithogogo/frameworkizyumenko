from datetime import date

from django.shortcuts import render

from db.queries import fetch_all, fetch_one


def index(request):
    today = date.today().isoformat()
    context = {
        "summary": fetch_one("summary"),
        "status_counts": fetch_all("status_counts", {"today": today}),
        "expiring": fetch_all(
            "expiring_certificates", {"today": today, "days": 30}
        ),
    }
    return render(request, "homepage/index.html", context)


def page_not_found(request, exception):
    return render(request, "homepage/404.html", status=404)
