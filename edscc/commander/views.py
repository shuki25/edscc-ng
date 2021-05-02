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

from edscc.core.utils import evaluate_journal_log

from .forms import JournalLogForm
from .models import Commander, CommanderInfo, UserProfile

log = logging.getLogger(__name__)


def index(request):
    return render(request, "placeholder.html", context={"hello": "Hello World!"})


@login_required
def about_commander(request):
    skill_web = {}

    if request.user.is_authenticated:
        try:
            c = Commander.objects.get(user_id=request.user.id)
            skill_web = c.get_skill_web()
        except Commander.DoesNotExist:
            log.debug("Commander profile not found.")

    info = CommanderInfo.objects.filter(user_id=request.user.id)

    data = {
        "skill_web": skill_web,
        "tags_ignored": ["FLEETCARRIER", "timestamp", "event"],
    }

    for value in info:
        sort_list = sorted(value.content.items())
        data[value.event.lower()] = dict(sort_list)

    return render(request, "commander/commander_profile.html", context=data)


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
