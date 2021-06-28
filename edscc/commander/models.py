# Tracking file by folder pattern:  migrations
# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = True` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.contrib.auth.models import User
from django.db import models
from django.utils.timezone import now

from ..squadron.models import CustomRank, MinorFaction, Rank, Squadron, SquadronRoster


# Create your models here.make
class Status(models.Model):
    name = models.CharField(max_length=20)
    is_lock_out = models.BooleanField(default=False)
    is_banned = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    is_denied = models.BooleanField(default=False)
    tag = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = True
        db_table = "status"


class ActivityCounter(models.Model):
    user = models.ForeignKey(User, models.CASCADE)
    squadron = models.ForeignKey("squadron.Squadron", models.CASCADE, null=True)
    activity_date = models.DateField()
    bounties_claimed = models.IntegerField(default=0)
    systems_scanned = models.IntegerField(default=0)
    bodies_found = models.IntegerField(default=0)
    saa_scan_completed = models.IntegerField(default=0)
    efficiency_achieved = models.IntegerField(default=0)
    market_buy = models.IntegerField(default=0)
    market_sell = models.IntegerField(default=0)
    missions_completed = models.IntegerField(default=0)
    mining_refined = models.IntegerField(default=0)
    illegal_goods = models.IntegerField(default=0)
    stolen_goods = models.IntegerField(default=0)
    black_market = models.IntegerField(default=0)
    cg_participated = models.IntegerField(default=0)
    crimes_committed = models.IntegerField(default=0)
    donations = models.IntegerField(default=0)

    class Meta:
        managed = True
        db_table = "activity_counter"

    def add_by_attr(self, attr_name, count):
        current_value = getattr(self, attr_name)
        current_value += count
        setattr(self, attr_name, current_value)


class Commander(models.Model):
    player_id = models.CharField(max_length=20, blank=True, null=True)
    user = models.OneToOneField(User, models.CASCADE, blank=True, null=True)
    asset = models.BigIntegerField(blank=True, null=True)
    credits = models.BigIntegerField(blank=True, null=True)
    loan = models.IntegerField(blank=True, null=True)
    combat = models.ForeignKey(
        "squadron.Rank", models.CASCADE, related_name="combat", default=6, null=False
    )
    trade = models.ForeignKey(
        "squadron.Rank", models.CASCADE, related_name="trade", default=15, null=False
    )
    explore = models.ForeignKey(
        "squadron.Rank", models.CASCADE, related_name="explore", default=24, null=False
    )
    mercenary = models.ForeignKey(
        "squadron.Rank",
        models.CASCADE,
        related_name="mercenary",
        default=72,
        null=False,
    )
    exobiologist = models.ForeignKey(
        "squadron.Rank",
        models.CASCADE,
        related_name="exobiologist",
        default=81,
        null=False,
    )
    federation = models.ForeignKey(
        "squadron.Rank",
        models.CASCADE,
        related_name="federation",
        default=33,
        null=False,
    )
    empire = models.ForeignKey(
        "squadron.Rank", models.CASCADE, related_name="empire", default=48, null=False
    )
    cqc = models.ForeignKey(
        "squadron.Rank", models.CASCADE, related_name="cqc", default=63, null=False
    )
    combat_progress = models.IntegerField(default=0, null=False)
    trade_progress = models.IntegerField(default=0, null=False)
    explore_progress = models.IntegerField(default=0, null=False)
    mercenary_progress = models.IntegerField(default=0, null=False)
    exobiologist_progress = models.IntegerField(default=0, null=False)
    federation_progress = models.IntegerField(default=0, null=False)
    empire_progress = models.IntegerField(default=0, null=False)
    cqc_progress = models.IntegerField(default=0, null=False)

    class Meta:
        managed = True
        db_table = "commander"

    def _calculate_points(self, rank_level, progress):
        if rank_level < 8:
            points = (rank_level * 100) + progress
        else:
            points = 800
        return int((points / 800) * 100)

    def get_skill_web(self):
        skill_web = {
            "combat": self._calculate_points(
                self.combat.assigned_id, self.combat_progress
            ),
            "trader": self._calculate_points(
                self.trade.assigned_id, self.trade_progress
            ),
            "explorer": self._calculate_points(
                self.explore.assigned_id, self.explore_progress
            ),
            "cqc": self._calculate_points(self.cqc.assigned_id, self.cqc_progress),
            "mercenary": self._calculate_points(
                self.mercenary.assigned_id, self.mercenary_progress
            ),
            "exobiologist": self._calculate_points(
                self.exobiologist.assigned_id, self.exobiologist_progress
            ),
        }
        return skill_web

    def get_squadron_id(self):
        try:
            member = SquadronRoster.objects.get(member_id=self.player_id)
            return member.squadron_id
        except SquadronRoster.DoesNotExist:
            return None


