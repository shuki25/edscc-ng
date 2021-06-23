import hashlib
import json
import logging
import os.path
from collections import defaultdict
from datetime import datetime
from urllib.parse import parse_qs, urlencode, urlparse

import filetype
import requests
from django.apps import apps
from django.conf import settings
from django.contrib import messages
from django.utils.translation import gettext as _
from markdownify import markdownify as md
from pytz import utc

from edscc.commander.models import JournalLog, UserProfile
from edscc.core.models import GalnetNews

log = logging.getLogger(__name__)
BUF_SIZE = 64 * 1024  # read in 64k chunks

AVAILABLE_LANGUAGE = {
    "en": "en-GB",
    "fr": "fr-FR",
    "de": "de-DE",
    "pt": "pt-BR",
    "ru": "ru-RU",
    "es": "es-ES",
}


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
    try:
        r = requests.get(endpoint_url, headers=headers)
        r.raise_for_status()
        status = {"Status": r.status_code}
        if r.status_code == 200:
            open(download_path, "wb").write(r.content)
    except requests.exceptions.Timeout as e:
        status = {"Status": "408", "Error": "%s" % repr(e)}
    except requests.exceptions.ConnectionError as e:
        status = {"Status": "504", "Error": "%s" % repr(e)}
    except requests.exceptions.HTTPError as e:
        status = {"Status": "500", "Error": "%s" % repr(e)}
    except requests.exceptions.RequestException as e:
        status = {"Status": "500", "Error": "%s" % repr(e)}
    if status["Status"] != 200:
        log.debug(status)
    return status, download_path


def fetch_galnet_news_feed(offset=0, limit=50, lang_code="en-GB"):
    galnet_feed_url_template = getattr(settings, "GALNET_FEED_URL")
    galnet_feed_url = galnet_feed_url_template.format(lang_code=lang_code)
    data = {}
    try:
        r = requests.get(
            galnet_feed_url,
            params={
                "page[offset]": offset,
                "page[limit]": limit,
                "sort": "-published_at",
            },
        )
        r.raise_for_status()
        status = {"Status": r.status_code}
        if r.status_code == 200:
            data = r.json()
        else:
            data = {}
    except requests.exceptions.Timeout as e:
        status = {"Status": "408", "Error": "%s" % repr(e)}
    except requests.exceptions.ConnectionError as e:
        status = {"Status": "504", "Error": "%s" % repr(e)}
    except requests.exceptions.HTTPError as e:
        status = {"Status": "500", "Error": "%s" % repr(e)}
    except requests.exceptions.RequestException as e:
        status = {"Status": "500", "Error": "%s" % repr(e)}
    if status["Status"] != 200:
        log.debug(status)
    return data, status


def update_galnet_news(request):
    new_counter = 0

    for lang_code, lang_country_code in AVAILABLE_LANGUAGE.items():
        is_done = False
        offset = 0
        limit = 100
        while is_done is False:
            (data, status) = fetch_galnet_news_feed(
                offset=offset, limit=limit, lang_code=lang_country_code
            )
            if status["Status"] != 200:
                messages.error(
                    request, _("Sync Failed: Unable to sync with Galnet Feed")
                )
                messages.error(
                    request, "[%s]: %s" % (status["Status"], status["Error"])
                )
                break
            try:
                content_lang_code = data["data"][0]["attributes"]["langcode"]
                log.debug(
                    f"Request language [{lang_code}], content language [{content_lang_code}]"
                )
            except Exception as e:
                log.debug(f"Error: {e}")
                content_lang_code = "en"
            qs = GalnetNews.objects.filter(lang_code=content_lang_code).values_list(
                "nid", flat=True
            )
            article_list = [i for i in qs]
            for row in data["data"]:
                if "attributes" in row:
                    article = row["attributes"]
                    if int(article["drupal_internal__nid"]) not in article_list:
                        a = GalnetNews(
                            title=article["title"],
                            body=md(article["body"]["processed"]),
                            lang_code=article["langcode"],
                            nid=article["drupal_internal__nid"],
                            galnet_date=article["field_galnet_date"],
                            image=article["field_galnet_image"],
                            slug=article["field_slug"],
                            created_at=article["created"],
                        )
                        a.save()
                        new_counter += 1
            if "next" in data["links"]:
                qs = urlparse(data["links"]["next"]["href"])
                o = parse_qs(qs.query)
                log.debug(o)
                offset = o["page[offset]"][0]
                limit = o["page[limit]"][0]
            else:
                is_done = True
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
                    is_beta_file = False
                    game_version = None
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
                                if (
                                    "beta" in data["gameversion"].lower()
                                    or "alpha" in data["gameversion"].lower()
                                ):
                                    is_journal_file = False
                                    is_beta_file = True
                                    game_version = data["gameversion"]
                                game_start = data["timestamp"]
                            if data["event"] == "LoadGame":
                                if (
                                    data["Commander"].lower()
                                    == user_profile.commander_name.lower()
                                ):
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

        if not is_valid or not is_journal_file or not is_true_commander or is_beta_file:
            if is_true_commander is False:
                message = "%s [%s]" % (_("Wrong Commander"), commander)
            elif is_beta_file:
                message = "%s: %s" % (_("Alpha/beta file"), game_version)
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


