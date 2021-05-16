import hashlib
import json
import logging
import os.path
from collections import defaultdict

import filetype
import requests
from django.apps import apps
from django.conf import settings
from django.contrib import messages
from django.utils.translation import gettext as _
from markdownify import markdownify as md

from edscc.commander.models import JournalLog, UserProfile
from edscc.core.models import GalnetNews

log = logging.getLogger(__name__)
BUF_SIZE = 64 * 1024  # read in 64k chunks


class BulkCreateManager(object):
    """
    This helper class keeps track of ORM objects to be created for multiple
    model classes, and automatically creates those objects with `bulk_create`
    when the number of objects accumulated for a given model class exceeds
    `chunk_size`.
    Upon completion of the loop that's `add()`ing objects, the developer must
    call `done()` to ensure the final set of objects is created for all models.
    """

    def __init__(self, chunk_size=100):
        self._create_queues = defaultdict(list)
        self.chunk_size = chunk_size

    def _commit(self, model_class):
        model_key = model_class._meta.label
        model_class.objects.bulk_create(self._create_queues[model_key])
        self._create_queues[model_key] = []

    def add(self, obj):
        """
        Add an object to the queue to be created, and call bulk_create if we
        have enough objs.
        """
        model_class = type(obj)
        model_key = model_class._meta.label
        self._create_queues[model_key].append(obj)
        if len(self._create_queues[model_key]) >= self.chunk_size:
            self._commit(model_class)

    def done(self):
        """
        Always call this upon completion to make sure the final partial chunk
        is saved.
        """
        for model_name, objs in self._create_queues.items():
            if len(objs) > 0:
                self._commit(apps.get_model(model_name))


def fetch_eddb_data(endpoint):
    eddb_url = getattr(settings, "EDDB_URL")
    endpoint_url = f"{eddb_url}{endpoint}"
    headers = {"Accept-Encoding": "gzip, deflate, sdch"}
    download_path = f"{settings.MEDIA_ROOT}/eddb/{endpoint}"
    r = None
    data = {}
    try:
        r = requests.get(endpoint_url, headers=headers)
        r.raise_for_status()
        status = {"Status": r.status_code}
        open(download_path, "wb").write(r.content)
    except requests.exceptions.Timeout as e:
        status = {"Status": r.status_code, "Error": "%s" % e}
    except requests.exceptions.ConnectionError as e:
        status = {"Status": r.status_code, "Error": "%s" % e}
    except requests.exceptions.HTTPError as e:
        status = {"Status": r.status_code, "Error": "%s" % e}
    except requests.exceptions.RequestException as e:
        status = {"Status": r.status_code, "Error": "%s" % e}
    return status, download_path


def fetch_galnet_news_feed():
    galnet_feed_url = getattr(settings, "GALNET_FEED_URL")
    r = None
    data = {}
    try:
        r = requests.get(galnet_feed_url, params={"_format": "json"})
        r.raise_for_status()
        status = {"Status": r.status_code}
        data = r.json()
    except requests.exceptions.Timeout as e:
        status = {"Status": r.status_code, "Error": "%s" % e}
    except requests.exceptions.ConnectionError as e:
        status = {"Status": r.status_code, "Error": "%s" % e}
    except requests.exceptions.HTTPError as e:
        status = {"Status": r.status_code, "Error": "%s" % e}
    except requests.exceptions.RequestException as e:
        status = {"Status": r.status_code, "Error": "%s" % e}
    return data, status


def update_galnet_news(request):
    (data, status) = fetch_galnet_news_feed()
    new_counter = 0
    if status["Status"] != 200:
        messages.error(request, _("Sync Failed: Unable to sync with Galnet Feed"))
        return
    qs = GalnetNews.objects.values_list("nid", flat=True)
    article_list = [i for i in qs]
    for article in data:
        if int(article["nid"]) not in article_list:
            a = GalnetNews(
                title=article["title"],
                body=md(article["body"]),
                nid=article["nid"],
                ed_date=article["date"],
                image=article["image"],
                slug=article["slug"],
            )
            a.save()
            new_counter += 1
    if new_counter > 1:
        messages.info(request, _("Sync completed: %d new articles added" % new_counter))
    elif new_counter:
        messages.info(request, _("Sync completed: One new article added"))
    else:
        messages.info(request, _("Sync completed: No new articles added"))


def evaluate_journal_log(user_id, file_path):  # noqa C901
    md5 = hashlib.md5()
    is_valid = False
    is_journal_file = False
    is_true_commander = None
    file_type = _("Unknown")
    game_start = ""
    game_end = ""

    try:
        user_profile = UserProfile.objects.get(user_id=user_id)
    except UserProfile.DoesNotExist:
        return {"is_valid": False, "message": _("Commander name not found")}

    if os.path.isfile(file_path):
        file_type = filetype.guess(file_path)
        if file_type is None:
            file_type = _("Unknown")
            try:
                with open(file_path, "r") as reader:
                    is_valid = True
                    file_type = "application/jsonl"
                    while True:
                        row = reader.readline()
                        if not row:
                            break
                        try:
                            data = json.loads(row)
                            game_end = data["timestamp"]
                            if data["event"] == "Fileheader":
                                is_journal_file = True
                                game_start = data["timestamp"]
                            if data["event"] == "LoadGame":
                                if data["Commander"] == user_profile.commander_name:
                                    is_true_commander = True
                                else:
                                    commander = data["Commander"]
                                    is_true_commander = False
                        except json.JSONDecodeError:
                            is_valid = False
                            file_type = _("Unknown")
            except Exception as e:
                log.debug(e)
            if is_valid:
                file_type = "application/jsonl"
        else:
            file_type = file_type.mime

        if not is_valid or not is_journal_file or not is_true_commander:
            if is_true_commander is False:
                message = "%s [%s]" % (_("Wrong Commander"), commander)
            else:
                message = _("Not a Journal file")
            data = {
                "is_valid": False,
                "file_type": file_type,
                "is_journal_file": is_journal_file,
                "is_true_commander": is_true_commander,
                "message": message,
            }
            return data

        with open(file_path, "rb") as f:
            while True:
                data = f.read(BUF_SIZE)
                if not data:
                    break
                md5.update(data)

        md5_hash = md5.hexdigest()
        log.debug("%s: %s" % (md5_hash, file_path))
        try:
            JournalLog.objects.get(user_id=user_id, file_hash=md5_hash)
            data = {
                "is_valid": False,
                "md5_hash": md5_hash,
                "message": _("Identical log was previously uploaded"),
            }
        except JournalLog.DoesNotExist:
            data = {
                "is_valid": True,
                "md5_hash": md5_hash,
                "game_start": game_start,
                "game_end": game_end,
            }
    else:
        data = {"is_valid": False, "message": _("Upload failed")}

    data["file_type"] = file_type

    return data
