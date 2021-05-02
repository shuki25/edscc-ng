import logging
from collections import defaultdict

import jsonlines
from django.conf import settings
from django.contrib.auth.models import User

from ..commander.models import Commander, CommanderInfo, JournalLog, Rank

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

    def __init__(self, user):
        self.file_path = ""
        self.event_callable = {
            'Rank': self.rank,
            'Statistics': self.commander_info,
            'EngineerProgress': self.commander_info,
            'Reputation': self.commander_info,
            'CarrierStats': self.commander_info,
            'Materials': self.commander_info,
            'Cargo': self.commander_info,
            'Progress': self.progress,
        }

        self.rank_dict = _rank_xref()

        if isinstance(user, User):
            self.user_id = User.pk
            self.user = user
        elif type(user) is int:
            try:
                self.user = User.objects.get(id=user)
                self.user_id = self.user.id
            except User.DoesNotExist:
                raise DoesNotExist('User %s not found' % user)
        else:
            raise TypeError('Not User instance or user id')

    def parse_event(self, event):
        if event['event'] in self.event_callable:
            self.event_callable[event['event']](event)

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
                    exobiologist_id=self.rank_dict["exobiologist"][data["Exobiologist"]],
                )
            self.commander_info(data)
        except Commander.DoesNotExist as e:
            log.debug('No Commander record found: %s' % e)
            return
        except Exception as e:
            log.debug(('Other error: %s' % e))
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
            log.debug('No Commander record found: %s' % e)
            return
        except Exception as e:
            log.debug(('Other error: %s' % e))
            return

    def commander_info(self, data):
        try:
            cmdr_info = CommanderInfo.objects.get(event=data['event'], user_id=self.user_id)
            cmdr_info.content = data
            cmdr_info.save()
        except CommanderInfo.DoesNotExist:
            CommanderInfo(event=data['event'], content=data, user_id=self.user_id).save()


class ParseJournalLogFile(ParseJournalLog):
    def __init__(self, user):
        super().__init__(user)

    def start(self):
        queue = JournalLog.objects.filter(progress_code='Q', user_id=self.user_id).order_by('game_start')
        for log_obj in queue:
            file_path = settings.MEDIA_ROOT + "/" + str(log_obj.file)
            log.debug('Parsing: %s' % file_path)
            log.debug('Start: %s End: %s' % (log_obj.game_start, log_obj.game_end))
            try:
                with jsonlines.open(file_path) as reader:
                    for row in reader:
                        self.parse_event(row)
            except jsonlines.Error as e:
                log.debug(e)
                raise FileNotFound('%s' % file_path)


def _rank_xref():
    rank_dict = defaultdict(dict)
    rank_qs = Rank.objects.all()
    for row in rank_qs:
        rank_dict[row.group_code][row.assigned_id] = row.id

    return rank_dict