class CrimeType(models.Model):
    name = models.CharField(max_length=255)
    alias = models.CharField(max_length=512, blank=True, null=True)
    category = models.CharField(max_length=25, blank=True, null=True)

    class Meta:
        managed = True
        db_table = "crime_type"


class Crime(models.Model):
    user = models.ForeignKey(User, models.CASCADE)
    squadron = models.ForeignKey(
        "squadron.Squadron", models.CASCADE, blank=True, null=True
    )
    crime_type = models.ForeignKey("CrimeType", models.CASCADE)
    minor_faction = models.ForeignKey(
        "squadron.MinorFaction", models.CASCADE, blank=True, null=True
    )
    victim = models.CharField(max_length=255, blank=True, null=True)
    fine = models.IntegerField(blank=True, null=True)
    bounty = models.IntegerField(blank=True, null=True)
    committed_on = models.DateTimeField()
    notes = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = True
        db_table = "crime"


class FactionActivity(models.Model):
    user = models.ForeignKey(User, models.CASCADE)
    squadron = models.ForeignKey("squadron.Squadron", models.CASCADE, null=True)
    earning_type = models.ForeignKey("core.EarningType", models.CASCADE)
    minor_faction = models.ForeignKey(
        "squadron.MinorFaction",
        models.CASCADE,
        related_name="minor_faction",
        blank=True,
        null=True,
    )
    target_minor_faction = models.ForeignKey(
        "squadron.MinorFaction",
        models.CASCADE,
        related_name="target_minor_faction",
        blank=True,
        null=True,
    )
    earned_on = models.DateField()
    reward = models.IntegerField()

    class Meta:
        managed = True
        db_table = "faction_activity"


class ThargoidActivity(models.Model):
    user = models.ForeignKey(User, models.CASCADE)
    squadron = models.ForeignKey(Squadron, models.CASCADE)
    minor_faction = models.ForeignKey(
        MinorFaction, models.CASCADE, blank=True, null=True
    )
    thargoid = models.ForeignKey("core.ThargoidVariant", models.CASCADE)
    reward = models.IntegerField()
    date_killed = models.DateTimeField()

    class Meta:
        managed = True
        db_table = "thargoid_activity"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    commander_name = models.CharField(max_length=255)
    alternate_email = models.CharField(max_length=180, null=True)
    roles = models.TextField(default="[]")
    has_fleetcarrier = models.BooleanField(default=False)
    squadron = models.ForeignKey(
        "squadron.Squadron", models.CASCADE, blank=True, null=True
    )
    squadron_name = models.CharField(max_length=255, blank=True, null=True)
    rank = models.ForeignKey(Rank, models.CASCADE, blank=True, null=True)
    custom_rank = models.ForeignKey(CustomRank, models.CASCADE, blank=True, null=True)
    status = models.ForeignKey(Status, models.CASCADE, default="6")
    status_comment = models.CharField(max_length=255, blank=True, null=True)
    seen_welcome_message = models.BooleanField(default=False)
    has_gravatar = models.BooleanField(default=False)
    avatar_url = models.CharField(max_length=255, blank=True, null=True)
    is_setup_complete = models.BooleanField(default=False)
    date_joined = models.DateTimeField(blank=True, null=True)
    last_login_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = "user_profile"


class CommanderInfo(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.CharField(max_length=30)
    content = models.JSONField()
    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = "commander_info"


class JournalLog(models.Model):
    user = models.ForeignKey(User, models.CASCADE)
    file = models.FileField(upload_to="journal_log/")
    file_hash = models.CharField(max_length=32, blank=True, null=True, db_index=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    game_start = models.DateTimeField(blank=True, null=True, db_index=True)
    game_end = models.DateTimeField(blank=True, null=True, db_index=True)
    time_started = models.DateTimeField(blank=True, null=True)
    parser_time = models.FloatField(null=True)
    rows_processed = models.IntegerField(null=True)
    progress_code = models.CharField(max_length=1, default="Q")
    progress_percent = models.FloatField(blank=True, null=True)
    error_count = models.IntegerField(default=0)

    class Meta:
        managed = True
        db_table = "journal_log"

    def get_status(self):
        status_code = {
            "Q": "In Queue",
            "U": "Uploaded",
            "P": "Parsing",
            "C": "Processed",
            "E": "Error",
        }
        return status_code[self.progress_code]


class EarningHistory(models.Model):
    user = models.ForeignKey(User, models.CASCADE)
    squadron = models.ForeignKey(Squadron, models.CASCADE, null=True)
    earning_type = models.ForeignKey("core.EarningType", models.CASCADE)
    earned_on = models.DateField(db_index=True)
    reward = models.IntegerField()
    crew_wage = models.IntegerField()
    minor_faction = models.ForeignKey(
        MinorFaction, models.CASCADE, blank=True, null=True
    )
    notes = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = True
        db_table = "earning_history"
