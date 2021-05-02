"""
Refresh Frontier Token
Checks if a user token is expired, send a request to Frontier server to refresh token to maintain access to cAPI.
"""
import logging
from datetime import timedelta

import requests
from allauth.socialaccount.models import SocialToken
from allauth.socialaccount.providers.frontier.views import FrontierOAuth2Adapter
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.http import HttpResponseRedirect
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin

log = logging.getLogger(__name__)


def token_updater(social_token, token):
    log.debug("Frontier token refreshed")
    social_token.token = token["access_token"]
    social_token.token_secret = token["refresh_token"]
    social_token.expires_at = timezone.now() + timedelta(
        seconds=int(token["expires_in"])
    )
    social_token.save()


class FrontierRefreshTokenMiddleware(MiddlewareMixin):
    log.debug("Loading FrontierRefreshTokenMiddleware")

    def process_request(self, request):
        """Create OAuth2 session which autoupdates the access token if it has expired"""

        # This needs to be amended to whatever your refresh_token_url is.

        if request.user.is_authenticated is False:
            return

        refresh_token_url = FrontierOAuth2Adapter.access_token_url
        # refresh_token_url = "https://073f4ddf-58bf-4d24-af3a-0e1cb7ba655d.mock.pstmn.io/token" # noqa
        try:
            social_token = SocialToken.objects.get(account__user=request.user)
        except Exception as e:
            log.debug(e)
            return

        expires_in = (social_token.expires_at - timezone.now()).total_seconds()
        if expires_in > 600:
            log.debug("Token is not expired yet")
            return

        payload = {
            "client_id": social_token.app.client_id,
            "client_secret": social_token.app.secret,
            "refresh_token": social_token.token_secret,
            "grant_type": "refresh_token",
        }

        header = {
            "User-Agent": settings.USER_AGENT,
            "Content-Type": "application/x-www-form-urlencoded",
        }
        try:
            r = requests.post(refresh_token_url, headers=header, data=payload)
            token = r.json()
            log.debug(token)
            if r.status_code == 200:
                token_updater(social_token, token)
            else:
                messages.error(
                    request,
                    "Your session with Frontier Authentication has expired. Please try signing in again.",
                )
                logout(request)
                return HttpResponseRedirect("https://%s" % (request.get_host()))
            log.debug(r)

        except Exception as e:
            log.debug(e)
