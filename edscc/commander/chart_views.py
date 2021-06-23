import logging

from django.db.models import Count, Sum
from django.http import Http404
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _

from ..core.chart_js import ChartLineView, ChartPieView
from ..core.decorators import cached
from ..core.models import EarningType
from .models import ActivityCounter, Crime, EarningHistory

log = logging.getLogger(__name__)


class DashboardLineReports:
    def __init__(self):
        for key, values in self.chart_config.items():
            self.chart_config[key]["js"] = "line_chart_tpl.js"

    def get_report(self, key):
        if key in self.chart_config:
            return self.chart_config[key]
        else:
            return None

    def all_reports(self):
        return self.chart_config

    def earning_history(self, user_id, action="setup", data=None):
        if action == "setup":
            rs = (
                EarningHistory.objects.filter(user_id=user_id)
                .order_by("earned_on")
                .values("earned_on")
                .annotate(total_reward=Sum("reward"), crew_total=Sum("crew_wage"))
            )
            return rs
        if action == "data":
            commander = [value["total_reward"] for value in data]
            crew = [value["crew_total"] for value in data]
            # log.debug("data=%s" % data)
            return [commander, crew]
        return None

    def bounties_collected(self, user_id, action="setup", data=None):
        if action == "setup":
            et = EarningType.objects.filter(name="Bounty").values_list("id", flat=True)
            rs = (
                EarningHistory.objects.filter(user_id=user_id, earning_type_id__in=et)
                .order_by("earned_on")
                .values("earned_on")
                .annotate(total_reward=Sum("reward"), crew_total=Sum("crew_wage"))
            )
            return rs
        if action == "data":
            commander = [value["total_reward"] for value in data]
            crew = [value["crew_total"] for value in data]
            # log.debug("data=%s" % data)
            return [commander, crew]
        return None

    def exploration_data_sold(self, user_id, action="setup", data=None):
        if action == "setup":
            et = EarningType.objects.filter(name="ExplorationData").values_list(
                "id", flat=True
            )
            rs = (
                EarningHistory.objects.filter(user_id=user_id, earning_type_id__in=et)
                .order_by("earned_on")
                .values("earned_on")
                .annotate(total_reward=Sum("reward"), crew_total=Sum("crew_wage"))
            )
            return rs
        if action == "data":
            commander = [value["total_reward"] for value in data]
            crew = [value["crew_total"] for value in data]
            # log.debug("data=%s" % data)
            return [commander, crew]
        return None

    def trade_profit(self, user_id, action="setup", data=None):
        if action == "setup":
            groups = ["MarketBuy", "MarketSell"]
            et = EarningType.objects.filter(name__in=groups).values_list(
                "id", flat=True
            )
            rs = (
                EarningHistory.objects.filter(user_id=user_id, earning_type_id__in=et)
                .order_by("earned_on")
                .values("earned_on")
                .annotate(total_reward=Sum("reward"), crew_total=Sum("crew_wage"))
            )
            return rs
        if action == "data":
            commander = [value["total_reward"] for value in data]
            crew = [value["crew_total"] for value in data]
            # log.debug("data=%s" % data)
            return [commander, crew]
        return None

    def mission_rewards(self, user_id, action="setup", data=None):
        if action == "setup":
            et = EarningType.objects.filter(mission_flag=True).values_list(
                "id", flat=True
            )
            rs = (
                EarningHistory.objects.filter(user_id=user_id, earning_type_id__in=et)
                .order_by("earned_on")
                .values("earned_on")
                .annotate(total_reward=Sum("reward"), crew_total=Sum("crew_wage"))
            )
            return rs
        if action == "data":
            commander = [value["total_reward"] for value in data]
            crew = [value["crew_total"] for value in data]
            # log.debug("data=%s" % data)
            return [commander, crew]
        return None

    chart_config = {
        "daily_earning": {
            "title": _("Daily Earning"),
            "icon": "fas fa-money-bill-alt",
            "chart_url": "commander:commander_line_chart",
            "chart_id": "cmdr_daily_earning",
            "report_id": "daily_earning",
            "frequency": "daily",
            "type": "line",
            "label": "earned_on",
            "callable": earning_history,
        },
        "bounties": {
            "title": _("Bounties Collected"),
            "icon": "fas fa-bullseye",
            "chart_url": "commander:commander_line_chart",
            "chart_id": "cmdr_bounties_collected",
            "report_id": "bounties",
            "frequency": "daily",
            "type": "line",
            "label": "earned_on",
            "callable": bounties_collected,
        },
        "exploration_data": {
            "title": _("Exploration Data Sold"),
            "icon": "fas fa-globe-americas",
            "chart_url": "commander:commander_line_chart",
            "chart_id": "cmdr_exploration_data",
            "report_id": "exploration_data",
            "frequency": "daily",
            "type": "line",
            "label": "earned_on",
            "callable": exploration_data_sold,
        },
        "trade_profit": {
            "title": _("Trade Profit"),
            "icon": "fas fa-funnel-dollar",
            "chart_url": "commander:commander_line_chart",
            "chart_id": "cmdr_trade_profit",
            "report_id": "trade_profit",
            "frequency": "daily",
            "type": "line",
            "label": "earned_on",
            "callable": trade_profit,
        },
        "mission_rewards": {
            "title": _("Mission Rewards Collected"),
            "icon": "fas fa-tasks",
            "chart_url": "commander:commander_line_chart",
            "chart_id": "cmdr_mission_rewards",
            "report_id": "mission_rewards",
            "frequency": "daily",
            "type": "line",
            "label": "earned_on",
            "callable": mission_rewards,
        },
    }


