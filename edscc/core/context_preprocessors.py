import logging

from edscc.commander.models import Commander, UserProfile
from edscc.core.menu import build_menu
from edscc.squadron.models import Squadron

log = logging.getLogger(__name__)


def commander_context(request):
    context_data = dict()
    squadron = None
    if request.user.is_authenticated:
        try:
            commander = Commander.objects.get(user_id=request.user.id)
            squadron_id = commander.get_squadron_id()
            if squadron_id:
                squadron = Squadron.objects.get(id=squadron_id)
            context_data = {
                "commander": commander,
                "user_profile": UserProfile.objects.get(id=request.user.id),
                "squadron_info": squadron,
            }
        except Exception as e:
            log.debug(e)

    return context_data


def menu_context(request):
    context_data = dict()
    try:
        context_data = {
            "menu_list": build_menu(request.user),
            "current_route": request.resolver_match.view_name,
        }
        print("Got Here")
    except Exception as e:
        log.debug(e)

    return context_data
