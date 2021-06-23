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
    about_commander,
    dashboard,
    game_journal,
    game_journal_upload,
    initial_setup,
    activities_report,
    chart_js_generator,
)
from .chart_views import CommanderDashboardLineChart, CommanderDashboardPieChart
from .ajax_datatables import AjaxJournalLog

app_name = "commander"

urlpatterns = [
    path(
        "datatable/report/commander/<slug:report>/",
        activities_report,
        name="ajax_activities_report",
    ),
    path("activities_report/", activities_report, name="activities_report"),
    path(
        "chart/line/<slug:report_id>/",
        CommanderDashboardLineChart.as_view(),
        name="commander_line_chart",
    ),
    path(
        "chart/pie/<slug:report_id>/",
        CommanderDashboardPieChart.as_view(),
        name="commander_pie_chart",
    ),
    path(
        "chart/js/<slug:report_id>/chart.js",
        chart_js_generator,
        name="chart_js_generator",
    ),
    path("dashboard/", dashboard, name="dashboard"),
    path("datatable/journal_log", AjaxJournalLog.as_view(), name="ajax_journal_log"),
    path("fleet_carrier/", cmdr_fleet_carrier, name="fleet_carrier"),
    path("game_journal/", game_journal, name="game_journal"),
    path("game_journal/upload/", game_journal_upload, name="game_journal_upload"),
    path("initial_setup/", initial_setup, name="initial_setup"),
    path("profile/", about_commander, name="profile"),
    path("sync_fleet_carrier/", sync_fleet_carrier, name="sync_fleet_carrier"),
]
