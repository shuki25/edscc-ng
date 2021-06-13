"""
ASGI config for edscc-ng project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/asgi/
"""

import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.conf.urls import url
from django.core.asgi import get_asgi_application

from edscc.commander.initial_setup import StartSetup
from edscc.core.install_setup import StartInstall
from edscc.squadron.setup import StartActivation

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local.py")

application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "https": get_asgi_application(),
        "websocket": AuthMiddlewareStack(
            URLRouter(
                [
                    url(r"^ws/commander/begin_setup/$", StartSetup.as_asgi()),
                    url(r"^ws/core/begin_install/$", StartInstall.as_asgi()),
                    url(r"^ws/squadron/activate_squadron/$", StartActivation.as_asgi()),
                ]
            )
        ),
    }
)
