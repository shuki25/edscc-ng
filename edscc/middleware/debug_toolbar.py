from django.conf import settings


def show_toolbar(request):
    """
    Default function to determine whether to show the toolbar on a given page.
    """
    if request.META.get("HTTP_X_REAL_IP") is not None:
        return (
            settings.DEBUG
            and request.META.get("HTTP_X_REAL_IP") in settings.INTERNAL_IPS
        )
    elif request.META.get("HTTP_X_FORWARD_FOR") is not None:
        return (
            settings.DEBUG
            and request.META.get("HTTP_X_FORWARD_FOR") in settings.INTERNAL_IPS
        )
    else:
        return (
            settings.DEBUG and request.META.get("REMOTE_ADDR") in settings.INTERNAL_IPS
        )
