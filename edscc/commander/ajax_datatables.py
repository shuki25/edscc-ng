import logging

from ajax_datatable.views import AjaxDatatableView
from django.db.models import Count, Sum
from django.utils.formats import number_format
from django.utils.html import escape
from django.utils.text import camel_case_to_spaces
from django.utils.translation import ugettext as _

from .models import Crime, EarningHistory, FactionActivity, JournalLog

log = logging.getLogger(__name__)


class AjaxEarningHistory(AjaxDatatableView):
    model = EarningHistory
    title = "Earning History"
    initial_order = [["earned_on", "asc"]]
    length_menu = [[15, 25, 50, 100], [15, 25, 50, 100]]
    search_values_separator = "+"
    show_column_filters = False

    column_defs = [
        {"name": "id", "searchable": False, "visible": False},
        {
            "name": "earned_on",
            "title": _("Date"),
            "searchable": False,
            "visible": True,
        },
        {
            "name": "earning_type_id",
            "title": _("Type"),
            "foreign_field": "earning_type__name",
            "searchable": False,
            "visible": True,
        },
        {
            "name": "minor_faction_id",
            "title": _("Paying Minor Faction"),
            "foreign_field": "minor_faction__name",
            "searchable": False,
            "visible": True,
        },
        {
            "name": "reward",
            "title": _("Amount"),
            "searchable": False,
            "visible": True,
        },
        {
            "name": "crew_wage",
            "title": _("Crew Paid"),
            "searchable": False,
            "visible": True,
        },
    ]

    def get_initial_queryset(self, request=None):
        return self.model.objects.filter(user_id=request.user.id)

    def render_column(self, row, column):
        if column in ["reward", "crew_wage"]:
            return escape(
                number_format(getattr(row, column), use_l10n=True, force_grouping=True)
            )
        else:
            return super(AjaxEarningHistory, self).render_column(row, column)


class AjaxEarningHistorySummary(AjaxDatatableView):
    model = EarningHistory
    title = "Earning History Summary"
    initial_order = [["earning_type__name", "asc"]]
    length_menu = [[15, 25, 50, 100], [15, 25, 50, 100]]
    search_values_separator = "+"
    show_column_filters = False

    column_defs = [
        {
            "name": "earning_type__name",
            "title": _("Type"),
            "searchable": False,
            "visible": True,
        },
        {
            "name": "num_events",
            "title": _("Count"),
            "searchable": False,
            "visible": True,
        },
        {
            "name": "total_reward",
            "title": _("Amount"),
            "searchable": False,
            "visible": True,
        },
        {
            "name": "total_crew_wage",
            "title": _("Crew Paid"),
            "searchable": False,
            "visible": True,
        },
    ]

    def get_initial_queryset(self, request=None):
        return (
            EarningHistory.objects.filter(user_id=request.user.id)
            .values("earning_type__name")
            .annotate(
                num_events=Count("earning_type__name"),
                total_reward=Sum("reward"),
                total_crew_wage=Sum("crew_wage"),
            )
        )

    def render_column(self, row, column):
        if column in ["num_events", "total_reward", "total_crew_wage"]:
            log.debug(row, column)
            return escape(
                number_format(row[column], use_l10n=True, force_grouping=True)
            )
        else:
            return row[column]


class AjaxEarningHistorySummaryMinorFaction(AjaxDatatableView):
    model = EarningHistory
    title = "Earning History Summary by Minor Faction"
    initial_order = [["earning_type__name", "asc"]]
    length_menu = [[15, 25, 50, 100], [15, 25, 50, 100]]
    search_values_separator = "+"
    show_column_filters = False

    column_defs = [
        {
            "name": "earning_type__name",
            "title": _("Type"),
            "searchable": False,
            "visible": True,
        },
        {
            "name": "minor_faction__name",
            "title": _("Paying Minor Faction"),
            "searchable": False,
            "visible": True,
        },
        {
            "name": "num_events",
            "title": _("Count"),
            "searchable": False,
            "visible": True,
        },
        {
            "name": "total_reward",
            "title": _("Amount"),
            "searchable": False,
            "visible": True,
        },
        {
            "name": "total_crew_wage",
            "title": _("Crew Paid"),
            "searchable": False,
            "visible": True,
        },
    ]

    def get_initial_queryset(self, request=None):
        return (
            EarningHistory.objects.filter(user_id=request.user.id)
            .values("earning_type__name", "minor_faction__name")
            .annotate(
                num_events=Count("earning_type__name"),
                total_reward=Sum("reward"),
                total_crew_wage=Sum("crew_wage"),
            )
        )

    def render_column(self, row, column):
        if column in ["num_events", "total_reward", "total_crew_wage"]:
            log.debug(row, column)
            return escape(
                number_format(row[column], use_l10n=True, force_grouping=True)
            )
        else:
            return row[column]


