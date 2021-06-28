import json
import logging

import numpy as np
import pandas as pd
from django.contrib.auth.models import User
from django.db.models.query import QuerySet
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from ..commander.models import Commander, UserProfile
from ..core.capi import Capi
from ..core.utils import hex2text, percentage_diff, timezone_aware
from .models import Leaderboard, Rank, Squadron, SquadronRoster

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


def sync_leaderboard(user: User, platform="PC"):
    status = {"Status": 200}
    if isinstance(user, User) and user.userprofile.squadron_id:
        leaderboard_types = [
            "combat",
            "trade",
            "exploration",
            "bgs",
            "powerplay",
            "aegis",
            "cqc",
        ]
        squadron_id = user.userprofile.squadron_id
        try:
            s = Squadron.objects.get(id=squadron_id)
            fdev_id = s.fdev_id
            if not fdev_id:
                raise BaseException("FDev_id not available")
        except UserProfile.DoesNotExist:
            raise BaseException("User profile not found")
        api = Capi()
        last_updated = timezone.now()

        board = Leaderboard.objects.filter(
            last_updated=last_updated,
            squadron_id=squadron_id,
        ).values("leaderboard_type")

        existing_board = []
        if len(board):
            existing_board = [row["leaderboard_type"] for row in board]
        for t in leaderboard_types:
            if t not in existing_board:
                status, data = api.get_squadron_leaderboard(
                    user.pk,
                    leaderboard_type=t,
                    platform=platform,
                    squadron_id=fdev_id,
                )
                if status["Status"] == 200 and "leaderboards" in data:
                    new_board = Leaderboard(
                        leaderboard_type=t,
                        content=data["leaderboards"],
                        squadron_id=squadron_id,
                    )
                    new_board.save()
    else:
        status.update(
            {"Status": 500, "Error": _("user_id and squadron_id are required")}
        )

    return status


def top_n_leaderboard(df, top_n=25, fdev_id=None):
    icons = {
        "combat": "fas fa-fist-raised",
        "trade": "fas fa-hand-holding-usd",
        "exploration": "fas fa-space-shuttle",
        "bgs": "",
        "powerplay": "",
        "aegis": "",
        "cqc": "fas fa-fighter-jet",
    }
    leaderboards = []

    for key, icon in icons.items():
        board = df.loc[df["type"] == key]
        leaderboards.append(
            {
                "type": key,
                "board": df.loc[
                    ((df["type"] == key) & (df["rank"] < top_n))
                    | ((df["type"] == key) & (df["squadron"] == fdev_id))
                ].to_dict(
                    orient="records",
                ),
                "icon": icon,
            }
        )

    return leaderboards


def leaderboards_to_df(new_boards, old_boards):
    frames = []
    for row in new_boards:
        df = pd.DataFrame.from_dict(row.content[row.leaderboard_type])
        df["type"] = row.leaderboard_type
        myranking = row.content["myranking"]
        if myranking["rank"] != "-" and int(myranking["rank"]) > 1000:
            myranking["percentile"] = "0"
            df = df.append(myranking, ignore_index=True)
        frames.append(df)

    final = pd.concat(frames)

    if isinstance(old_boards, QuerySet):
        frames = []
        for row in old_boards:
            df = pd.DataFrame.from_dict(row.content[row.leaderboard_type])
            df["type"] = row.leaderboard_type
            myranking = row.content["myranking"]
            if myranking["rank"] != "-" and int(myranking["rank"]) > 1000:
                myranking["percentile"] = "0"
                df.append(myranking, ignore_index=True)
            frames.append(df)

        df = pd.concat(frames)
        old_df = df[["squadron", "rank", "score", "type"]]
        old_df.columns = ["squadron", "prev_rank", "prev_score", "type"]

        final = pd.merge(final, old_df, how="left", on=["squadron", "type"])
        final["prev_rank"] = final["prev_rank"].astype("Int64")
        final["prev_score"] = final["prev_score"].astype("Int64")

    else:
        final["prev_rank"] = None
        final["prev_score"] = None

    final["delta_rank"] = final.apply(
        lambda x: x["prev_rank"] - x["rank"]
        if isinstance(x["prev_rank"], int)
        else None,
        axis=1,
    )
    final["delta_score"] = final.apply(
        lambda x: percentage_diff(x["prev_score"], x["score"]), axis=1
    )
    final = final.sort_values(by=["type", "rank"])
    final = final.replace({np.nan: None})

    return final
