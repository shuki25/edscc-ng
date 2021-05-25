import ast
import datetime
import logging
import traceback

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import redirect, render, resolve_url
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from .capi import Capi
from .models import CapiLog, Carousel, CommunityGoal, GalnetNews
from .utils import update_galnet_news
from ..commander.models import CommanderInfo, Status

log = logging.getLogger(__name__)


def login_required_alert(request):
    return render(request, "core/login_required.html")


def placeholder(request):
    return render(request, "placeholder.html")


def privacy_policy(request):
    return render(request, "privacy_policy.html", context={"title": "Privacy Policy"})


def home_page(request):
    if request.method == "GET" and "new" in request.GET:
        messages.success(request, "Your account was successfully created.")

    data = {
        "carousel": Carousel.objects.filter(
            start_datetime__lte=timezone.now(),
            end_datetime__gte=timezone.now(),
            is_active=True,
            is_visible=True,
            squadron__isnull=True,
        ).order_by("start_datetime"),
        "cg_list": CommunityGoal.objects.filter(expiry__gte=timezone.now()),
    }
    return render(request, "core/index.html", context=data)


def galnet_news(request):
    data = {
        "carousel": GalnetNews.objects.all().order_by("-nid")[:4],
        "galnet_news": GalnetNews.objects.all().order_by("-nid")[4:10],
        "galnet_img_url": settings.GALNET_IMAGE_URL,
    }
    data["num_cards"] = len(data["galnet_news"])
    return render(request, "core/galnet.html", context=data)


def galnet_news_detail(request, slug):
    try:
        article = GalnetNews.objects.get(slug=slug)
    except GalnetNews.DoesNotExist:
        raise Http404("Article not found.")

    data = {
        "article": article,
        "galnet_img_url": settings.GALNET_IMAGE_URL,
    }

    return render(request, "core/galnet-detail.html", context=data)


def sync_galnet_news(request):
    update_galnet_news(request)
    return HttpResponseRedirect(request.META.get("HTTP_REFERER"))


@login_required
def cmdr_fleet_carrier(request):
    capi_log = (
        CapiLog.objects.filter(user_id=request.user.id, endpoint="fleetcarrier")
        .order_by("date_received")
        .last()
    )
    if isinstance(capi_log, CapiLog):
        fc_data = ast.literal_eval(capi_log.data)
        days_remaining = (
            fc_data["finance"]["bankReservedBalance"]
            / fc_data["finance"]["maintenance"]
        )

        funded_until = datetime.datetime.now() + datetime.timedelta(
            weeks=days_remaining
        )

        info = CommanderInfo.objects.filter(user_id=request.user.id, event="Statistics")

        tmp = {}
        for value in info:
            sort_list = sorted(value.content.items())
            tmp[value.event.lower()] = dict(sort_list)

        operation_statistics = {}

        if "statistics" in tmp:
            if "FLEETCARRIER" in tmp["statistics"]:
                operation_statistics = tmp["statistics"]["FLEETCARRIER"]
                operation_statistics_timestamp = parse_datetime(
                    tmp["statistics"]["timestamp"]
                )

        data = {
            "has_carrier_info": True,
            "data": fc_data,
            "fc_name": bytes.fromhex(fc_data["name"]["vanityName"]).decode("utf-8"),
            "arrived_since": parse_datetime(
                fc_data["itinerary"]["completed"][0]["arrivalTime"]
            ),
            "fuel_percent": (int(fc_data["fuel"]) / 1000) * 100,
            "last_updated": parse_datetime(str(capi_log.date_received)),
            "funded_until": funded_until,
            "operation_statistics": operation_statistics,
            "operation_statistics_timestamp": operation_statistics_timestamp,
        }
    else:
        data = {}
    return render(request, "core/fleet-carrier.html", context=data)


@login_required
def sync_fleet_carrier(request):
    api = Capi(request)
    return_code, data = api.get_fleetcarrier(request.user.id)
    return HttpResponseRedirect(request.META.get("HTTP_REFERER"))


def install_setup(request):
    status = None
    try:
        status = Status.objects.get(pk=1)
    except Exception as e:
        log.debug("initial_setup: %s" % e)
        traceback.print_exc()
    if status is None:
        return render(request, "core/install_setup.html")
    else:
        log.debug("Install setup was previously done, setup skipped")
        return redirect(resolve_url("home"))
