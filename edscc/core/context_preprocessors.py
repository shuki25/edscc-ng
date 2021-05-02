import logging

from edscc.commander.models import Commander, UserProfile
from edscc.core.menu import build_menu

log = logging.getLogger(__name__)


def commander_context(request):
    context_data = dict()
    if request.user.is_authenticated:
        try:
            context_data = {
                "commander": Commander.objects.get(user_id=request.user.id),
                "user_profile": UserProfile.objects.get(id=request.user.id),
            }
        except Exception as e:
            log.debug(e)

    return context_data


def menu_context(request):
    context_data = dict()

    log.debug("context_data: %s" % context_data)
    try:
        context_data = {
            "menu_list": build_menu(request.user),
            "current_route": request.resolver_match.view_name,
        }
        print("Got Here")
    except Exception as e:
        log.debug(e)

    return context_data
