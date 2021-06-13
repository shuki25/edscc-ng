"""commander URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path

from edscc.core.views import placeholder, cmdr_fleet_carrier, sync_fleet_carrier

from .views import (
    join_squadron,
    setup_squadron,
    finish_activate_squadron,
    settings,
    roster,
)

from .ajax_datatables import AjaxMemberRoster

app_name = "squadron"

urlpatterns = [
    path("join_squadron/", join_squadron, name="join_squadron"),
    path("setup_squadron/", setup_squadron, name="setup_squadron"),
    path(
        "finish_activate_squadron/",
        finish_activate_squadron,
        name="finish_activate_squadron",
    ),
    path("settings/", settings, name="settings"),
    path("roster/", roster, name="roster"),
    path("datatable/roster/", AjaxMemberRoster.as_view(), name="roster_datatable"),
]
