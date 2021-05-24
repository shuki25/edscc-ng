import copy
import logging
import os
from hashlib import md5

from django.contrib.auth.models import User

from .models import SessionTracker

log = logging.getLogger(__name__)


class SessionTrackerManager:
    def __init__(
        self,
        hash_key=None,
        user=None,
        session_identifier="journal",
        initial_payload=None,
    ):

        self.session_obj = None

        if user is not None and not isinstance(user, User):
            raise TypeError
        if hash_key is None and isinstance(user, User):
            session_string = "%s:%d:%s" % (
                session_identifier,
                user.id,
                os.environ.get("SESSION_TRACKER_SECRET"),
            )
            m = md5(session_string.encode("utf-8"))
            self.hash_key = m.hexdigest()
        elif hash_key:
            self.hash_key = hash_key
        else:
            return

        try:
            self.session_obj = SessionTracker.objects.get(hash_key=self.hash_key)
        except SessionTracker.DoesNotExist:
            if initial_payload is None:
                payload = {
                    "station_name": None,
                    "station_faction": None,
                }
            else:
                payload = copy.deepcopy(initial_payload)
            self.session_obj = SessionTracker(hash_key=self.hash_key, payload=payload)
            self.session_obj.save()

    def get_attr(self, key):
        if key in self.session_obj.payload:
            return self.session_obj.payload[key]

    def set_attr(self, key, value):
        self.session_obj.payload[key] = value
        self.session_obj.save()
