import copy
import logging
import re
import time
from collections import defaultdict

import jsonlines
from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from ..commander.models import (
    ActivityCounter,
    Commander,
    CommanderInfo,
    EarningHistory,
    FactionActivity,
    JournalLog,
    Rank,
    UserProfile,
)
from ..core.models import EarningType, ParserLog
from ..core.session_tracker import SessionTrackerManager
from ..squadron.models import MinorFaction

log = logging.getLogger(__name__)


class DoesNotExist(Exception):
    """Exception raised for model record that does not exist"""

    def __init__(self, message):
        self.message = message


class FileNotFound(Exception):
    """Log file is not found"""

    def __init__(self, message):
        self.message = message


class ParseJournalLog:
    def __init__(self, user, session_type="journal"):
        self.file_path = ""
        self.event_callable = {
            "Fileheader": self.file_header,
            "LoadGame": self.load_game,
            "Bounty": self.bounty,
            "Cargo": self.commander_info,
            "CarrierStats": self.commander_info,
            "Docked": self.docked,
            "EngineerProgress": self.commander_info,
            "Materials": self.commander_info,
            "MultiSellExplorationData": self.multisell_exploration_data,
            "Progress": self.progress,
            "Rank": self.rank,
            "RedeemVoucher": self.redeem_voucher,
            "Reputation": self.commander_info,
            "SellExplorationData": None,
            "Shutdown": self.undocked,
            "Statistics": self.commander_info,
            "Undocked": self.undocked,
        }

        self.rank_dict = _rank_xref()
        self.earning_type = _earning_type_xref()
        self.activity_counter = ActivityCounter()
        self.log_date = None
        self.squadron_id = None
        self.parser_log = {}

        if isinstance(user, User):
            self.user_id = User.pk
            self.user = user
        elif type(user) is int:
            try:
                self.user = User.objects.get(id=user)
                self.user_id = self.user.id
            except User.DoesNotExist:
                raise DoesNotExist("User or User Profile %s not found" % user)
        else:
            raise TypeError("Not User instance or user id")

        self.user_profile = UserProfile.objects.get(user_id=self.user_id)
        self.squadron_id = self.user_profile.squadron_id
        self.session = SessionTrackerManager(
            user=self.user, session_identifier=session_type
        )
        parser_log = ParserLog.objects.filter(user_id=self.user_id)
        if parser_log:
            for row in parser_log:
                self.parser_log[row.event] = row.counter
        log.debug("Tracking session %s" % self.session.hash_key)
        log.debug(self.parser_log)

    @transaction.atomic
    def save_parser_log(self):
        event_list = ParserLog.objects.filter(user_id=self.user_id)
        parser_log = copy.deepcopy(self.parser_log)
        for row in event_list:
            row.counter = parser_log[row.event]
            del parser_log[row.event]
            row.save()
        for key, value in parser_log.items():
            ParserLog(event=key, counter=value, user_id=self.user_id).save()

    def get_localized_string(self, data, key):
        original_string = data[key] if key in data else ""
        match = re.match(r"^[\$](.)*", original_string)
        localised_key = "%s_Localised" % key
        if match is not None:
            return data[localised_key] if localised_key in data else original_string
        return original_string

    def parse_event(self, event):
        if event["event"] in self.event_callable:
            self.event_callable[event["event"]](event)
        else:
            if event["event"] in self.parser_log:
                self.parser_log[event["event"]] += 1
            else:
                self.parser_log[event["event"]] = 1

    def file_header(self, data):
        log.debug("in file_header")
        self.log_date = parse_datetime(data["timestamp"]).strftime("%Y-%m-%d")
        try:
            self.activity_counter = ActivityCounter.objects.get(
                user_id=self.user_id, activity_date=self.log_date
            )
            log.debug("activity_counter record loaded")
        except ActivityCounter.DoesNotExist:
            self.activity_counter = ActivityCounter(
                user_id=self.user_id, activity_date=self.log_date
            )
            self.activity_counter.save()
            log.debug("activity_counter record created")

    def load_game(self, data):
        try:
            Commander.objects.filter(user_id=self.user_id).update(
                credits=data["Credits"], loan=data["Loan"]
            )
        except Commander.DoesNotExist as e:
            log.debug("No Commander record found: %s" % e)
            return
        except Exception as e:
            log.debug(("Other error: %s" % e))
            return

    def docked(self, data):
        self.session.set_attr("station_name", data["StationName"])
        self.session.set_attr("market_id", data["MarketID"])
        self.session.set_attr("station_faction", data["StationFaction"]["Name"])

    def undocked(self, data):
        self.session.set_attr("station_name", None)
        self.session.set_attr("market_id", None)
        self.session.set_attr("station_faction", None)

    def rank(self, data):
        try:
            Commander.objects.filter(user_id=self.user_id).update(
                combat_id=self.rank_dict["combat"][data["Combat"]],
                trade_id=self.rank_dict["trade"][data["Trade"]],
                explore_id=self.rank_dict["explore"][data["Explore"]],
                cqc_id=self.rank_dict["cqc"][data["CQC"]],
                federation_id=self.rank_dict["federation"][data["Federation"]],
                empire_id=self.rank_dict["empire"][data["Empire"]],
            )
            if "Mercenary" in data:
                Commander.objects.filter(user_id=self.user_id).update(
                    mercenary_id=self.rank_dict["mercenary"][data["Mercenary"]],
                    exobiologist_id=self.rank_dict["exobiologist"][
                        data["Exobiologist"]
                    ],
                )
            self.commander_info(data)
        except Commander.DoesNotExist as e:
            log.debug("No Commander record found: %s" % e)
            return
        except Exception as e:
            log.debug(("Other error: %s" % e))
            return

    def progress(self, data):
        try:
            Commander.objects.filter(user_id=self.user_id).update(
                combat_progress=data["Combat"],
                trade_progress=data["Trade"],
                explore_progress=data["Explore"],
                empire_progress=data["Empire"],
                federation_progress=data["Federation"],
            )
            if "Mercenary" in data:
                Commander.objects.filter(user_id=self.user_id).update(
                    mercenary_progress=data["Mercenary"],
                    exobiologist_progress=data["Exobiologist"],
                )
            self.commander_info(data)
        except Commander.DoesNotExist as e:
            log.debug("No Commander record found: %s" % e)
            return
        except Exception as e:
            log.debug(("Other error: %s" % e))
            return

    def commander_info(self, data):
        try:
            cmdr_info = CommanderInfo.objects.get(
                event=data["event"], user_id=self.user_id
            )
            cmdr_info.content = data
            cmdr_info.save()
        except CommanderInfo.DoesNotExist:
            CommanderInfo(
                event=data["event"], content=data, user_id=self.user_id
            ).save()

    @transaction.atomic
    def bounty(self, data):
        log.debug("in bounty")
        reward = data["TotalReward"] if "TotalReward" in data else data["Reward"]
        target_faction = (
            self.get_localized_string(data, "VictimFaction")
            if "VictimFaction" in data
            else ""
        )
        self.activity_counter.add_by_attr("bounties_claimed", 1)
        if "Rewards" in data:
            for row in data["Rewards"]:
                minor_faction = (
                    self.get_localized_string(row, "Faction")
                    if "Faction" in row
                    else ""
                )
                self.add_minor_faction(
                    data["event"].lower(),
                    parse_datetime(data["timestamp"]).strftime("%Y-%m-%d"),
                    row["Reward"],
                    minor_faction,
                    target_faction,
                )
        else:
            log.debug("in reward")
            minor_faction = (
                self.get_localized_string(data, "Faction") if "Faction" in data else ""
            )
            self.add_minor_faction(
                data["event"].lower(),
                parse_datetime(data["timestamp"]).strftime("%Y-%m-%d"),
                reward,
                minor_faction,
                target_faction,
            )

    @transaction.atomic
    def redeem_voucher(self, data):
        log.debug("in redeem_voucher")
        earning_type = data["Type"].lower()
        if "Factions" in data:
            for row in data["Factions"]:
                minor_faction = (
                    self.get_localized_string(row, "Faction")
                    if "Faction" in row
                    else ""
                )
                minor_faction_obj = self.find_minor_faction(minor_faction)
                EarningHistory(
                    user_id=self.user_id,
                    earned_on=parse_datetime(data["timestamp"]),
                    reward=row["Amount"],
                    crew_wage=0,
                    earning_type_id=self.earning_type[earning_type],
                    minor_faction=minor_faction_obj,
                ).save()
        elif "Faction" in data:
            minor_faction_obj = self.find_minor_faction(
                self.get_localized_string(data, "Faction")
            )
            EarningHistory(
                user_id=self.user_id,
                earned_on=parse_datetime(data["timestamp"]),
                reward=data["Amount"],
                crew_wage=0,
                earning_type_id=self.earning_type[earning_type],
                minor_faction=minor_faction_obj,
            ).save()

    @transaction.atomic
    def multisell_exploration_data(self, data):
        num_systems = len(data["Discovered"])
        num_bodies = 0
        for system in data["Discovered"]:
            num_bodies += system["NumBodies"]
        minor_faction_obj = self.find_minor_faction(
            self.session.get_attr("station_faction")
        )
        station_name = self.session.get_attr("station_name")
        crew_wage = data["BaseValue"] + data["Bonus"] - data["TotalEarnings"]
        EarningHistory(
            user_id=self.user_id,
            earned_on=parse_datetime(data["timestamp"]),
            reward=data["TotalEarnings"],
            crew_wage=crew_wage,
            earning_type_id=self.earning_type["explorationdata"],
            minor_faction=minor_faction_obj,
            notes=station_name,
        ).save()
        self.activity_counter.add_by_attr("bodies_found", num_bodies)
        self.activity_counter.add_by_attr("systems_scanned", num_systems)

    def find_minor_faction(self, minor_faction):
        minor_faction = minor_faction.strip()
        if minor_faction == "":
            return None
        try:
            minor_faction_obj = MinorFaction.objects.get(name=minor_faction)
            log.debug("found minor faction: %s" % minor_faction)
        except MinorFaction.DoesNotExist:
            minor_faction_obj = MinorFaction(
                name=minor_faction, player_faction=False, eddb_id=None
            ).save()
            log.debug("created minor faction: %s" % minor_faction)
        return minor_faction_obj

    def add_minor_faction(
        self, earning_type, earned_on, reward, minor_faction, target_faction
    ):
        minor_faction_obj = self.find_minor_faction(minor_faction)
        target_faction_obj = self.find_minor_faction(target_faction)
        FactionActivity(
            minor_faction=minor_faction_obj,
            target_minor_faction=target_faction_obj,
            earning_type_id=self.earning_type[earning_type],
            earned_on=earned_on,
            reward=reward,
            user_id=self.user_id,
        ).save()


