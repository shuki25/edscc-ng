import logging
from urllib.parse import urlencode

import pandas as pd
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods, require_POST

from ..commander.models import Commander, UserProfile
from ..core.capi import Capi
from ..core.decorators import group_required, cached
from ..core.utils import Paginator
from .forms import SquadronForm
from .models import Faction, Leaderboard, Power, Squadron, SquadronRoster
from .utils import leaderboards_to_df, sync_leaderboard, top_n_leaderboard

log = logging.getLogger(__name__)


@login_required
def join_squadron(request):
    if request.method == "GET" and "new" in request.GET:
        messages.success(request, "Your account was successfully created.")

    data = {
        "squadron": Squadron.objects.filter(
            active=True,
        ).order_by("tag"),
    }
    return render(request, "squadron/join_squadron.html", context=data)


@login_required
def setup_squadron(request):
    keyword = None
    limit = 12
    offset = 0
    platform = "PC"

    if request.method == "POST":
        keyword = request.POST.get("keyword")
        platform = request.POST.get("platform")
    if request.method == "GET":
        if request.GET.get("offset"):
            offset = request.GET.get("offset")
            limit = request.GET.get("limit")
            keyword = request.GET.get("keyword")
            platform = request.GET.get("platform")

    api = Capi()
    status, data = api.get_squadron_list(
        request.user.id,
        name=keyword,
        tag=keyword[0:3] if keyword else None,
        offset=offset,
        limit=limit,
        platform=platform,
    )

    if status["Status"] == 200:
        if "totalResults" in data:
            data["keyword"] = keyword if keyword else ""
            data["platform"] = platform if platform else ""
            p = Paginator(
                offset=data["offset"],
                limit=data["limit"],
                count=data["totalResults"],
                width=7,
                keyword=data["keyword"],
                tag=data["keyword"][0:3],
                platform=data["platform"],
            )

            data["num_squadrons_column"] = round(
                (p.num_items(p.current_page()) / 3) + 0.45
            )
            data["pagination"] = p
            qs = Power.objects.all()
            power = {i.name.lower(): i.logo for i in qs}
            qs = Faction.objects.all()
            superpower = {i.name.lower(): i.logo for i in qs}
            qs = Squadron.objects.all()
            active_squadrons = {i.fdev_id: i.name for i in qs}

            for row, squadron in enumerate(data["squadrons"]):
                logo = None
                if "powerName" in squadron and squadron["powerName"].lower() in power:
                    logo = power[squadron["powerName"].lower()]
                elif (
                    "superpowerName" in squadron
                    and squadron["superpowerName"].lower() in superpower
                ):
                    logo = superpower[squadron["superpowerName"].lower()]
                data["squadrons"][row]["logo"] = logo
                if squadron["id"] in active_squadrons:
                    data["squadrons"][row]["active"] = True
                else:
                    data["squadrons"][row]["active"] = False

    return render(request, "squadron/setup_squadron.html", context=data)


@login_required
@require_http_methods(["POST"])
def finish_activate_squadron(request):
    members = None
    owner = None
    admin = None
    squadron_form = SquadronForm()

    squadron_id = request.POST.get("squadron_id")
    squadron_tag = request.POST.get("squadron_tag")
    kwargs = {
        "keyword": request.POST.get("keyword"),
        "platform": request.POST.get("platform"),
        "offset": request.POST.get("offset"),
        "limit": request.POST.get("limit"),
    }
    squadron_uuid = request.POST.get("uuid")

    if squadron_uuid:
        squadron_form = SquadronForm(request.POST)
        try:
            squadron = Squadron.objects.get(uuid=squadron_uuid)
            admin = UserProfile.objects.get(id=squadron.admin_id)
            if squadron_form.is_valid():
                update_data = squadron_form.save(commit=False)
                squadron.home_base = update_data.home_base
                squadron.primary_language = update_data.primary_language
                squadron.description = update_data.description
                squadron.welcome_message = update_data.welcome_message
                squadron.require_approval = update_data.require_approval
                squadron.save()
                messages.success(
                    request,
                    _("Your Squadron information has been saved and activated."),
                )
                return HttpResponseRedirect(reverse("home"))
        except Squadron.DoesNotExist:
            squadron = None
            admin = None
    else:
        if request.POST.get("status") != "200":
            msg = _(request.POST.get("message"))
            messages.error(request, msg)
            url = "%s?%s" % (reverse("squadron:setup_squadron"), urlencode(kwargs))
            return HttpResponseRedirect(url)

        try:
            squadron = Squadron.objects.get(fdev_id=squadron_id)
            admin = UserProfile.objects.get(id=squadron.admin_id)
            squadron_form = SquadronForm(instance=squadron)
        except Squadron.DoesNotExist:
            squadron = None

    if squadron is not None:
        try:
            members = SquadronRoster.objects.filter(squadron_id=squadron.id)
        except SquadronRoster.DoesNotExist:
            members = None
        try:
            owner_commander = Commander.objects.get(player_id=squadron.owner_id)
            owner = UserProfile.objects.get(id=owner_commander.id)
        except Commander.DoesNotExist:
            owner = None

    qs = Power.objects.all()
    power = {i.id: i.logo for i in qs}
    qs = Faction.objects.all()
    superpower = {i.id: i.logo for i in qs}

    logo = None
    if squadron is not None and squadron.power_id in power:
        logo = power[squadron.power_id]
    elif squadron is not None and squadron.superpower_id in superpower:
        logo = superpower[squadron.superpower_id]

    context = {
        "squadron": squadron,
        "members": members,
        "num_members": len(members),
        "owner": owner,
        "admin": admin,
        "logo": logo,
        "squadron_form": squadron_form,
    }
    return render(request, "squadron/activation_next_step.html", context=context)


