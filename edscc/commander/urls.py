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

from .views import about_commander, game_journal, game_journal_upload, initial_setup

urlpatterns = [
    path("profile/", about_commander, name="profile"),
    path("fleet_carrier", cmdr_fleet_carrier, name="fleet_carrier"),
    path("sync_fleet_carrier", sync_fleet_carrier, name="sync_fleet_carrier"),
    path("initial_setup/", initial_setup, name="initial_setup"),
    path("game_journal/", game_journal, name="game_journal"),
    path("game_journal/upload/", game_journal_upload, name="game_journal_upload"),
]