@method_decorator(
    cached(name="line_dashboard", timeout=300, request=True), name="dispatch"
)
class CommanderDashboardLineChart(ChartLineView, DashboardLineReports):
    chart_id = None
    labels = []
    dataset = [_("Commander"), _("Crew Wage")]
    data = {}
    report = {}

    def setup(self, request, *args, **kwargs):
        super().setup(request, args, kwargs)
        # log.debug("kwargs=%s, user_id=%s" % (kwargs, self.request.user.id))
        if "report_id" in kwargs:
            # log.debug("kwargs=%s" % kwargs)
            self.report = self.get_report(kwargs["report_id"])
            # log.debug("report=%s" % self.report)
            if not self.report:
                raise Http404
            self.data = self.report["callable"](self, self.request.user.id)
        else:
            raise Http404

    def get_labels(self):
        key = self.report["label"]
        labels = [label[key] for label in self.data]
        # log.debug("labels=%s" % labels)
        return labels

    def get_providers(self):
        return self.dataset

    def get_data(self):
        return self.report["callable"](
            self, self.request.user.id, action="data", data=self.data
        )

    def get_dataset_options(self, **kwargs):
        options = super(CommanderDashboardLineChart, self).get_dataset_options(**kwargs)
        options.update({"fill": False})
        return options


