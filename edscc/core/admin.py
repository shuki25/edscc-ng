from django.contrib import admin
from django.conf import settings
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from .models import Carousel, CommunityGoal, GalnetNews, Motd

# Unregister the provided model admin for User
admin.site.unregister(User)


# Register our own model admin, based on the default UserAdmin
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    readonly_fields = [
        'date_joined',
    ]

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        is_superuser = request.user.is_superuser
        disabled_fields = set()

        if not is_superuser:
            disabled_fields |= {
                'username',
                'is_superuser',
                'user_permissions',
            }

        if not is_superuser and obj is not None and obj == request.user:
            disabled_fields |= {
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions',
            }

        for f in disabled_fields:
            if f in form.base_fields:
                form.base_fields[f].disabled = True

        return form


# Register your models here.
class MotdAdmin(admin.ModelAdmin):
    list_display = ("title", "message", "created_at")
    list_filter = ("title", "created_at")


class CarouselAdmin(admin.ModelAdmin):
    list_display = ("name", "slide_label", "squadron", "user", "start_datetime")
    list_filter = ("name", "slide_label", "squadron", "user", "start_datetime")


class CommunityGoalAdmin(admin.ModelAdmin):
    list_display = ("title", "starsystem_name", "market_name", "expiry")


class GalnetNewsAdmin(admin.ModelAdmin):
    list_display = ("title", "ed_date", "slug", "date_added")
    change_list_template = "%s%s" % (settings.APPS_DIR, '/templates/admin/galnet_change_list.html')


admin.site.register(Motd, MotdAdmin)
admin.site.register(Carousel, CarouselAdmin)
admin.site.register(CommunityGoal, CommunityGoalAdmin)
admin.site.register(GalnetNews, GalnetNewsAdmin)
