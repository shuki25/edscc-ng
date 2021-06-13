import logging
from pathlib import Path

import yaml

from edscc.core.sql_util import sql_query, sql_query_with_user

log = logging.getLogger(__name__)

MENU_PATH = "%s%s" % (Path(__file__).resolve().parent, "/menu.yaml")


def load_menu_yaml():
    data = dict()

    with open(MENU_PATH) as file:
        data = yaml.full_load(file)

    return data


def group_membership(user):
    group_list = user.groups.all()
    group = []
    if list is not None:
        for name in group_list:
            group.append("%s" % name)
    return group


def is_in_group(user_membership, group_list):
    intersect = set.intersection(set(user_membership), set(group_list))
    return len(intersect) > 0


def build_menu(user):  # noqa C901
    final_menu = dict()
    menu_list = load_menu_yaml()

    if user.is_authenticated:
        group = group_membership(user)
    else:
        group = ["General"]

    for category, top_level in menu_list.items():
        if top_level is not None:
            subgroup = dict()
            for i, menu_item in top_level.items():
                menu_items = dict()
                routes = []
                if "group" in menu_item and (
                    is_in_group(group, menu_item["group"]) or user.is_superuser
                ):
                    for attr, value in menu_item.items():
                        if attr not in ["group", "counter_sql"]:
                            menu_items[attr] = value
                        if attr in ["counter_sql", "alert_sql"]:
                            if ":user_id" in value:
                                replace_tag = {":user_id": user.id}
                                rs = sql_query_with_user(value, replace_tag)
                            else:
                                rs = sql_query(value)
                            if len(rs):
                                key = "alert" if "alert" in rs[0] else "counter"
                                menu_items[key] = rs[0][key]
                        if attr == "route":
                            routes.append(value)
                        if attr == "routes":
                            routes = routes + value
                    if len(menu_items):
                        subgroup[i] = menu_items
            if len(subgroup):
                final_menu[category] = subgroup
    return final_menu
