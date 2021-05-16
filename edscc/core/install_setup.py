import json
import logging
import time

import channels.exceptions
import jsonlines
from channels.consumer import SyncConsumer
from django.core import management
from django.db import transaction

from ..squadron.models import MinorFaction
from .utils import BulkCreateManager, fetch_eddb_data

log = logging.getLogger(__name__)


class StartInstall(SyncConsumer):
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
        if parsed_message["message"] == "start-setup":
            install_tasks = {
                "Starting Setup": None,
                "Loading Data Fixtures": self.do_data_fixtures,
                "Downloading Minor Factions": self.do_mf_download,
                "Loading Minor Factions": self.do_mf_import,
                "Finishing up the setup install": self.do_cleanup,
                "DONE": None,
            }
            time.sleep(1)
            num_tasks = len(install_tasks) * 2
            i = 1
            for status, task in install_tasks.items():
                i = self.update_progress_bar(status, i, num_tasks, {"Status": "OK"})
                if task is not None:
                    status, i = task(i, num_tasks)
                    if status["code"] == 500:
                        self.update_progress_bar(
                            status["message"], i, num_tasks, {"Status": status["code"]}
                        )
                        raise BaseException
                    time.sleep(1)
                time.sleep(0.5)
        else:
            print("Bypassed, did not intercept")
            print(event)
            self.send(
                {
                    "type": "websocket.send",
                    "text": event["text"],
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

    def do_data_fixtures(self, current, max_value):
        status = {"code": 200}
        log.debug("in do_data_fixture")
        app_fixtures = [
            "fixtures/commander/initial_setup.json",
            "fixtures/core/initial_setup.json",
            "fixtures/core/initial_auth_group.json",
            "fixtures/squadron/initial_setup.json",
        ]

        for fixture in app_fixtures:
            try:
                management.call_command("loaddata", fixture, verbosity=1)
            except management.CommandError as e:
                log.debug(e)
                current = self.update_progress_bar(
                    "Failed to load fixtures, aborted.",
                    current,
                    max_value,
                    {"Status": "OK"},
                )
                status = {"code": 500, "message": f"Error: {e}"}
                break
        return status, current + 2

    def do_mf_download(self, current, max_value):
        status = {"code": 200}
        log.debug("in do_mf_download")
        return_code, path = fetch_eddb_data("factions.jsonl")
        if return_code["Status"] != 200:
            current = self.update_progress_bar(
                "Failed to download Minor Factions Data",
                current,
                max_value,
                return_code,
            )
            status = {"code": 500, "message": f"Error: Download from EDDB failed"}
            time.sleep(2)
        else:
            self.download_path = path
        time.sleep(1)
        return status, current + 2

    @transaction.atomic
    def do_mf_import(self, current, max_value):
        status = {"code": 200}
        log.debug("in do_mf_import")
        log.debug(f"Downloaded file: {self.download_path}")
        try:
            i = 0
            with jsonlines.open(self.download_path) as reader:
                bulk_mgr = BulkCreateManager(chunk_size=150)
                for row in reader:
                    bulk_mgr.add(
                        MinorFaction(
                            eddb_id=row["id"],
                            name=row["name"],
                            player_faction=row["is_player_faction"],
                        )
                    )
                    i += 1
                bulk_mgr.done()
            log.debug("%d minor factions added" % i)
        except jsonlines.Error as e:
            log.debug(e)
            status = {"code": 500, "message": f"Error: JSON Parse failed"}
        return status, current + 2

    def do_cleanup(self, current, max_value):
        status = {"code": 200}
        time.sleep(1)
        return status, current + 1
