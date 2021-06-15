import logging

from django.db import connection

from edscc.core.decorators import cached

log = logging.Logger(__name__)


def dict_fetch_all(cursor):
    """
    Return all rows from a cursor as a dict
    :param cursor:
    :return:
    """
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


@cached(name="sql_query")
def sql_query(sql):
    rs = {}
    with connection.cursor() as c:
        c.execute(sql)
        rs = dict_fetch_all(c)
        log.debug("in sql_query: %s" % rs)
    return rs


@cached(name="sql_query_with_user")
def sql_query_with_user(sql, replace_tags):
    rs = {}
    with connection.cursor() as c:
        for tag, value in replace_tags.items():
            sql = sql.replace(tag, "%s" % value)
        c.execute(sql)
        rs = dict_fetch_all(c)
        log.debug("in sql_query: %s" % rs)
    return rs
