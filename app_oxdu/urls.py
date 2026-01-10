from core.mixins import OpenView

from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include
from django.urls import path
from django.utils.translation import gettext_lazy as _


module_urls = i18n_patterns(
    path("", include("core.urls", namespace="core")),
    path("", include("user_sessions.urls", "user_sessions")),
    path("admin/doc/", include("django.contrib.admindocs.urls")),
    path("admin/", admin.site.urls),
    path("accounts/", include("registration.backends.simple.urls")),
    # path("login/", CustomLoginView.as_view(), name="auth_login"),
    path("accounts/", include("accounts.urls", namespace="accounts")),
    path("accounting/", include("accounting.urls", namespace="accounting")),
    path("transactions/", include("transactions.urls", namespace="transactions")),
    path("employees/", include("employees.urls", namespace="employees")),
    path("admission/", include("admission.urls", namespace="admission")),
    path("branches/", include("branches.urls", namespace="branches")),
    path("masters/", include("masters.urls", namespace="masters")),
    prefix_default_language=False,
)

plugin_urls = [
    path("tinymce/", include("tinymce.urls")),
    path("i18n/", include("django.conf.urls.i18n")),
    path("sitemap.xml", OpenView.as_view(template_name="sitemap.xml", content_type="text/xml")),
    path("robots.txt", OpenView.as_view(template_name="robots.txt", content_type="text/plain")),
    path("OneSignalSDKWorker.js", OpenView.as_view(template_name="OneSignalSDKWorker.js", content_type="text/javascript")),
]

urlpatterns = module_urls + plugin_urls + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

PROJECT_NAME = settings.APP_SETTINGS.get("site_name")
admin.site.site_header = _("%(project_name)s Administration") % {"project_name": PROJECT_NAME}
admin.site.site_title = _("%(project_name)s Admin Portal") % {"project_name": PROJECT_NAME}
admin.site.index_title = _("Welcome to %(project_name)s Admin Portal") % {"project_name": PROJECT_NAME}
