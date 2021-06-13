import logging

from ajax_datatable.views import AjaxDatatableView
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.db.models import Count, Sum
from django.utils.formats import number_format
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.text import camel_case_to_spaces
from django.utils.translation import ugettext as _

from ..commander.models import Commander
from .models import Squadron, SquadronRoster

log = logging.getLogger(__name__)


class AjaxMemberRoster(AjaxDatatableView):
    model = SquadronRoster
    title = _("Squadron Roster")
    initial_order = [["cmdr_name", "asc"]]
    length_menu = [[15, 25, 50, 100], [15, 25, 50, 100]]
    search_values_separator = "+"
    show_column_filters = False

    column_defs = [
        {"name": "id", "searchable": False, "visible": False},
        {
            "name": "cmdr_name",
            "title": _("Commander"),
            "searchable": False,
            "visible": True,
        },
        {
            "name": "rank_id",
            "title": _("Squadron Rank"),
            "foreign_field": "rank__name",
            "searchable": False,
            "visible": True,
        },
        {
            "name": "rank_combat_id",
            "title": _("Combat Rank"),
            "foreign_field": "rank_combat__name",
            "searchable": False,
            "visible": True,
        },
        {
            "name": "rank_explore_id",
            "title": _("Explore Rank"),
            "foreign_field": "rank_explore__name",
            "searchable": False,
            "visible": True,
        },
        {
            "name": "rank_trade_id",
            "title": _("Trade Rank"),
            "foreign_field": "rank_trade__name",
            "searchable": False,
            "visible": True,
        },
        {
            "name": "rank_exobiologist_id",
            "title": _("Exobiologist Rank"),
            "foreign_field": "rank_exobiologist__name",
            "searchable": False,
            "visible": True,
        },
        {
            "name": "rank_mercenary_id",
            "title": _("Mercenary Rank"),
            "foreign_field": "rank_mercenary__name",
            "searchable": False,
            "visible": True,
        },
        {
            "name": "is_member",
            "title": _("Active"),
            "searchable": False,
            "visible": True,
        },
        {
            "name": "has_account",
            "title": _("ED:SCC"),
            "searchable": False,
            "visible": True,
        },
        {
            "name": "last_online",
            "title": _("Last Online"),
            "searchable": False,
            "visible": True,
        },
    ]

    def get_initial_queryset(self, request=None):
        if not request.user.is_authenticated:
            raise PermissionDenied

        if "uuid" in request.POST:
            uuid = request.POST.get("uuid")
        else:
            raise ImproperlyConfigured("Variable 'uuid' is required")

        if uuid:
            squadron = Squadron.objects.get(uuid=uuid)
            return self.model.objects.filter(squadron_id=squadron.id)
        else:
            raise ImproperlyConfigured("Variable 'uuid' is required")

    def render_column(self, row, column):
        if column in ["is_member", "has_account"]:
            if getattr(row, column) is True:
                html = '<i class="fas fa-check-circle text-success"></i>'
            else:
                html = '<i class="fas fa-times-circle text-danger"></i>'
            return mark_safe(html)
        else:
            return super(AjaxMemberRoster, self).render_column(row, column)
