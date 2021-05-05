from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views import defaults as default_views
from django.views.generic import TemplateView
from rest_framework.authtoken.views import obtain_auth_token

from edscc.core.views import (
    galnet_news,
    galnet_news_detail,
    home_page,
    login_required_alert,
    placeholder,
    privacy_policy,
    sync_galnet_news,
)

urlpatterns = [
    path(
        "about/", TemplateView.as_view(template_name="pages/about.html"), name="about"
    ),
    # Django Admin, use {% url 'admin:index' %}
    path('admin/sync/galnet_news/', sync_galnet_news, name="sync-galnet-news"),
    path(settings.ADMIN_URL, admin.site.urls),
    # User management
    path("accounts/", include("allauth.urls")),
    # Your stuff: custom urls includes go here
    path("", home_page, name="home"),
    path("i18n/", include("django.conf.urls.i18n")),
    path("galnet/", galnet_news, name="galnet"),
    path("galnet/<slug:slug>", galnet_news_detail, name="galnet-detail"),
    path("blog/", placeholder, name="blog"),
    path("github/", placeholder, name="github"),
    path("patreon/", placeholder, name="patreon"),
    path("discord/", placeholder, name="discord"),
    path("placeholder/", placeholder, name="placeholder"),
    path("privacy_policy/", privacy_policy, name="privacy-policy"),
    path("commander/", include("edscc.commander.urls")),
    path("login_required/", login_required_alert, name="login-required"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# API URLS
urlpatterns += [
    # API base url
    path("api/", include("edscc.api.urls")),
    # DRF auth token
    path("auth-token/", obtain_auth_token),
]

if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        path(
            "400/",
            default_views.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        path(
            "403/",
            default_views.permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "404/",
            default_views.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path("500/", default_views.server_error),
    ]
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
