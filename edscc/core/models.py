import logging

from django.contrib.auth.models import User
from django.db import models

from edscc.squadron.models import Squadron

log = logging.getLogger(__name__)


# Create your models here.
class AccessHistory(models.Model):
    user = models.ForeignKey(User, models.CASCADE)
    remote_ip = models.CharField(max_length=16)
    country_code = models.CharField(max_length=2)
    country_name = models.CharField(max_length=64)
    region_name = models.CharField(max_length=128)
    city_name = models.CharField(max_length=128)
    latitude = models.FloatField()
    longitude = models.FloatField()
    zip_code = models.CharField(max_length=30)
    browser = models.CharField(max_length=255, blank=True, null=True)
    platform = models.CharField(max_length=255, blank=True, null=True)
    device = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    google_2fa_trust_flag = models.IntegerField()

    class Meta:
        managed = True
        db_table = "access_history"


class Acl(models.Model):
    role_string = models.CharField(max_length=50)
    description = models.CharField(max_length=255)
    list_order = models.SmallIntegerField()
    admin_flag = models.IntegerField()

    class Meta:
        managed = True
        db_table = "acl"


class Announcement(models.Model):
    user = models.ForeignKey(User, models.CASCADE)
    squadron = models.ForeignKey(Squadron, models.CASCADE)
    title = models.CharField(max_length=255)
    message = models.TextField(blank=True, null=True)
    publish_at = models.DateTimeField(blank=True, null=True)
    created_by = models.ForeignKey(
        User,
        models.CASCADE,
        related_name="created_by",
        db_column="created_by",
        blank=True,
        null=True,
    )
    updated_by = models.ForeignKey(
        User,
        models.CASCADE,
        related_name="updated_by",
        db_column="updated_by",
        blank=True,
        null=True,
    )
    published_flag = models.IntegerField()
    pinned_flag = models.IntegerField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = True
        db_table = "announcement"


class Debug(models.Model):
    detail = models.TextField()
    posted_at = models.DateTimeField()

    class Meta:
        managed = True
        db_table = "debug"


class EarningType(models.Model):
    name = models.CharField(max_length=40)
    mission_flag = models.IntegerField()

    class Meta:
        managed = True
        db_table = "earning_type"


class Edmc(models.Model):
    user = models.ForeignKey(User, models.CASCADE)
    entry = models.TextField(blank=True, null=True)
    entered_at = models.DateTimeField()
    processed_flag = models.IntegerField()

    class Meta:
        managed = True
        db_table = "edmc"


class ErrorLog(models.Model):
    scope = models.CharField(max_length=50)
    error_id = models.CharField(max_length=50, blank=True, null=True)
    error_msg = models.TextField()
    debug_info = models.TextField(blank=True, null=True)
    stack_trace = models.TextField(blank=True, null=True)
    data_trace = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = True
        db_table = "error_log"


class Language(models.Model):
    locale = models.CharField(max_length=2)
    name = models.CharField(max_length=50)
    locale_name = models.CharField(max_length=50)
    has_translation = models.IntegerField()
    percent_complete = models.SmallIntegerField()
    verified = models.IntegerField()

    class Meta:
        managed = True
        db_table = "language"


class Motd(models.Model):
    title = models.CharField(max_length=255, blank=True, null=True)
    message = models.TextField(blank=True, null=True)
    show_flag = models.IntegerField()
    show_login = models.IntegerField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = True
        db_table = "motd"


class ReadHistory(models.Model):
    announcement = models.ForeignKey(
        Announcement, models.CASCADE, blank=True, null=True
    )
    motd = models.ForeignKey("Motd", models.CASCADE, blank=True, null=True)
    user = models.ForeignKey(User, models.CASCADE, blank=True, null=True)

    class Meta:
        managed = True
        db_table = "read_history"


class ThargoidVariant(models.Model):
    name = models.CharField(max_length=50)
    reward = models.IntegerField()

    class Meta:
        managed = True
        db_table = "thargoid_variant"


class CommunityGoal(models.Model):
    title = models.CharField(max_length=255)
    expiry = models.DateTimeField()
    market_name = models.CharField(max_length=50)
    starsystem_name = models.CharField(max_length=50)
    activityType = models.CharField(max_length=50)
    target_qty = models.BigIntegerField()
    qty = models.BigIntegerField()
    objective = models.TextField()
    news = models.TextField()
    bulletin = models.TextField()

    class Meta:
        managed = True
        db_table = "community_goal"


class CapiLog(models.Model):
    user = models.ForeignKey(User, models.CASCADE)
    endpoint = models.CharField(max_length=50)
    response_code = models.CharField(max_length=20)
    data = models.TextField()
    date_received = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = "capi_log"


class Carousel(models.Model):
    squadron = models.ForeignKey(Squadron, models.CASCADE, blank=True, null=True)
    name = models.CharField(max_length=50)
    img_src = models.CharField(max_length=255)
    slide_label = models.CharField(max_length=128)
    caption = models.CharField(max_length=128, blank=True, null=True)
    is_active = models.BooleanField(default=False)
    is_visible = models.BooleanField(default=False)
    start_datetime = models.DateTimeField(null=True)
    end_datetime = models.DateTimeField(null=True)
    user = models.ForeignKey(User, models.CASCADE)

    class Meta:
        managed = True
        db_table = "carousel"


class GalnetNews(models.Model):
    title = models.CharField(max_length=100)
    body = models.TextField()
    nid = models.IntegerField()
    ed_date = models.CharField(max_length=15)
    image = models.CharField(max_length=100)
    slug = models.CharField(max_length=100)
    date_added = models.DateTimeField(auto_now=True)

    def first_image(self):
        chunks = self.image.split(",")
        if chunks[0]:
            return chunks[0]
        else:
            return chunks[1]

    class Meta:
        managed = True
        db_table = "galnet_news"
        verbose_name_plural = "Galnet news"