def to_snake_case(text):
    text = text.title().replace(" ", "")
    return "".join(["_" + i.lower() if i.isupper() else i for i in text]).lstrip("_")


def hex2text(text):
    return bytes.fromhex(text).decode("utf-8")


def timezone_aware(text):
    date_format = "%Y-%m-%d %H:%M:%S"
    return utc.localize(datetime.strptime(text, date_format))


def merge_dicts(*dict_args):
    """
    Given any number of dictionaries, shallow copy and merge into a new dict,
    precedence goes to key-value pairs in latter dictionaries.
    """
    result = {}
    for dictionary in dict_args:
        result.update(dictionary)
    return result


class Paginator:
    def __init__(self, **kwargs):
        exclude_list = ["offset", "limit", "count", "width"]
        self.offset = int(kwargs["offset"] if "offset" in kwargs else 0)
        self.limit = int(kwargs["limit"] if "limit" in kwargs else 25)
        self.count = int(kwargs["count"] if "count" in kwargs else 0)
        self.width = int(kwargs["width"] if "width" in kwargs else 7)
        self.kwargs = {}

        for key, value in kwargs.items():
            if key not in exclude_list:
                self.kwargs[key] = value

    def has_previous(self):
        return self.offset - self.limit >= 0

    def has_next(self):
        return self.offset + self.limit < self.count

    def is_current_page(self, page_num):
        return self.current_page() == page_num

    def num_pages(self):
        return round((self.count / self.limit) + 0.5)

    def current_page(self):
        return int(self.offset / self.limit) + 1

    def calculate_offset(self, page_num):
        return (page_num - 1) * self.limit

    def num_items(self, page_num):
        if page_num < self.num_pages():
            return self.limit
        else:
            offset = self.calculate_offset(self.num_pages())
            return self.count - offset

    def urlencode(self, params, include_list):
        filtered_params = {}
        for i in include_list:
            if i in params:
                filtered_params[i] = params[i]
        return urlencode(filtered_params)

    def add_kwargs(self, original, extra_data):
        for key, value in extra_data.items():
            if value:
                original[key] = value
        return original

    def next_page(self):
        page = self.current_page() + 1
        item = {
            "offset": self.calculate_offset(page),
            "limit": self.limit,
        }
        item = self.add_kwargs(item, self.kwargs)
        return urlencode(item)

    def previous_page(self):
        page = self.current_page() - 1
        item = {
            "offset": self.calculate_offset(page),
            "limit": self.limit,
        }
        item = self.add_kwargs(item, self.kwargs)
        return urlencode(item)

    def pagination_list(self):
        pagination = []
        include_list = ["keyword", "platform", "offset", "limit"]
        cur_page = self.current_page()
        num_pages = self.num_pages()
        half_width = int(self.width / 2)
        print(
            "cur_page=%s, num_pages=%s, half_width=%s"
            % (cur_page, num_pages, half_width)
        )
        if num_pages < self.width or cur_page < self.width:
            print("In block 1")
            max_pages = num_pages if num_pages <= self.width else self.width
            for i in range(1, max_pages + 1):
                item = {
                    "num": i,
                    "offset": self.calculate_offset(i),
                    "limit": self.limit,
                    "is_current": self.is_current_page(i),
                }
                item = self.add_kwargs(item, self.kwargs)
                item["params"] = self.urlencode(item, include_list)
                pagination.append(item)
            if num_pages > self.width:
                item = {"num": "..."}
                pagination.append(item)
                item = {
                    "num": num_pages,
                    "offset": self.calculate_offset(num_pages),
                    "limit": self.limit,
                    "is_current": False,
                }
                item = self.add_kwargs(item, self.kwargs)
                item["params"] = self.urlencode(item, include_list)
                pagination.append(item)
        else:
            print("In block 2")
            start_page = self.current_page() - half_width
            end_page = self.current_page() + half_width
            if end_page > num_pages:
                end_page = num_pages
            print("start_page=%s, end_page=%s" % (start_page, end_page))
            item = {"num": 1, "offset": 0, "limit": self.limit, "is_current": False}
            item = self.add_kwargs(item, self.kwargs)
            item["params"] = self.urlencode(item, include_list)
            pagination.append(item)
            item = {"num": "..."}
            pagination.append(item)
            for i in range(start_page, end_page + 1):
                item = {
                    "num": i,
                    "offset": self.calculate_offset(i),
                    "limit": self.limit,
                    "is_current": self.is_current_page(i),
                }
                item = self.add_kwargs(item, self.kwargs)
                item["params"] = self.urlencode(item, include_list)
                pagination.append(item)
            if end_page < num_pages != cur_page:
                item = {"num": "..."}
                pagination.append(item)
                item = {
                    "num": num_pages,
                    "offset": self.calculate_offset(num_pages),
                    "limit": self.limit,
                    "is_current": False,
                }
                item = self.add_kwargs(item, self.kwargs)
                item["params"] = self.urlencode(item, include_list)
                pagination.append(item)

        return pagination
