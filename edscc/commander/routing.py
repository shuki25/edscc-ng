from django.urls import re_path

from . import initial_setup

websocket_urlpatterns = [
    re_path(r"ws/begin_setup/$", initial_setup.StartSetup.as_asgi()),
]