@group_required("Squadron Admin", "Squadron Owner")
def settings(request):
    members = None
    owner = None
    admin = None
    commander = get_object_or_404(Commander, user_id=request.user.id)

    if request.POST.get("uuid"):
        squadron_form = SquadronForm(request.POST)
        squadron = get_object_or_404(Squadron, uuid=request.POST.get("uuid"))
        try:
            admin = UserProfile.objects.get(id=squadron.admin_id)
            if squadron_form.is_valid():
                update_data = squadron_form.save(commit=False)
                squadron.home_base = update_data.home_base
                squadron.primary_language = update_data.primary_language
                squadron.description = update_data.description
                squadron.welcome_message = update_data.welcome_message
                squadron.require_approval = update_data.require_approval
                squadron.save()
                messages.success(
                    request,
                    _("Your Squadron settings have been updated."),
                )
        except Squadron.DoesNotExist:
            squadron = None
            admin = None
    else:
        squadron = get_object_or_404(Squadron, id=commander.get_squadron_id())
        try:
            admin = UserProfile.objects.get(id=squadron.admin_id)
            squadron_form = SquadronForm(instance=squadron)
        except Squadron.DoesNotExist:
            squadron = None

    if squadron is not None:
        num_members = SquadronRoster.objects.filter(squadron_id=squadron.id).count()
        try:
            owner_commander = Commander.objects.get(player_id=squadron.owner_id)
            owner = UserProfile.objects.get(id=owner_commander.id)
        except Commander.DoesNotExist:
            owner = None

    qs = Power.objects.all()
    power = {i.id: i.logo for i in qs}
    qs = Faction.objects.all()
    superpower = {i.id: i.logo for i in qs}

    logo = None
    if squadron is not None and squadron.power_id in power:
        logo = power[squadron.power_id]
    elif squadron is not None and squadron.superpower_id in superpower:
        logo = superpower[squadron.superpower_id]

    context = {
        "squadron": squadron,
        "num_members": num_members,
        "owner": owner,
        "admin": admin,
        "logo": logo,
        "squadron_form": squadron_form,
    }
    return render(request, "squadron/settings.html", context=context)


@group_required("Squadron")
def roster(request):
    return render(request, "squadron/roster.html", context={})


@group_required("Squadron")
# @cached(name="leaderboard", timeout=300, request=True)
def leaderboard(request):
    leaderboards = []
    sync_leaderboard(request.user, platform=request.user.userprofile.squadron.platform)
    rs = (
        Leaderboard.objects.filter(squadron_id=2)
        .values("last_updated")
        .distinct()
        .order_by("-last_updated")[:2]
    )
    date_range = [i["last_updated"] for i in rs]
    current = Leaderboard.objects.filter(
        squadron_id=request.user.userprofile.squadron_id, last_updated=date_range[0]
    )
    previous = Leaderboard.objects.filter(
        squadron_id=request.user.userprofile.squadron_id, last_updated=date_range[1]
    )
    if len(previous) == 0:
        available_squadron = (
            Leaderboard.objects.filter(last_updated=date_range[1])
            .values("squadron_id")
            .distinct()
        )
        if len(available_squadron):
            previous = Leaderboard.objects.filter(
                squadron_id=available_squadron[0]["squadron_id"],
                last_updated=date_range[1],
            )

    df = leaderboards_to_df(current, previous)

    data = {
        "leaderboards": top_n_leaderboard(
            df, fdev_id=request.user.userprofile.squadron.fdev_id
        ),
        "fdev_id": request.user.userprofile.squadron.fdev_id,
    }

    return render(request, "squadron/leaderboard.html", context=data)