class AjaxMinorFactionActivitiesSummary(AjaxDatatableView):
    model = FactionActivity
    title = "Minor Faction Activities Summary"
    initial_order = [["earning_type__name", "asc"]]
    length_menu = [[15, 25, 50, 100], [15, 25, 50, 100]]
    search_values_separator = "+"
    show_column_filters = False

    column_defs = [
        {
            "name": "earning_type__name",
            "title": _("Type"),
            "searchable": False,
            "visible": True,
        },
        {
            "name": "minor_faction__name",
            "title": _("Paying Minor Faction"),
            "searchable": False,
            "visible": True,
        },
        {
            "name": "target_minor_faction__name",
            "title": _("Targeted Minor Faction"),
            "searchable": False,
            "visible": True,
        },
        {
            "name": "num_events",
            "title": _("Count"),
            "searchable": False,
            "visible": True,
        },
        {
            "name": "total_reward",
            "title": _("Amount"),
            "searchable": False,
            "visible": True,
        },
    ]

    def get_initial_queryset(self, request=None):
        return (
            FactionActivity.objects.filter(user_id=request.user.id)
            .values(
                "earning_type__name",
                "minor_faction__name",
                "target_minor_faction__name",
            )
            .annotate(
                num_events=Count("earning_type__name"),
                total_reward=Sum("reward"),
            )
        )

    def render_column(self, row, column):
        if column in ["num_events", "total_reward"]:
            log.debug(row, column)
            return escape(
                number_format(row[column], use_l10n=True, force_grouping=True)
            )
        else:
            return row[column]


class AjaxCrimeHistory(AjaxDatatableView):
    model = Crime
    title = "Criminal History"
    initial_order = [["committed_on", "desc"]]
    length_menu = [[15, 25, 50, 100], [15, 25, 50, 100]]
    search_values_separator = "+"
    show_column_filters = False

    column_defs = [
        {
            "name": "committed_on",
            "title": _("Date Committed"),
            "searchable": False,
            "visible": True,
        },
        {
            "name": "crime_type_id",
            "title": _("Crime"),
            "foreign_field": "crime_type__name",
            "searchable": False,
            "visible": True,
        },
        {
            "name": "minor_faction_id",
            "title": _("Minor Faction Issued By"),
            "foreign_field": "minor_faction__name",
            "searchable": False,
            "visible": True,
        },
        {
            "name": "victim",
            "title": _("Victim"),
            "searchable": False,
            "visible": True,
        },
        {
            "name": "fine",
            "title": _("Fine"),
            "searchable": False,
            "visible": True,
        },
        {
            "name": "bounty",
            "title": _("Bounty"),
            "searchable": False,
            "visible": True,
        },
    ]

    def get_initial_queryset(self, request=None):
        return Crime.objects.filter(user_id=request.user.id)

    def render_column(self, row, column):
        if column in ["fine", "bounty"]:
            log.debug(row, column)
            return escape(
                number_format(getattr(row, column), use_l10n=True, force_grouping=True)
            )
        else:
            value = super(AjaxCrimeHistory, self).render_column(row, column)
            if column == "crime_type_id":
                value = _(camel_case_to_spaces(str(value)).title())
            return value


class AjaxCrimeHistorySummary(AjaxDatatableView):
    model = Crime
    title = "Criminal History Summary"
    initial_order = [["crime_type__name", "asc"]]
    length_menu = [[15, 25, 50, 100], [15, 25, 50, 100]]
    search_values_separator = "+"
    show_column_filters = False

    column_defs = [
        {
            "name": "crime_type__name",
            "title": _("Crime"),
            "searchable": False,
            "visible": True,
        },
        {
            "name": "num_crimes",
            "title": _("Count"),
            "searchable": False,
            "visible": True,
        },
        {
            "name": "total_fine",
            "title": _("Total Fine"),
            "searchable": False,
            "visible": True,
        },
        {
            "name": "total_bounty",
            "title": _("Total Bounty"),
            "searchable": False,
            "visible": True,
        },
    ]

    def get_initial_queryset(self, request=None):
        return (
            Crime.objects.filter(user_id=request.user.id)
            .values(
                "crime_type__name",
            )
            .annotate(
                num_crimes=Count("crime_type__name"),
                total_fine=Sum("fine"),
                total_bounty=Sum("bounty"),
            )
        )

    def render_column(self, row, column):
        if column in ["total_fine", "total_bounty"]:
            log.debug(row, column)
            return escape(
                number_format(row[column], use_l10n=True, force_grouping=True)
            )
        else:
            value = row[column]
            if column == "crime_type__name":
                value = _(camel_case_to_spaces(str(value)).title())
            return value


