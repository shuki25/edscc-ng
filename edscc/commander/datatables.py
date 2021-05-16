import logging

from django.utils.html import escape
from django_datatables_view.base_datatable_view import BaseDatatableView

from .models import JournalLog

progress_code = {
    "Q": "In Queue",
    "U": "Uploaded",
    "P": "Parsing",
    "C": "Processed",
    "E": "Error",
}
log = logging.getLogger(__name__)


class AjaxJournalLog(BaseDatatableView):
    model = JournalLog
    columns = [
        "id",
        "file",
        "game_start",
        "game_end",
        "progress_code",
        "error_count",
    ]
    order_columns = [
        "id",
        "file",
        "game_start",
        "game_end",
        "progress_code",
        "error_count",
    ]

    max_display_length = 50

    def get_initial_queryset(self):
        return self.model.objects.filter(user_id=2)

    def render_column(self, row, column):
        if column == "progress_code":
            return escape(progress_code[row.progress_code])
        elif column == "file":
            return escape(str(row.file).rsplit("/", 1)[1])
        elif column in ["game_start", "game_end"]:
            return escape(getattr(row, column).strftime("%Y-%m-%d %H:%M:%S"))
        else:
            return super(AjaxJournalLog, self).render_column(row, column)

    def filter_queryset(self, qs):
        search = self.request.GET.get("search[value]", None)
        if search:
            qs = qs.filter(file__istartswith=search, user_id=self.request.user.id)
        return qs
