import json
import logging
import time
import traceback

import channels.exceptions
from channels.consumer import SyncConsumer
from django.contrib.auth.models import Group, User

from edscc.commander.models import Commander, Status, UserProfile
from edscc.core.capi import Capi
from edscc.core.models import CommunityGoal
from edscc.squadron.models import Rank

log = logging.getLogger(__name__)


def get_user_id(email):
    user_id = None
    try:
        user_id = User.objects.get(email=email).id
    except User.DoesNotExist:
        log.debug("%s not found in user table" % email)
    return user_id


class StartSetup(SyncConsumer):
    api = Capi()

    def websocket_disconnect(self, event):
        raise channels.exceptions.StopConsumer

    def websocket_connect(self, event):
        self.user = self.scope["user"]
        self.uid = get_user_id(self.user)
        self.send({"type": "websocket.accept", "text": "connected"})

    def websocket_receive(self, event):
        parsed_message = json.loads(event["text"])
        if parsed_message["message"] == "start-setup":
            setup_tasks = {
                "Connecting to Frontier Server": None,
                "Fetching Commander Profile": self.do_profile,
                "Fetching Shipyard Inventory": self.do_shipyard,
                "Fetching Fleet Carrier Information": self.do_fleetcarrier,
                "Fetching Community Goals Information": self.do_community_goals,
                "Setting Up Your Account": self.do_cleanup,
                "DONE": None,
            }
            time.sleep(1)
            num_tasks = len(setup_tasks) * 2
            i = 1
            for status, task in setup_tasks.items():
                i = self.update_progress_bar(status, i, num_tasks, {"Status": "OK"})
                if task is not None:
                    i = task(self.uid, i, num_tasks)
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

    def add_user_to_groups(self, user, groups):
        for group in groups:
            try:
                g_obj = Group.objects.get(name=group)
                g_obj.user_set.add(user)
            except Exception as e:
                log.debug(e)

    def data_preview(self, data):
        parsed_data = json.loads(data)
        for key, value in parsed_data:
            self.status_update("key %s: value: %s" % (key, value), False)
            break

    def update_progress_bar(self, status, current, max_value, server_code):
        progress_pct = round((current / max_value) * 100)
        self.status_update(status, progress=progress_pct, server_code=server_code)
        return current + 1

    def do_profile(self, user_id, current, max_value):
        return_code, data = self.api.get_profile(user_id)
        if return_code["Status"] != 200:
            current = self.update_progress_bar(
                "Failed to receive Commander Profile", current, max_value, return_code
            )
            time.sleep(2)
        else:
            current = self.update_progress_bar(
                "Processing Commander Profile", current, max_value, return_code
            )
            try:
                user = User.objects.get(id=user_id)
                initial_groups = ["General", "Commander", "Unaffiliated"]
                self.add_user_to_groups(user, initial_groups)
                log.debug("Added user to groups: %s" % initial_groups)
            except Exception as e:
                log.debug(e)

            try:
                c = data["commander"]
                u = UserProfile(
                    id=user_id,
                    user=User.objects.get(id=user_id),
                    commander_name=c["name"],
                    status=Status.objects.get(name="Unlinked"),
                )
                u.save()
                log.debug("UserProfile record added, id: [%s]", u.id)
                asset = 0
                for i, items in data["ships"].items():
                    asset = asset + int(items["value"]["total"])
                log.debug("Total ship assets: %s" % asset)
                asset += +int(c["credits"])
                log.debug("Total assets: %s" % asset)
                r = c["rank"]
                try:
                    cmdr_id = Commander.objects.get(
                        user=User.objects.get(id=user_id)
                    ).id
                    cmdr = Commander(
                        id=cmdr_id,
                        player_id=c["id"],
                        user=User.objects.get(id=user_id),
                        asset=asset,
                        credits=c["credits"],
                        loan=c["debt"],
                        combat=Rank.objects.get(
                            group_code="combat", assigned_id=r["combat"]
                        ),
                        cqc=Rank.objects.get(group_code="cqc", assigned_id=r["cqc"]),
                        empire=Rank.objects.get(
                            group_code="empire", assigned_id=r["empire"]
                        ),
                        explore=Rank.objects.get(
                            group_code="explore", assigned_id=r["explore"]
                        ),
                        federation=Rank.objects.get(
                            group_code="federation", assigned_id=r["federation"]
                        ),
                        trade=Rank.objects.get(
                            group_code="trade", assigned_id=r["trade"]
                        ),
                    )
                    log.debug("Commander object updated [%d]" % cmdr_id)
                except Commander.DoesNotExist:
                    cmdr = Commander(
                        player_id=c["id"],
                        user=User.objects.get(id=user_id),
                        asset=asset,
                        credits=c["credits"],
                        loan=c["debt"],
                        combat=Rank.objects.get(
                            group_code="combat", assigned_id=r["combat"]
                        ),
                        cqc=Rank.objects.get(group_code="cqc", assigned_id=r["cqc"]),
                        empire=Rank.objects.get(
                            group_code="empire", assigned_id=r["empire"]
                        ),
                        explore=Rank.objects.get(
                            group_code="explore", assigned_id=r["explore"]
                        ),
                        federation=Rank.objects.get(
                            group_code="federation", assigned_id=r["federation"]
                        ),
                        trade=Rank.objects.get(
                            group_code="trade", assigned_id=r["trade"]
                        ),
                    )
                    cmdr.save()

                    log.debug("Commander object created [%d]" % cmdr.id)
            except Exception as e:
                log.debug("do_profile: %s" % e)
                traceback.print_exc()
        time.sleep(1)
        return current + 1

    def do_shipyard(self, user_id, current, max_value):
        return_code, data = self.api.get_shipyard(user_id)
        if return_code["Status"] != 200:
            current = self.update_progress_bar(
                "Failed to Receive Shipyard Inventory", current, max_value, return_code
            )
            time.sleep(2)
        else:
            current = self.update_progress_bar(
                "Processing Shipyard Inventory", current, max_value, return_code
            )

        time.sleep(1)
        return current + 1

    def do_fleetcarrier(self, user_id, current, max_value):
        return_code, data = self.api.get_fleetcarrier(user_id)
        if return_code["Status"] != 200:
            current = self.update_progress_bar(
                "Failed to Receive Fleet Carrier Profile",
                current,
                max_value,
                return_code,
            )
            time.sleep(2)
        elif return_code["Status"] == 204:
            current = self.update_progress_bar(
                "No Fleet Carrier Profile Available", current, max_value, return_code
            )
            time.sleep(2)
        else:
            user = User.objects.get(id=user_id)
            self.add_user_to_groups(user, ["Fleet Carrier Owner"])
            current = self.update_progress_bar(
                "Processing Fleet Carrier Profile", current, max_value, return_code
            )

        time.sleep(1)
        return current + 1

    def do_community_goals(self, user_id, current, max_value):
        return_code, data = self.api.get_communitygoals(user_id)
        if return_code["Status"] != 200:
            current = self.update_progress_bar(
                "Failed to Receive Community Goals Information",
                current,
                max_value,
                return_code,
            )

            time.sleep(2)
        else:
            current = self.update_progress_bar(
                "Processing Community Goals Information",
                current,
                max_value,
                return_code,
            )
            for key, cg_group in data.items():
                for item in cg_group:
                    try:
                        cg_id = CommunityGoal.objects.get(id=item["id"]).id
                        cg = CommunityGoal(
                            id=cg_id,
                            title=item["title"],
                            expiry=item["expiry"],
                            market_name=item["market_name"],
                            starsystem_name=item["starsystem_name"],
                            activityType=item["activityType"],
                            target_qty=item["target_qty"],
                            qty=item["qty"],
                            objective=item["objective"],
                            news=item["news"],
                            bulletin=item["bulletin"],
                        )
                        cg.save()
                        log.debug("Community Goal object updated [%d]" % cg.id)
                    except CommunityGoal.DoesNotExist:
                        cg = CommunityGoal(
                            id=item["id"],
                            title=item["title"],
                            expiry=item["expiry"],
                            market_name=item["market_name"],
                            starsystem_name=item["starsystem_name"],
                            activityType=item["activityType"],
                            target_qty=item["target_qty"],
                            qty=item["qty"],
                            objective=item["objective"],
                            news=item["news"],
                            bulletin=item["bulletin"],
                        )
                        cg.save()
                        log.debug("Community Goal object created [%d]" % cg.id)
                    except Exception as e:
                        log.debug(e)

        time.sleep(0.5)
        return current + 1

    def do_cleanup(self, user_id, current, max_value):
        try:
            u = UserProfile.objects.get(id=user_id)
            u.is_setup_complete = True
            u.save()
        except Exception as e:
            log.debug(e)
        time.sleep(1)
        return current + 1
