import copy
import json
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
from semantic_version import Version

from ..commander.models import (
    ActivityCounter,
    Commander,
    CommanderInfo,
    Crime,
    CrimeType,
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


class EDVersion(Version):
    def __init__(self, version_string=None, **kwargs):
        self.version_xref = {
            "April Update EDH": "3.4.0",
            "April Update Patch 1 EDH": "3.4.1",
            "April Update Patch 2 EDH": "3.4.2",
            "January Update": "3.6.0",
            "January Update - Patch 1": "3.6.1",
            "January Update - Patch 2": "3.6.2",
            "Fleet Carriers Update": "3.7.0",
            "Fleet Carriers Update - Patch 1": "3.7.1",
            "Fleet Carriers Update - Patch 2": "3.7.2",
            "Fleet Carriers Update - Patch 3": "3.7.3",
            "Fleet Carriers Update - Patch 4": "3.7.4",
            "Fleet Carriers Update - Patch 5": "3.7.5",
            "Fleet Carriers Update - Patch 6": "3.7.6",
            "Fleet Carriers Update - Patch 7": "3.7.7",
            "Fleet Carriers Update - Patch 8": "3.7.8",
            "Fleet Carriers Update - Patch 9": "3.7.9",
            "Fleet Carriers Update - Patch 10": "3.7.10",
            "Fleet Carriers Update - Patch 11": "3.7.11",
            "Fleet Carriers Update - Patch 12": "3.7.12",
        }

        if version_string:
            v = version_string.split(".", 4)
            if v[0].isdigit():
                for i in range(4 - len(v)):
                    v.append("0")
                v = [str(int(re.sub("[^0-9]", "", i))) for i in v]
                version_string = ".".join(v[0:3])
            else:
                if version_string in self.version_xref:
                    version_string = self.version_xref[version_string]
                else:
                    version_string = "0.0.0"
            super().__init__(version_string=version_string)
        else:
            super().__init__(**kwargs)


class ParseJournalLog:
    def __init__(self, user, session_type="journal"):
        self.file_path = ""
        self.event_callable = {
            "Fileheader": self.file_header,
            "LoadGame": self.load_game,
            "Bounty": self.bounty,
            "Cargo": self.commander_info,
            "CarrierStats": self.commander_info,
            "CommunityGoalReward": self.community_goal,
            "CommitCrime": self.commit_crime,
            "Docked": self.docked,
            "EngineerProgress": self.commander_info,
            "FactionKillBond": self.faction_kill_bond,
            "MarketBuy": self.market_buy,
            "MarketSell": self.market_sell,
            "Materials": self.commander_info,
            "MiningRefined": self.mining_refined,
            "MissionCompleted": self.mission_completed,
            "MultiSellExplorationData": self.multisell_exploration_data,
            "Progress": self.progress,
            "Rank": self.rank,
            "RedeemVoucher": self.redeem_voucher,
            "Reputation": self.commander_info,
            "SAAScanComplete": self.saa_scan_complete,
            "SellExplorationData": self.sell_exploration_data,
            "Shutdown": self.undocked,
            "Statistics": self.commander_info,
            "Undocked": self.undocked,
        }

        self.rank_dict = _rank_xref()
        self.earning_type = _earning_type_xref()
        self.crime_type = _crime_type_xref()
        self.activity_counter = ActivityCounter()
        self.log_date = None
        self.squadron_id = None
        self.parser_log = {}
        self.log_version = None

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

    @transaction.atomic
    def save_parser_log(self):
        event_list = ParserLog.objects.filter(user_id=self.user_id).distinct()
        parser_log = copy.deepcopy(self.parser_log)
        for row in event_list:
            if row.event in parser_log:
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

    def to_do(self, data):
        pass

    def file_header(self, data):
        self.log_date = parse_datetime(data["timestamp"]).strftime("%Y-%m-%d")
        try:
            self.activity_counter = ActivityCounter.objects.get(
                user_id=self.user_id, activity_date=self.log_date
            )
        except ActivityCounter.DoesNotExist:
            self.activity_counter = ActivityCounter(
                user_id=self.user_id, activity_date=self.log_date
            )
            self.activity_counter.save()
        self.log_version = EDVersion(data["gameversion"])

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
        if self.log_version >= EDVersion("3.0.0"):
            self.session.set_attr("market_id", data["MarketID"])
        if self.log_version < EDVersion("3.3.3"):
            if "StationFaction" in data:
                self.session.set_attr("station_faction", data["StationFaction"])
            elif "Faction" in data:
                self.session.set_attr("station_faction", data["Faction"])
        else:
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
            if "Soldier" in data:
                Commander.objects.filter(user_id=self.user_id).update(
                    mercenary_id=self.rank_dict["mercenary"][data["Soldier"]],
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
    def faction_kill_bond(self, data):
        reward = data["TotalReward"] if "TotalReward" in data else data["Reward"]
        minor_faction = (
            self.get_localized_string(data, "AwardingFaction")
            if "AwardingFaction" in data
            else ""
        )
        target_faction = (
            self.get_localized_string(data, "VictimFaction")
            if "VictimFaction" in data
            else ""
        )
        minor_faction_obj = self.find_minor_faction(minor_faction)
        EarningHistory(
            user_id=self.user_id,
            earned_on=parse_datetime(data["timestamp"]),
            reward=reward,
            crew_wage=0,
            earning_type_id=self.earning_type[data["event"].lower()],
            minor_faction=minor_faction_obj,
        ).save()
        self.activity_counter.add_by_attr("bounties_claimed", 1)
        self.add_minor_faction(
            data["event"].lower(),
            parse_datetime(data["timestamp"]).strftime("%Y-%m-%d"),
            reward,
            minor_faction,
            target_faction,
        )

    @transaction.atomic
    def redeem_voucher(self, data):
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

    @transaction.atomic
    def sell_exploration_data(self, data):
        num_systems = len(data["Systems"])
        num_bodies = len(data["Discovered"])
        minor_faction_obj = self.find_minor_faction(
            self.session.get_attr("station_faction")
        )
        station_name = self.session.get_attr("station_name")
        if "TotalEarnings" in data:
            reward = data["TotalEarnings"]
            crew_wage = data["BaseValue"] + data["Bonus"] - data["TotalEarnings"]
        else:
            reward = data["BaseValue"] + data["Bonus"]
            crew_wage = 0
        EarningHistory(
            user_id=self.user_id,
            earned_on=parse_datetime(data["timestamp"]),
            reward=reward,
            crew_wage=crew_wage,
            earning_type_id=self.earning_type["explorationdata"],
            minor_faction=minor_faction_obj,
            notes=station_name,
        ).save()
        self.activity_counter.add_by_attr("bodies_found", num_bodies)
        self.activity_counter.add_by_attr("systems_scanned", num_systems)

    @transaction.atomic
    def saa_scan_complete(self, data):
        efficiency = 1 if data["ProbesUsed"] <= data["EfficiencyTarget"] else 0
        self.activity_counter.add_by_attr("saa_scan_completed", 1)
        self.activity_counter.add_by_attr("efficiency_achieved", efficiency)

    @transaction.atomic
    def market_buy(self, data):
        station_name = self.session.get_attr("station_name")
        minor_faction_obj = self.find_minor_faction(
            self.session.get_attr("station_faction")
        )
        EarningHistory(
            user_id=self.user_id,
            earned_on=parse_datetime(data["timestamp"]),
            reward=int(data["TotalCost"]) * -1,
            crew_wage=0,
            earning_type_id=self.earning_type[data["event"].lower()],
            minor_faction=minor_faction_obj,
            notes=station_name,
        ).save()
        self.activity_counter.add_by_attr("market_buy", data["Count"])

    @transaction.atomic
    def market_sell(self, data):
        station_name = self.session.get_attr("station_name")
        minor_faction_obj = self.find_minor_faction(
            self.session.get_attr("station_faction")
        )
        crew_wage = data["TotalSale"] - (data["Count"] * data["SellPrice"])
        EarningHistory(
            user_id=self.user_id,
            earned_on=parse_datetime(data["timestamp"]),
            reward=data["TotalSale"],
            crew_wage=crew_wage,
            earning_type_id=self.earning_type[data["event"].lower()],
            minor_faction=minor_faction_obj,
            notes=station_name,
        ).save()
        self.activity_counter.add_by_attr("market_sell", data["Count"])
        if "IllegalGoods" in data:
            self.activity_counter.add_by_attr("illegal_goods", data["Count"])
        if "StolenGoods" in data:
            self.activity_counter.add_by_attr("stolen_goods", data["Count"])
        if "BlackMarket" in data:
            self.activity_counter.add_by_attr("black_market", data["Count"])

    @transaction.atomic
    def community_goal(self, data):
        station_name = self.session.get_attr("station_name")
        minor_faction_obj = self.find_minor_faction(
            self.session.get_attr("station_faction")
        )
        EarningHistory(
            user_id=self.user_id,
            earned_on=parse_datetime(data["timestamp"]),
            reward=data["Reward"],
            crew_wage=0,
            earning_type_id=self.earning_type[data["event"].lower()],
            minor_faction=minor_faction_obj,
            notes=station_name,
        ).save()
        self.activity_counter.add_by_attr("cg_participated", 1)

    @transaction.atomic
    def mining_refined(self, data):
        self.activity_counter.add_by_attr("mining_refined", 1)

    @transaction.atomic
    def mission_completed(self, data):
        old_name = self.get_localized_string(data, "Name") if "Name" in data else ""
        pieces = old_name.split("_")
        name = "_".join(pieces[0:2])
        notes = ""

        if name.lower() in self.earning_type:
            earning_type_id = self.earning_type[name.lower()]
        else:
            earning_type_id = self.earning_type["missioncompleted"]
            notes = name
            name = "missioncompleted"

        log.debug("old_name=%s, name=%s, notes=%s" % (old_name, name, notes))

        minor_faction = (
            self.get_localized_string(data, "Faction") if "Faction" in data else ""
        )
        target_faction = (
            self.get_localized_string(data, "TargetFaction")
            if "TargetFaction" in data
            else ""
        )

        minor_faction_obj = self.find_minor_faction(
            self.get_localized_string(data, "Faction") if "Faction" in data else ""
        )

        if "Reward" in data:
            EarningHistory(
                user_id=self.user_id,
                earned_on=parse_datetime(data["timestamp"]),
                reward=data["Reward"],
                crew_wage=0,
                earning_type_id=earning_type_id,
                minor_faction=minor_faction_obj,
                notes=notes,
            ).save()
            self.add_minor_faction(
                name,
                parse_datetime(data["timestamp"]).strftime("%Y-%m-%d"),
                data["Reward"],
                minor_faction,
                target_faction,
            )
            self.activity_counter.add_by_attr("missions_completed", 1)
        elif "Donation" in data or "Donated" in data:
            donation = data["Donated"] if "Donated" in data else data["Donation"]
            EarningHistory(
                user_id=self.user_id,
                earned_on=parse_datetime(data["timestamp"]),
                reward=int(donation) * -1,
                crew_wage=0,
                earning_type_id=earning_type_id,
                minor_faction=minor_faction_obj,
                notes=notes,
            ).save()
            self.add_minor_faction(
                name,
                parse_datetime(data["timestamp"]).strftime("%Y-%m-%d"),
                int(donation) * -1,
                minor_faction,
                target_faction,
            )
            self.activity_counter.add_by_attr("donations", 1)

    @transaction.atomic
    def commit_crime(self, data):
        log.debug("in commit_crime")
        log.debug("data: %s" % data)
        self.activity_counter.add_by_attr("crimes_committed", 1)
        crime_committed = data["CrimeType"].lower() if "CrimeType" in data else ""

        if crime_committed in self.crime_type:
            crime_type_id = self.crime_type[crime_committed]
            notes = None
        else:
            crime_type_id = self.crime_type["other"]
            notes = data["CrimeType"]

        minor_faction_obj = self.find_minor_faction(
            self.get_localized_string(data, "Faction") if "Faction" in data else ""
        )
        victim = self.get_localized_string(data, "Victim") if "Victim" in data else ""
        Crime(
            user_id=self.user_id,
            committed_on=parse_datetime(data["timestamp"]),
            victim=victim,
            fine=data["Fine"] if "Fine" in data else "0",
            bounty=data["Bounty"] if "Bounty" in data else "0",
            minor_faction=minor_faction_obj,
            crime_type_id=crime_type_id,
            squadron_id=self.squadron_id,
            notes=notes,
        ).save()

    def find_minor_faction(self, minor_faction):
        minor_faction = minor_faction.strip()
        if minor_faction == "":
            return None
        try:
            minor_faction_obj = MinorFaction.objects.get(name=minor_faction)
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
        log.debug(
            "minor_faction=%s, target_minor_faction=%s, earning_type=%s, earning_type_id=%s, earned_on=%s, reward=%s, user_id=%s"
            % (
                minor_faction_obj,
                target_faction_obj,
                earning_type,
                self.earning_type[earning_type.lower()],
                earned_on,
                reward,
                self.user_id,
            )
        )
        FactionActivity(
            minor_faction=minor_faction_obj,
            target_minor_faction=target_faction_obj,
            earning_type_id=self.earning_type[earning_type.lower()],
            earned_on=earned_on,
            reward=reward,
            user_id=self.user_id,
        ).save()


class ParseJournalLogFile(ParseJournalLog):
    def __init__(self, user):
        super().__init__(user)

    def start(self, num_logs_process=-1):
        queue = (
            JournalLog.objects.filter(progress_code="Q", user_id=self.user_id)
            .exclude(game_start__isnull=True)
            .order_by("game_start")
        )
        logs_processed = 0
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
            except jsonlines.Error as e:
                log.debug(e)
                raise FileNotFound("%s" % file_path)
            toc = time.perf_counter()
            log_obj.parser_time = "{:0.5f}".format(toc - tic)
            log_obj.rows_processed = i
            log_obj.progress_code = "C"
            log_obj.progress_percent = 100
            log_obj.save()
            time.sleep(0.55)
            logs_processed += 1
            if logs_processed >= num_logs_process:
                count_remaining = (
                    JournalLog.objects.filter(progress_code="Q", user_id=self.user_id)
                    .exclude(game_start__isnull=True)
                    .count()
                )
                return count_remaining
        return 0


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


def _crime_type_xref():
    crime_type_dict = defaultdict(dict)
    crime_type_qs = CrimeType.objects.all()
    for row in crime_type_qs:
        crime_type_dict[row.name.lower()] = row.id
        if row.alias:
            alias_list = json.loads(row.alias)
            for alias in alias_list:
                crime_type_dict[alias.lower()] = row.id

    return crime_type_dict
