import logging
import os
import time
import traceback

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render, resolve_url
from django.template.defaultfilters import filesizeformat
from django.utils.translation import gettext as _
from django.views.decorators.csrf import ensure_csrf_cookie

from ..core.session_tracker import SessionTrackerManager
from ..core.utils import evaluate_journal_log
from .ajax_datatables import activities_report_callable, activities_report_title
from .forms import JournalLogForm
from .models import CommanderInfo, UserProfile
from .tasks import parse_journal_file

log = logging.getLogger(__name__)


def index(request):
    return render(request, "placeholder.html", context={"hello": "Hello World!"})


@login_required
def about_commander(request):
    tags_ignored = ["FLEETCARRIER", "timestamp", "event"]
    info = CommanderInfo.objects.filter(user_id=request.user.id)
    data = {}

    for value in info:
        sort_list = sorted(value.content.items())
        data[value.event.lower()] = dict(sort_list)

    if "statistics" in data:
        for tag in tags_ignored:
            data["statistics"].pop(tag, None)
        data["num_categories_column"] = int(len(data["statistics"]) / 3)

    return render(request, "commander/commander_profile2.html", context=data)


@login_required
def initial_setup(request):
    user_list = None
    try:
        user_list = UserProfile.objects.get(id=request.user.id, is_setup_complete=True)
    except Exception as e:
        log.debug("initial_setup: %s" % e)
        traceback.print_exc()
    if user_list is None:
        return render(
            request, "commander/initial_setup.html", context={"user_list": user_list}
        )
    else:
        log.debug(user_list)
        return redirect(resolve_url("home"))


@ensure_csrf_cookie
@login_required
def activities_report(request, report=None):
    if report in activities_report_callable:
        log.debug("is executing activities report callable")
        callable_class = activities_report_callable[report]
        return callable_class.as_view()(request)
    else:
        report_name = (
            request.POST.get("selected-report")
            if request.POST.get("selected-report")
            else "earning_history"
        )

    data = {
        "available_reports": activities_report_title,
        "report_name": report_name,
    }
    return render(request, "commander/activities_report.html", context=data)


@login_required
def game_journal(request):
    data = {}
    return render(request, "commander/journal_log.html", context=data)


@login_required
def game_journal_upload(request):
    data = {"is_valid": False, "message": _("Bad method")}
    if request.method == "POST":
        form = JournalLogForm(request.POST, request.FILES)
        if form.is_valid():
            status = "Accepted"
            journal_file = form.save(commit=False)
            journal_file.user = request.user
            journal_file.save()
            file_path = settings.MEDIA_ROOT + "/" + str(journal_file.file.name)
            i = 10
            while i > 0:
                if os.path.isfile(file_path) is False:
                    i -= 1
                    if i == 0:
                        data = {"is_valid": False, "message": _("Upload failed")}
                        return JsonResponse(data)
                    time.sleep(0.5)
                else:
                    break

            filesize = filesizeformat(os.path.getsize(file_path))
            rs = evaluate_journal_log(request.user.id, file_path)

            data = {
                "is_valid": True,
                "name": str(journal_file.file.name).replace("journal_log/", ""),
                "file_type": rs["file_type"],
                "size": filesize,
                "message": _(status),
            }
            if rs["is_valid"]:
                journal_file.file_hash = rs["md5_hash"]
                journal_file.game_start = rs["game_start"]
                journal_file.game_end = rs["game_end"]
                journal_file.save()
                session = SessionTrackerManager(
                    user=request.user,
                    session_identifier="upload",
                    initial_payload={"celery_task": False},
                )
                celery_task = session.get_attr("celery_task")
                if celery_task is False:
                    parse_journal_file.apply_async(args=[request.user.id], countdown=20)
                    session.set_attr("celery_task", True)
            else:
                data["is_valid"] = False
                data["message"] = "%s: %s" % (_("Rejected"), _(rs["message"]))
                try:
                    os.remove(file_path)
                    journal_file.delete()
                    log.debug(
                        "Not valid: Upload record deleted and the file was removed"
                    )
                except FileNotFoundError:
                    pass
        else:
            data = {"is_valid": False, "message": _("Problems with the upload")}
    return JsonResponse(data)
