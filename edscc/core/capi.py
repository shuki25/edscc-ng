import logging
from json import JSONDecodeError

import requests
from allauth.socialaccount.models import SocialToken
from django.conf import settings
from django.contrib import messages

from ..squadron.models import Tags
from .models import CapiLog
from .utils import to_snake_case

log = logging.getLogger(__name__)

badge_color_list = [
    "bg-blue",
    "bg-orange",
    "bg-green",
    "bg-olive",
    "bg-navy",
    "bg-default",
    "bg-purple",
    "bg-red",
]


class Capi:
    def __init__(self, request=None):
        self.is_beta = getattr(settings, "FDEV_BETA", False)
        self.request = request

        if not self.is_beta:
            capi_api = settings.CAPI_URL
            # Mock Server for testing
            # capi_api = "https://073f4ddf-58bf-4d24-af3a-0e1cb7ba655d.mock.pstmn.io"
        else:
            capi_api = settings.CAPI_BETA_URL

        self.profile_url = capi_api + "profile"
        self.shipyard_url = capi_api + "shipyard"
        self.fleetcarrier_url = capi_api + "fleetcarrier"
        self.communitygoals_url = capi_api + "communitygoals"
        self.squadron_url = settings.API_URL + "squadron"
        self.capi_token = None
        return

    def get_user_token(self, user):
        if self.capi_token is None or self.capi_token == "":
            rs = list(
                SocialToken.objects.filter(
                    account__user=user, account__provider="frontier"
                )
            )
            self.capi_token = rs.pop()
        return self.capi_token

    def api_fetch(self, url, user, payload=None, allow_log=True, websocket=False):
        status = {"Status": "OK", "Error": None}
        data = {}
        try:
            r = requests.get(
                url,
                headers={
                    "User-Agent": settings.USER_AGENT,
                    "Authorization": "Bearer %s" % self.get_user_token(user),
                },
                params=payload,
            )
            try:
                data = r.json()
            except JSONDecodeError as e:
                status = {"Status": "500", "Error": "%s" % repr(e)}
                data = {}
            r.raise_for_status()
            status["Status"] = r.status_code
        except requests.exceptions.Timeout as e:
            status = {"Status": "408", "Error": "%s" % repr(e)}
        except requests.exceptions.ConnectionError as e:
            status = {"Status": "504", "Error": "%s" % repr(e)}
        except requests.exceptions.HTTPError as e:
            status = {"Status": "404", "Error": "%s" % repr(e)}
        except requests.exceptions.RequestException as e:
            status = {"Status": "500", "Error": "%s" % repr(e)}

        if status["Status"] != 200:
            if self.request is not None and not websocket:
                messages.error(
                    self.request, "[%s]: %s" % (status["Status"], status["Error"])
                )
            log.debug(status)
            return status, data

        if allow_log:
            capi_log = CapiLog(
                user_id=user,
                endpoint=url.rsplit("/", 1)[-1],
                response_code=status["Status"],
                data=data,
            )
            capi_log.save()

        return status, data

    def get_profile(self, user):
        status, data = self.api_fetch(self.profile_url, user)
        return status, data

    def get_shipyard(self, user):
        status, data = self.api_fetch(self.shipyard_url, user)
        return status, data

    def get_fleetcarrier(self, user):
        status, data = self.api_fetch(self.fleetcarrier_url, user)
        return status, data

    def get_communitygoals(self, user):
        status, data = self.api_fetch(self.communitygoals_url, user)
        return status, data

    def get_squadron_list(
        self,
        user,
        platform="PC",
        name=None,
        tag=None,
        usertags=None,
        offset=0,
        limit=12,
        websocket=False,
    ):
        payload = {
            "platform": platform,
            "name": name,
            "usertags": usertags,
            "tag": tag,
            "offset": offset,
            "limit": limit,
            "sort": "name",
        }
        status, data = self.api_fetch(
            self.squadron_url + "/list",
            user,
            payload=payload,
            allow_log=False,
            websocket=websocket,
        )
        return status, data

    def get_squadron_members(self, user, squadron_id=None, websocket=False):
        if squadron_id:
            payload = {"squadronId": squadron_id}
            status, data = self.api_fetch(
                self.squadron_url + "/member/list",
                user,
                payload=payload,
                websocket=websocket,
            )
            return status, data

    def get_squadron_details(
        self, user, platform="PC", squadron_tag=None, websocket=False
    ):
        if squadron_tag:
            payload = {"tag": squadron_tag, "platform": platform}
            status, data = self.api_fetch(
                self.squadron_url + "/info",
                user,
                payload=payload,
                allow_log=False,
                websocket=websocket,
            )
            return status, data

    def get_squadron_tags(self, user):
        status, data = self.api_fetch(self.squadron_url + "/tags/available", user)
        return status, data

    def import_squadron_tags(self, user):
        qs = Tags.objects.filter(collection="activities")
        print(qs)
        if not qs:
            status, data = self.get_squadron_tags(user)
            if status["Status"] == 200:
                if "SquadronTagData" in data:
                    tag_list = data["SquadronTagData"]["SquadronTagCollections"]
                    for i, collection in enumerate(tag_list):
                        collection_name = to_snake_case(
                            collection["localisedCollectionName"]
                        )
                        for tags in collection["SquadronTags"]:
                            r = Tags(
                                fdev_id=tags["ServerUniqueId"],
                                collection=collection_name,
                                name=tags["LocalisedString"],
                                badge_color=badge_color_list[i],
                            )
                            r.save()
