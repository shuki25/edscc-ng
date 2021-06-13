import logging

from django.utils import timezone

from ..commander.models import Commander
from ..core.utils import hex2text, timezone_aware
from .models import Rank, SquadronRoster

log = logging.getLogger(__name__)


def sync_squadron_roster(roster=None, squadron_id=None):
    if squadron_id is None or roster is None:
        return {"error": True, "message": "Empty parameters"}

    if not isinstance(roster, list):
        return {"error": True, "message": "Not list Type"}

    update_counter = 0
    new_counter = 0
    leave_counter = 0

    current_roster = SquadronRoster.objects.filter(squadron_id=squadron_id)
    roster_lookup = {i.member_id: True for i in current_roster}

    for r in roster:
        try:
            member = SquadronRoster.objects.get(member_id=r["member_id"])
        except SquadronRoster.DoesNotExist:
            member = SquadronRoster()

        commander = Commander.objects.filter(player_id=r["member_id"])

        member.squadron_id = squadron_id
        member.member_id = r["member_id"]
        member.cmdr_name = hex2text(r["name"])
        member.has_account = True if len(commander) else False
        member.is_member = True
        member.rank = Rank.objects.get(group_code="squadron", assigned_id=r["rank_id"])
        member.rank_combat = Rank.objects.get(
            group_code="combat", assigned_id=r["rankCombat"]
        )
        member.rank_explore = Rank.objects.get(
            group_code="explore", assigned_id=r["rankExplore"]
        )
        member.rank_trade = Rank.objects.get(
            group_code="trade", assigned_id=r["rankTrade"]
        )
        member.rank_mercenary = Rank.objects.get(
            group_code="mercenary", assigned_id=r["rankSoldier"]
        )
        member.rank_exobiologist = Rank.objects.get(
            group_code="exobiologist", assigned_id=r["rankExobiologist"]
        )
        member.join_date = timezone_aware(r["joined"])
        member.request_date = timezone_aware(r["requested"])
        member.last_online = timezone_aware(r["lastOnline"])
        member.save()

        if r["member_id"] in roster_lookup:
            update_counter += 1
            roster_lookup.pop(r["member_id"], None)
        else:
            new_counter += 1

    for member_id, i in roster_lookup.items():
        member = SquadronRoster.objects.get(member_id=member_id)
        member.is_member = False
        member.leave_date = timezone.now()
        member.save()
        leave_counter += 1

    results = {
        "update": update_counter,
        "new": new_counter,
        "leave": leave_counter,
    }

    return results
