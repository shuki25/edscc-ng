import logging

from django.db import connection

log = logging.Logger(__name__)


def dict_fetch_all(cursor):
    """
    Return all rows from a cursor as a dict
    :param cursor:
    :return:
    """
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def sql_query(sql):
    rs = {}
    with connection.cursor() as c:
        c.execute(sql)
        rs = dict_fetch_all(c)
        log.debug(rs)
    return rs


def sql_query_with_user(sql, replace_tags):
    rs = {}
    with connection.cursor() as c:
        for tag, value in replace_tags.items():
            sql = sql.replace(tag, "%s" % value)
        c.execute(sql)
        rs = dict_fetch_all(c)
        log.debug(rs)
    return rs
