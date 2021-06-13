import json
import logging
import time

import channels.exceptions
from channels.consumer import SyncConsumer
from django.contrib.auth.models import Group, User
from django.db import transaction
from django.utils.translation import gettext as _

from ..core.capi import Capi
from ..core.utils import hex2text
from ..squadron.models import Faction, MinorFaction, Power, Squadron, Tags
from .utils import sync_squadron_roster

log = logging.getLogger(__name__)


class StartActivation(SyncConsumer):
    download_path = None
    fdev_squadron_id = None
    local_squadron_id = None
    squadron_tag = None
    user = None
    squadron_data = None
    members = None
    api = None

    def __init__(self):
        super().__init__()
        self.download_path = None

    def websocket_disconnect(self, event):
        raise channels.exceptions.StopConsumer

    def websocket_connect(self, event):
        self.send({"type": "websocket.accept", "text": "connected"})
        log.debug("Websocket connected: awaiting next step")

    def websocket_receive(self, event):
        log.debug("in websocket_receive")
        log.debug(event["text"])
        parsed_message = json.loads(event["text"])
        is_valid = False

        if (
            parsed_message["message"] == "start-setup"
            and "user_id" in parsed_message
            and "squadron_id" in parsed_message
            and "squadron_tag" in parsed_message
        ):
            try:
                self.user = User.objects.get(id=parsed_message["user_id"])
                self.fdev_squadron_id = parsed_message["squadron_id"]
                self.squadron_tag = parsed_message["squadron_tag"]
                is_valid = True

            except User.DoesNotExist:
                self.send(
                    {
                        "type": "websocket.send",
                        "text": {"status": "404", "message": "User account not found."},
                    }
                )

        if parsed_message["message"] == "start-setup" and is_valid:
            install_tasks = {
                "Preparing": self.do_prepare_activation,
                "Activating": self.do_activate,
                "Synchronizing Squadron Roster": self.do_sync_roster,
                "Finishing up": self.do_cleanup,
                "DONE": None,
            }

            time.sleep(1)
            num_tasks = len(install_tasks) * 2
            i = 1
            for status, task in install_tasks.items():
                i = self.update_progress_bar(status, i, num_tasks, {"Status": "200"})
                if task is not None:
                    status, i = task(i, num_tasks)
                    log.debug("in websocket_receive: status=%s" % status)
                    if status["code"] in [500, 404, 403, 401]:
                        log.debug("raise BaseException")
                        self.update_progress_bar(
                            status["message"],
                            i,
                            num_tasks,
                            {"Status": status["code"]},
                        )
                        raise BaseException
                    time.sleep(0.5)
                time.sleep(0.5)

        else:
            self.send(
                {
                    "type": "websocket.send",
                    "text": {
                        "status": "500",
                        "message": "Missing parameters, aborted.",
                        "event": event["text"],
                    },
                }
            )

    def status_update(self, message, formatted=True, progress=0, server_code=None):
        if server_code is None:
            server_code = {"Status": "Unknown"}
        if formatted and "DONE" not in message:
            message = "Status: %s..." % message
        print(server_code)
        json_data = json.dumps(
            {"server_code": server_code, "message": message, "progress_value": progress}
        )
        print(json_data)
        self.send({"type": "websocket.send", "text": json_data})

    def data_preview(self, data):
        parsed_data = json.loads(data)
        for key, value in parsed_data:
            self.status_update("key %s: value: %s" % (key, value), False)
            break

    def update_progress_bar(self, status, current, max_value, server_code):
        progress_pct = round((current / max_value) * 100)
        self.status_update(status, progress=progress_pct, server_code=server_code)
        return current + 1

    def do_prepare_activation(self, current, max_value):
        status = {"code": 200}
        log.debug("in do_prepare_activation")

        self.api = Capi(self.user.id)
        server_status, members = self.api.get_squadron_members(
            self.user.id, self.fdev_squadron_id, websocket=True
        )

        if server_status["Status"] != 200:
            log.debug("status=%s\nmembers=%s" % (server_status, self.members))
            if "message" in members:
                msg = "%s %s" % (
                    _("Permission denied, activation failed."),
                    _(members["message"]),
                )
                server_status["Status"] = members["status"]
            else:
                msg = "%s %s" % (
                    _("Permission denied, activation failed."),
                    _("Unknown Error."),
                )
            status["message"] = msg
            status["code"] = server_status["Status"]
        else:
            self.members = members["members"]

        time.sleep(0.5)
        return status, current + 2

    def do_activate(self, current, max_value):
        data = {}
        status = {"code": 200}

        server_status, self.squadron_data = self.api.get_squadron_details(
            self.user.id, squadron_tag=self.squadron_tag
        )

        if server_status["Status"] != 200:
            msg = "status=%s\ndata=%s" % (server_status, data)
            status["message"] = msg
            status["code"] = server_status["Status"]
            log.debug(msg)
        else:
            if "squadron" in self.squadron_data:
                data = self.squadron_data["squadron"]
                log.debug(data)
                qs = Power.objects.all()
                power = {i.name.lower(): i.id for i in qs}
                qs = Faction.objects.all()
                superpower = {i.name.lower(): i.id for i in qs}
                qs = MinorFaction.objects.all()
                minor_faction = {i.name.lower(): i.id for i in qs}
                power_id = None
                superpower_id = None
                minor_faction_id = None

                if "powerName" in data and data["powerName"].lower() in power:
                    power_id = power[data["powerName"].lower()]
                if (
                    "superpowerName" in data
                    and data["superpowerName"].lower() in superpower
                ):
                    superpower_id = superpower[data["superpowerName"].lower()]
                if (
                    "factionName" in data
                    and data["factionName"].lower() in minor_faction
                ):
                    minor_faction_id = minor_faction[data["factionName"].lower()]

                try:
                    squadron = Squadron.objects.get(fdev_id=data["id"])
                    msg = _("Squadron is already activated.")
                    status = {"code": 500, "message": msg}
                    log.debug(msg)

                except Squadron.DoesNotExist:
                    squadron = Squadron(
                        fdev_id=data["id"],
                        name=data["name"],
                        tag=data["tag"],
                        owner_id=data["ownerId"],
                        owner_name=hex2text(data["ownerName"]),
                        platform=data["platform"],
                        power_id=power_id,
                        superpower_id=superpower_id,
                        faction_id=minor_faction_id,
                        admin_id=self.user.id,
                        established_on=data["created"],
                    )
                    squadron.save()
                    self.local_squadron_id = squadron.id
                    tags = Tags.objects.filter(fdev_id__in=data["squadron_tag_ids"])
                    log.debug(tags)
                    for i in tags:
                        squadron.squadron_tags.add(i)

                    try:
                        user = User.objects.get(id=self.user.id)
                        group = Group.objects.get(name="Unaffiliated")
                        user.groups.remove(group)
                        groups = Group.objects.filter(
                            name__in=["Squadron", "Squadron Owner"]
                        )
                        for group in groups:
                            group.user_set.add(user)
                    except Exception as e:
                        log.debug(e)

            else:
                msg = _(
                    "Unable to activate Squadron. Problem with getting the data from Frontier Server."
                )
                status["code"] = 500
                status["message"] = msg
                log.debug(msg)

        return status, current + 2

    @transaction.atomic
    def do_sync_roster(self, current, max_value):
        try:
            results = sync_squadron_roster(self.members, self.local_squadron_id)
            if "error" in results and results["error"]:
                status = {"code": 500, "message": results["message"]}
            else:
                status = {"code": 200, "message": results}
        except Exception as e:
            status = {"code": 500, "message": e}
        return status, current + 1

    def do_cleanup(self, current, max_value):
        status = {"code": 200}
        time.sleep(0.5)
        return status, current + 1
