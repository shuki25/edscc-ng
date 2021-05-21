import logging

import requests
from allauth.socialaccount.models import SocialToken
from django.conf import settings
from django.contrib import messages

from edscc.core.models import CapiLog

log = logging.getLogger(__name__)


class Capi:
    def __init__(self, request=None):
        self.is_beta = getattr(settings, "FDEV_BETA", False)
        self.request = request

        if not self.is_beta:
            capi_api = "https://companion.orerve.net"
            # Mock Server for testing
            # capi_api = "https://073f4ddf-58bf-4d24-af3a-0e1cb7ba655d.mock.pstmn.io"
        else:
            capi_api = "https://pts-companion.orerve.net"

        self.profile_url = capi_api + "/profile"
        self.shipyard_url = capi_api + "/shipyard"
        self.fleetcarrier_url = capi_api + "/fleetcarrier"
        self.communitygoals_url = capi_api + "/communitygoals"
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

    def api_fetch(self, url, user):
        status = {"Status": "OK"}
        data = {}
        r = object
        try:
            r = requests.get(
                url,
                headers={
                    "User-Agent": settings.USER_AGENT,
                    "Authorization": "Bearer %s" % self.get_user_token(user),
                },
            )
            r.raise_for_status()
            status["Status"] = r.status_code
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

        if status["Status"] != "OK":
            if self.request:
                messages.error(
                    self.request, "[%s]: %s" % (status["Status"], status["Error"])
                )
            log.debug(status)
            return status, {}

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
