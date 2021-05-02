from django.contrib import admin

from .models import Carousel, CommunityGoal, GalnetNews, Motd


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


admin.site.register(Motd, MotdAdmin)
admin.site.register(Carousel, CarouselAdmin)
admin.site.register(CommunityGoal, CommunityGoalAdmin)
admin.site.register(GalnetNews, GalnetNewsAdmin)
