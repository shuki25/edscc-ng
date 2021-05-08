from django.contrib.auth.models import User
from django.db import models


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


class Squadron(models.Model):
    name = models.CharField(max_length=255)
    id_code = models.CharField(max_length=4, blank=True, null=True)
    active = models.CharField(max_length=1, blank=True, null=True)
    admin = models.OneToOneField(User, models.CASCADE)
    faction = models.ForeignKey(Faction, models.CASCADE, blank=True, null=True)
    power = models.ForeignKey(Power, models.CASCADE, blank=True, null=True)
    home_base = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    welcome_message = models.TextField(blank=True, null=True)
    require_approval = models.CharField(max_length=1)
    invite_link = models.IntegerField()

    class Meta:
        managed = True
        db_table = "squadron"


class Tags(models.Model):
    group_code = models.CharField(max_length=20)
    name = models.CharField(max_length=40)
    badge_color = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = True
        db_table = "tags"


class SquadronTags(models.Model):
    squadron = models.ForeignKey(Squadron, models.CASCADE)
    tag = models.ForeignKey("Tags", models.CASCADE)

    class Meta:
        managed = True
        db_table = "squadron_tags"


class CustomRank(models.Model):
    squadron = models.ForeignKey(Squadron, models.CASCADE)
    order_id = models.SmallIntegerField()
    name = models.CharField(max_length=30)

    class Meta:
        managed = True
        db_table = "custom_rank"


class MinorFaction(models.Model):
    name = models.CharField(max_length=255, db_index=True)
    player_faction = models.BooleanField(default=False)
    eddb_id = models.IntegerField(blank=True, null=True, db_index=True)

    class Meta:
        managed = True
        db_table = "minor_faction"
