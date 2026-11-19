from django.conf import settings
from django.contrib import admin
from django.http import FileResponse, HttpResponse
from django.urls import include, path, re_path
from django.views.decorators.http import require_safe


@require_safe
def angular(request):
    response = FileResponse((settings.ANGULAR_ROOT / "index.html").open("rb"), content_type="text/html")
    response["Cache-Control"] = "no-cache"
    return response


@require_safe
def health(request):
    return HttpResponse("ok", content_type="text/plain")


urlpatterns = [
    path("healthz/", health),
    path("admin/", admin.site.urls),
    path("api/", include("api.urls")),
    path("", angular),
    # Only client routes fall back to index.html. Missing API and media URLs stay 404s.
    re_path(
        r"^(?:login|register|dashboard|"
        r"jobs(?:/[0-9]+(?:/apply)?)?|"
        r"forum(?:/ask|/[0-9]+(?:/edit|/answers/[0-9]+/edit)?)?|"
        r"student/(?:profile|applications)|"
        r"company/(?:profile|jobs(?:/new|/[0-9]+/(?:edit|applicants))?|applications/[0-9]+))/?$",
        angular,
    ),
]