class DashboardPieReports:
    def __init__(self):
        for key, values in self.chart_config.items():
            self.chart_config[key]["js"] = "pie_chart_tpl.js"

    def get_report(self, key):
        if key in self.chart_config:
            return self.chart_config[key]
        else:
            return None

    def all_reports(self):
        return self.chart_config

    def activity_pie(self, user_id, action="setup", data=None):
        if action == "setup":
            ac = ActivityCounter.objects.filter(user_id=user_id)
            trimmed_rs = {}
            rs = {
                "Blackmarket": sum(ac.values_list("black_market", flat=True)),
                "Bounty": sum(ac.values_list("bounties_claimed", flat=True)),
                "Donation": sum(ac.values_list("donations", flat=True)),
                "Exploration": sum(ac.values_list("systems_scanned", flat=True)),
                "Market": sum(ac.values_list("market_buy", flat=True))
                + sum(ac.values_list("market_sell", flat=True)),
                "Missions": sum(ac.values_list("missions_completed", flat=True)),
                "Mining": sum(ac.values_list("mining_refined", flat=True)),
            }
            for key, value in rs.items():
                if value:
                    trimmed_rs[key] = value
            # log.debug("data=%s" % trimmed_rs)
            return trimmed_rs
        if action == "data":
            return [value for key, value in data.items()]
        if action == "label":
            # log.debug("label=%s" % data)
            return [key for key, value in data.items()]
        return None

    def earning_pie(self, user_id, action="setup", data=None):
        if action == "setup":
            rs = (
                EarningHistory.objects.filter(user_id=user_id)
                .order_by("earning_type__category")
                .values("earning_type__category")
                .annotate(total_earned=Sum("reward"))
            )
            return rs
        if action == "data":
            return [value["total_earned"] for value in data]
        if action == "label":
            return [value["earning_type__category"] for value in data]
        return None

    def crimes(self, user_id, action="setup", data=None):
        if action == "setup":
            rs = (
                Crime.objects.filter(user_id=user_id)
                .order_by("crime_type__category")
                .values("crime_type__category")
                .annotate(count=Count("crime_type__category"))
            )
            # log.debug("data=%s" % rs)
            return rs
        if action == "data":
            return [value["count"] for value in data]
        if action == "label":
            return [value["crime_type__category"] for value in data]
        return None

    def fines_paid(self, user_id, action="setup", data=None):
        if action == "setup":
            rs = (
                Crime.objects.filter(user_id=user_id)
                .order_by("crime_type__category")
                .values("crime_type__category")
                .annotate(fines_paid=Sum("fine"))
            )
            # log.debug("data=%s" % rs)
            return rs
        if action == "data":
            return [value["fines_paid"] for value in data]
        if action == "label":
            return [value["crime_type__category"] for value in data]
        return None

    def bounties_paid(self, user_id, action="setup", data=None):
        if action == "setup":
            rs = (
                Crime.objects.filter(user_id=user_id)
                .order_by("crime_type__category")
                .values("crime_type__category")
                .annotate(bounties_paid=Sum("bounty"))
            )
            # log.debug("data=%s" % rs)
            return rs
        if action == "data":
            return [value["bounties_paid"] for value in data]
        if action == "label":
            return [value["crime_type__category"] for value in data]
        return None

    chart_config = {
        "earning_pie": {
            "title": _("Earning Distribution"),
            "icon": "fas fa-chart-pie",
            "chart_url": "commander:commander_pie_chart",
            "chart_id": "cmdr_earning_pie",
            "report_id": "earning_pie",
            "frequency": "daily",
            "type": "doughnut",
            "callable": earning_pie,
        },
        "crimes": {
            "title": _("Crimes Committed"),
            "icon": "fas fa-balance-scale",
            "chart_url": "commander:commander_pie_chart",
            "chart_id": "cmdr_crimes",
            "report_id": "crimes",
            "frequency": "daily",
            "type": "doughnut",
            "callable": crimes,
        },
        "fines_paid": {
            "title": _("Fines Paid"),
            "icon": "fas fa-balance-scale",
            "chart_url": "commander:commander_pie_chart",
            "chart_id": "cmdr_fines_paid",
            "report_id": "fines_paid",
            "frequency": "daily",
            "type": "doughnut",
            "callable": fines_paid,
        },
        "bounties_paid": {
            "title": _("Bounties Paid"),
            "icon": "fas fa-balance-scale",
            "chart_url": "commander:commander_pie_chart",
            "chart_id": "cmdr_bounties_paid",
            "report_id": "bounties_paid",
            "frequency": "daily",
            "type": "doughnut",
            "callable": bounties_paid,
        },
    }


@method_decorator(
    cached(name="pie_dashboard", timeout=300, request=True), name="dispatch"
)
class CommanderDashboardPieChart(ChartPieView, DashboardPieReports):
    chart_id = None
    data = {}
    report = {}

    def setup(self, request, *args, **kwargs):
        super().setup(request, args, kwargs)
        # log.debug("kwargs=%s, user_id=%s" % (kwargs, self.request.user.id))
        if "report_id" in kwargs:
            # log.debug("kwargs=%s" % kwargs)
            self.report = self.get_report(kwargs["report_id"])
            # log.debug("report=%s" % self.report)
            if not self.report:
                raise Http404
            self.data = self.report["callable"](self, self.request.user.id)
        else:
            raise Http404

    def get_dataset_options(self, **kwargs):
        options = super(CommanderDashboardPieChart, self).get_dataset_options(**kwargs)
        options.update(
            {
                "borderColor": "#000",
                "borderWidth": 1,
            }
        )
        return options

    def get_labels(self):
        return self.report["callable"](
            self, self.request.user.id, action="label", data=self.data
        )

    def get_data(self):
        return self.report["callable"](
            self, self.request.user.id, action="data", data=self.data
        )