class ParseJournalLogFile(ParseJournalLog):
    def __init__(self, user):
        super().__init__(user)

    def start(self):
        queue = JournalLog.objects.filter(
            progress_code="Q", user_id=self.user_id
        ).order_by("game_start")
        for log_obj in queue:
            tic = time.perf_counter()
            file_path = settings.MEDIA_ROOT + "/" + str(log_obj.file)
            log.debug("Parsing: %s" % file_path)
            log.debug("Start: %s End: %s" % (log_obj.game_start, log_obj.game_end))
            log_obj.time_started = timezone.now()
            log_obj.progress_code = "P"
            log_obj.progress_percent = 0
            log_obj.save()
            try:
                i = 0
                with jsonlines.open(file_path) as reader:
                    for row in reader:
                        self.parse_event(row)
                        i += 1
                log.debug("%d rows processed" % i)
                self.activity_counter.save()
                self.save_parser_log()
                log.debug(self.parser_log)
            except jsonlines.Error as e:
                log.debug(e)
                raise FileNotFound("%s" % file_path)
            toc = time.perf_counter()
            log_obj.parser_time = "{:0.5f}".format(toc - tic)
            log_obj.rows_processed = i
            log_obj.progress_code = "C"
            log_obj.progress_percent = 100
            log_obj.save()


def _rank_xref():
    rank_dict = defaultdict(dict)
    rank_qs = Rank.objects.all()
    for row in rank_qs:
        rank_dict[row.group_code][row.assigned_id] = row.id

    return rank_dict


def _earning_type_xref():
    earning_type_dict = defaultdict(dict)
    earning_type_qs = EarningType.objects.all()
    for row in earning_type_qs:
        earning_type_dict[row.name.lower()] = row.id

    return earning_type_dict
