import json
import logging
from collections import OrderedDict
from hashlib import md5

from django.contrib.auth.decorators import user_passes_test
from django.core.cache import cache

log = logging.getLogger(__name__)


def sort(kwargs):
    sorted_dict = OrderedDict()
    for key, value in kwargs.items():
        if isinstance(value, dict):
            sorted_dict[key] = sort(value)
        else:
            sorted_dict[key] = value
    return sorted_dict


def cached(name=None, request=False, timeout=300, request_list=None):

    if request_list is None:
        request_list = []
    params = {}

    def _cached(f):
        def __cached(*args, **kwargs):
            # log.debug("args=%s, kwargs=%s" % (args, kwargs))
            if request:
                obj = args[0]
                attr_list = [attribute for attribute in dir(obj)]
                params["user:email"] = obj.user.email if obj.user.is_authenticated else "anonymous"
                for a in attr_list:
                    if a in request_list:
                        params[a] = getattr(obj, a)
                params_sorted = sort(params)
                key = json.dumps(
                    [name, params_sorted, sort(kwargs)], separators=(",", ":")
                )
            else:
                key = json.dumps([name, args, sort(kwargs)], separators=(",", ":"))
            # log.debug("key=%s" % key)
            hashed_key = md5(key.encode("utf-8")).hexdigest()
            extended_key = "%s:%s" % (name, hashed_key)
            cache_value = cache.get(extended_key)
            if cache_value is not None:
                log.info("returning cached result")
                return cache_value
            result = f(*args, **kwargs)
            log.info("caching result: %s %s" % (name, id(f)))
            cache.set(extended_key, result, timeout=timeout)
            return result

        return __cached

    return _cached


def group_required(*group_names):
    """Requires user membership in at least one of the groups passed in."""

    def in_groups(user):
        if user.is_authenticated:
            if user.groups.filter(name__in=group_names).count() > 0 | user.is_superuser:
                return True
        return False

    return user_passes_test(in_groups)
