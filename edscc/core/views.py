import logging

from django.conf import settings
from django.contrib import messages
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render
from django.utils import timezone

from .models import Carousel, CommunityGoal, GalnetNews
from .utils import update_galnet_news

log = logging.getLogger(__name__)


# Create your views here.


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
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
