import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from ..squadron.models import Squadron

log = logging.getLogger(__name__)


@login_required
def join_squadron(request):
    if request.method == "GET" and "new" in request.GET:
        messages.success(request, "Your account was successfully created.")

    data = {
        "squadron": Squadron.objects.filter(
            active=True,
        ).order_by("id_code"),
    }
    return render(request, "squadron/join_squadron.html", context=data)


@login_required
def create_squadron(request):
    return render(request, "placeholder.html", context={})
