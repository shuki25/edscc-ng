import uuid as uuid
from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext_lazy as _


# Create your models here.
class Faction(models.Model):
    name = models.CharField(max_length=255)
    logo = models.CharField(max_length=255, blank=True, null=True)
    journal_id = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = "faction"


class Power(models.Model):
    name = models.CharField(max_length=255)
    logo = models.CharField(max_length=255, blank=True, null=True)
    journal_id = models.IntegerField(blank=True, null=True)
    color_power = models.CharField(max_length=7, blank=True, null=True)

    class Meta:
        managed = True
        db_table = "power"


class Rank(models.Model):
    group_code = models.CharField(max_length=20, blank=True, null=True)
    assigned_id = models.IntegerField(blank=True, null=True)
    name = models.CharField(max_length=20)
    perm_mask = models.IntegerField()

    def __str__(self):
        return self.name

    class Meta:
        managed = True
        db_table = "rank"


class Tags(models.Model):
    fdev_id = models.IntegerField()
    collection = models.CharField(max_length=25)
    name = models.CharField(max_length=40)
    badge_color = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        indexes = [models.Index(fields=["fdev_id"])]
        managed = True
        db_table = "tags"


class MinorFaction(models.Model):
    name = models.CharField(max_length=255, db_index=True)
    player_faction = models.BooleanField(default=False)
    eddb_id = models.IntegerField(blank=True, null=True, db_index=True)

    class Meta:
        managed = True
        db_table = "minor_faction"


class Squadron(models.Model):
    ENGLISH = "en"
    FRENCH = "fr"
    GERMAN = "de"
    PORTUGUESE = "pt"
    RUSSIAN = "ru"
    SPANISH = "es"

    LANGUAGE_CHOICES = [
        (ENGLISH, _("English")),
        (FRENCH, _("French")),
        (GERMAN, _("German")),
        (PORTUGUESE, _("Portuguese")),
        (RUSSIAN, _("Russian")),
        (SPANISH, _("Spanish")),
    ]

    PC = "PC"
    PS4 = "PS4"
    XBOX = "XBOX"

    PLATFORM_CHOICES = [
        (PC, _("PC")),
        (PS4, _("Playstation")),
        (XBOX, _("XBox")),
    ]

    uuid = models.UUIDField(db_index=True, default=uuid.uuid4)
    fdev_id = models.IntegerField()
    name = models.CharField(max_length=255)
    tag = models.CharField(max_length=4, blank=True, null=True)
    owner_id = models.IntegerField()
    owner_name = models.CharField(max_length=50)
    active = models.BooleanField(default=True)
    platform = models.CharField(max_length=4, choices=PLATFORM_CHOICES, default=PC)
    primary_language = models.CharField(
        max_length=2, choices=LANGUAGE_CHOICES, default=ENGLISH
    )
    accept_new_members = models.BooleanField(default=True)
    admin = models.OneToOneField(User, models.CASCADE)
    superpower = models.ForeignKey(Faction, models.CASCADE, blank=True, null=True)
    faction = models.ForeignKey(MinorFaction, models.CASCADE, blank=True, null=True)
    power = models.ForeignKey(Power, models.CASCADE, blank=True, null=True)
    home_base = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    welcome_message = models.TextField(blank=True, null=True)
    require_approval = models.BooleanField(default=True)
    invite_link = models.BooleanField(default=False)
    squadron_tags = models.ManyToManyField(Tags, blank=True)
    established_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = "squadron"


# class SquadronTags(models.Model):
#     squadron = models.ForeignKey(Squadron, models.CASCADE)
#     tag = models.ForeignKey("Tags", models.CASCADE)
#
#     class Meta:
#         managed = True
#         db_table = "squadron_tags"


class CustomRank(models.Model):
    squadron = models.ForeignKey(Squadron, models.CASCADE)
    order_id = models.SmallIntegerField()
    name = models.CharField(max_length=30)

    class Meta:
        managed = True
        db_table = "custom_rank"


class SquadronRoster(models.Model):
    squadron = models.ForeignKey(Squadron, models.CASCADE)
    member_id = models.IntegerField(db_index=True)
    cmdr_name = models.CharField(max_length=100)
    has_account = models.BooleanField(default=False)
    is_member = models.BooleanField(default=True)
    rank = models.ForeignKey(
        Rank, models.CASCADE, related_name="squadron_rank", default=1, null=False
    )
    rank_combat = models.ForeignKey(
        Rank, models.CASCADE, related_name="rank_combat", default=6, null=False
    )
    rank_trade = models.ForeignKey(
        Rank, models.CASCADE, related_name="rank_trade", default=15, null=False
    )
    rank_explore = models.ForeignKey(
        Rank, models.CASCADE, related_name="rank_explore", default=24, null=False
    )
    rank_mercenary = models.ForeignKey(
        Rank, models.CASCADE, related_name="rank_mercenary", default=72, null=False
    )
    rank_exobiologist = models.ForeignKey(
        Rank, models.CASCADE, related_name="rank_exobiologist", default=81, null=False
    )
    join_date = models.DateTimeField()
    request_date = models.DateTimeField()
    last_online = models.DateTimeField()
    leave_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = "squadron_roster"
