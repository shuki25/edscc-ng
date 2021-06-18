import logging

from chartjs.views.lines import BaseLineChartView
from django.db.models import Count, Sum
from django.http import Http404
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.cache import cache_page

from .models import EarningHistory
from ..core.models import EarningType
from ..core.decorators import cached

log = logging.getLogger(__name__)


class DashboardReports:
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
            "chart_url": "commander:commander_chart",
            "chart_id": "cmdr_daily_earning",
            "report_id": "daily_earning",
            "frequency": "daily",
            "label": "earned_on",
            "callable": earning_history,
        },
        "bounties": {
            "title": _("Bounties Collected"),
            "icon": "fas fa-bullseye",
            "chart_url": "commander:commander_chart",
            "chart_id": "cmdr_bounties_collected",
            "report_id": "bounties",
            "frequency": "daily",
            "label": "earned_on",
            "callable": bounties_collected,
        },
        "exploration_data": {
            "title": _("Exploration Data Sold"),
            "icon": "fas fa-globe-americas",
            "chart_url": "commander:commander_chart",
            "chart_id": "cmdr_exploration_data",
            "report_id": "exploration_data",
            "frequency": "daily",
            "label": "earned_on",
            "callable": exploration_data_sold,
        },
        "trade_profit": {
            "title": _("Trade Profit"),
            "icon": "fas fa-funnel-dollar",
            "chart_url": "commander:commander_chart",
            "chart_id": "cmdr_trade_profit",
            "report_id": "trade_profit",
            "frequency": "daily",
            "label": "earned_on",
            "callable": trade_profit,
        },
        "mission_rewards": {
            "title": _("Mission Rewards Collected"),
            "icon": "fas fa-tasks",
            "chart_url": "commander:commander_chart",
            "chart_id": "cmdr_mission_rewards",
            "report_id": "mission_rewards",
            "frequency": "daily",
            "label": "earned_on",
            "callable": mission_rewards,
        },
    }


@method_decorator(cached(name="dashboard", timeout=300, request=True), name="dispatch")
class CommanderDashboard(BaseLineChartView, DashboardReports):
    chart_id = None
    labels = []
    dataset = [_("Commander"), _("Crew Wage")]
    data = {}
    report = {}

    def setup(self, request, *args, **kwargs):
        super().setup(request, args, kwargs)
        log.debug("kwargs=%s, user_id=%s" % (kwargs, self.request.user.id))
        if "report_id" in kwargs:
            log.debug("kwargs=%s" % kwargs)
            self.report = self.get_report(kwargs["report_id"])
            log.debug("report=%s" % self.report)
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

    def get_dataset_options(self, index, color):
        options = super().get_dataset_options(index, color)
        options["fill"] = False
        return options