class AjaxCrimeHistorySummaryFaction(AjaxDatatableView):
    model = Crime
    title = "Criminal History Summary"
    initial_order = [["crime_type__name", "asc"]]
    length_menu = [[15, 25, 50, 100], [15, 25, 50, 100]]
    search_values_separator = "+"
    show_column_filters = False

    column_defs = [
        {
            "name": "crime_type__name",
            "title": _("Crime"),
            "searchable": False,
            "visible": True,
        },
        {
            "name": "minor_faction__name",
            "title": _("Minor Faction Issued By"),
            "searchable": False,
            "visible": True,
        },
        {
            "name": "num_crimes",
            "title": _("Count"),
            "searchable": False,
            "visible": True,
        },
        {
            "name": "total_fine",
            "title": _("Total Fine"),
            "searchable": False,
            "visible": True,
        },
        {
            "name": "total_bounty",
            "title": _("Total Bounty"),
            "searchable": False,
            "visible": True,
        },
    ]

    def get_initial_queryset(self, request=None):
        return (
            Crime.objects.filter(user_id=request.user.id)
            .values(
                "crime_type__name",
                "minor_faction__name",
            )
            .annotate(
                num_crimes=Count("minor_faction__name"),
                total_fine=Sum("fine"),
                total_bounty=Sum("bounty"),
            )
        )

    def render_column(self, row, column):
        if column in ["total_fine", "total_bounty"]:
            log.debug(row, column)
            return escape(
                number_format(row[column], use_l10n=True, force_grouping=True)
            )
        else:
            value = row[column]
            if column == "crime_type__name":
                value = _(camel_case_to_spaces(str(value)).title())
            return value


class AjaxJournalLog(AjaxDatatableView):
    model = JournalLog
    title = "Journal Log"
    initial_order = [["game_start", "asc"]]
    length_menu = [[15, 25, 50, 100], [15, 25, 50, 100]]
    search_values_separator = "+"
    show_column_filters = False

    column_defs = [
        AjaxDatatableView.render_row_tools_column_def(),
        {"name": "id", "searchable": False, "visible": False},
        {
            "name": "file",
            "title": _("Journal Log File"),
            "searchable": False,
            "visible": True,
        },
        {
            "name": "game_start",
            "title": _("Game Log Start Time"),
            "searchable": False,
            "visible": True,
        },
        {
            "name": "game_end",
            "title": _("Game Log End Time"),
            "searchable": False,
            "visible": True,
        },
        {
            "name": "progress_code",
            "title": _("Status"),
            "searchable": False,
            "visible": True,
        },
        {
            "name": "rows_processed",
            "title": _("Events Read"),
            "searchable": False,
            "className": "text-right",
            "visible": True,
        },
        {
            "name": "parser_time",
            "title": _("Processing Time"),
            "searchable": False,
            "className": "text-right",
            "visible": True,
        },
    ]

    def get_initial_queryset(self, request=None):
        return self.model.objects.filter(user_id=self.request.user.id)

    def render_column(self, row, column):
        if column == "progress_code":
            return escape(row.get_status())
        elif column == "file":
            return escape(str(row.file).rsplit("/", 1)[1])
        elif column == "rows_processed":
            return escape(
                number_format(row.rows_processed, use_l10n=True, force_grouping=True)
            )
        elif column == "parser_time":
            return escape(number_format(row.parser_time, decimal_pos=4, use_l10n=True))
        elif column in ["game_start", "game_end"]:
            return escape(getattr(row, column).strftime("%Y-%m-%d %H:%M:%S"))
        else:
            return super(AjaxJournalLog, self).render_column(row, column)


activities_report_callable = {
    "earning_history": AjaxEarningHistory,
    "earning_history_summary": AjaxEarningHistorySummary,
    "earning_history_summary_minor_faction": AjaxEarningHistorySummaryMinorFaction,
    "minor_faction_activities_summary": AjaxMinorFactionActivitiesSummary,
    "criminal_history": AjaxCrimeHistory,
    "criminal_history_summary": AjaxCrimeHistorySummary,
    "criminal_history_summary_faction": AjaxCrimeHistorySummaryFaction,
}

activities_report_title = {
    "earning_history": _("Earning History (Detailed)"),
    "earning_history_summary": _("Earning History Summary"),
    "earning_history_summary_minor_faction": _(
        "Earning History Summary by Minor Faction"
    ),
    "minor_faction_activities_summary": _("Minor Faction Activities Summary"),
    "criminal_history": _("Criminal History (Detailed)"),
    "criminal_history_summary": _("Criminal History Summary"),
    "criminal_history_summary_faction": _("Criminal History Summary by Faction"),
}
