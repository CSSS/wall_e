# for type references to own class
# https://stackoverflow.com/a/33533514
from __future__ import annotations
from typing import List
import datetime
import logging
import random
import time
import pytz
from asgiref.sync import sync_to_async
from django.conf import settings
from django.db import models
from django.forms import model_to_dict
from .customFields import GeneratedIdentityField
import django_db_orm_settings

logger = logging.getLogger('wall_e')


class BanRecords(models.Model):
    ban_id = GeneratedIdentityField(primary_key=True)
    username = models.CharField(max_length=37, null=False)
    user_id = models.BigIntegerField(null=False)
    mod = models.CharField(max_length=37, null=True)
    mod_id = models.BigIntegerField(null=True)
    ban_date = models.BigIntegerField(null=True)
    reason = models.CharField(max_length=512, null=False)
    unban_date = models.BigIntegerField(null=True, default=None)

    class Meta:
        db_table = 'WalleModels_ban_records'

    @classmethod
    @sync_to_async
    def insert_records(cls, records: List[BanRecords]) -> None:
        """Adds entry to BanRecords table"""
        BanRecords.objects.bulk_create(records)

    @classmethod
    @sync_to_async
    def insert_record(cls, record: BanRecords) -> None:
        """Adds entry to BanRecords table"""
        record.save()

    @classmethod
    @sync_to_async
    def get_all_active_ban_user_ids(cls) -> List[int]:
        """Returns list of user_ids for all currently banned users"""

        return list(BanRecords.objects.values_list('user_id', flat=True).filter(unban_date=None))

    @classmethod
    @sync_to_async
    def get_all_active_bans(cls) -> List[BanRecords]:
        """Returns list of usernames and user_ids for all currently banned users"""

        return list(BanRecords.objects.values('username', 'user_id').filter(unban_date=None))

    @classmethod
    @sync_to_async
    def get_active_bans_count(cls) -> int:
        """Returns count of all the active bans"""

        return BanRecords.objects.filter(unban_date=None).count()

    @classmethod
    @sync_to_async
    def unban_by_id(cls, user_id: int) -> str:
        """Set active=False for user with the given user_id. This representes unbanning a user."""
        try:
            user = BanRecords.objects.get(user_id=user_id, unban_date=None)
        except Exception:
            return None

        user.unban_date = datetime.datetime.now().timestamp()
        user.save()
        return user.username

    def __str__(self) -> str:
        return f"ban_id=[{self.ban_id}] username=[{self.username}] user_id=[{self.user_id}] " \
               f"mod=[{self.mod}] mod_id=[{self.mod_id}] date=[{self.ban_date}] reason=[{self.reason}]" \
               f"unban_date=[{self.unban_date}]"


class CommandStat(models.Model):
    epoch_time = models.BigAutoField(
        primary_key=True
    )
    year = models.IntegerField(
        default=datetime.datetime.now().year
    )
    month = models.IntegerField(
        default=datetime.datetime.now().month
    )
    day = models.IntegerField(
        default=datetime.datetime.now().day
    )
    hour = models.IntegerField(
        default=datetime.datetime.now().hour
    )
    channel_name = models.CharField(
        max_length=2000,
        default='NA'
    )
    command = models.CharField(
        max_length=2000
    )
    invoked_with = models.CharField(
        max_length=2000
    )
    invoked_subcommand = models.CharField(
        max_length=2000,
        blank=True, null=True
    )

    @classmethod
    def get_column_headers_from_database(cls):
        return [key for key in model_to_dict(CommandStat) if key != "epoch_time"]

    @classmethod
    async def get_all_entries_async(cls):
        return await sync_to_async(cls._get_all_entries, thread_sensitive=True)()

    @classmethod
    def _get_all_entries(cls):
        return list(CommandStat.objects.all())

    @classmethod
    async def save_command_async(cls, command_stat):
        await sync_to_async(cls._save_command_stat, thread_sensitive=True)(command_stat)

    @classmethod
    def _save_command_stat(cls, command_stat):
        while True:
            try:
                command_stat.save()
                return
            except Exception:
                command_stat.epoch_time += 1

    @classmethod
    async def get_command_stats_dict(cls, filters=None):
        filter_stats_dict = {}
        for command_stat in await CommandStat.get_all_entries_async():
            command_stat = model_to_dict(command_stat)
            key = ""
            for idx, command_filter in enumerate(filters):
                key += f"{command_stat[command_filter]}"
                if idx + 1 < len(filters):
                    key += "-"
            filter_stats_dict[key] = filter_stats_dict.get(key, 0) + 1
        return filter_stats_dict

    def __str__(self):
        return \
            f"{self.epoch_time} - {self.command} as invoked with {self.invoked_with} with " \
            f"subcommand {self.invoked_subcommand} and year {self.year}, " \
            f"month {self.month} and hour {self.hour}"


class UserPoint(models.Model):
    user_id = models.PositiveBigIntegerField(
        unique=True
    )
    points = models.PositiveBigIntegerField(

    )
    level_up_specific_points = models.PositiveBigIntegerField(

    )
    message_count = models.PositiveBigIntegerField(

    )
    latest_time_xp_was_earned_epoch = models.BigIntegerField(
        default=0
    )
    level_number = models.PositiveBigIntegerField(

    )
    hidden = models.BooleanField(
        default=False
    )

    @sync_to_async
    def async_save(self):
        self.save()

    @staticmethod
    @sync_to_async
    def create_user_point(
            user_id, points=random.randint(15, 25), message_count=1,
            latest_time_xp_was_earned=datetime.datetime.now(), level=0):
        user_point = UserPoint(
            user_id=user_id, points=points,
            level_up_specific_points=UserPoint.calculate_level_up_specific_points(points),
            message_count=message_count,
            latest_time_xp_was_earned_epoch=latest_time_xp_was_earned.timestamp(), level_number=level,
        )
        user_point.save()
        return user_point

    @classmethod
    def calculate_level_up_specific_points(cls, points):
        indx = 0
        levels = Level.objects.all().order_by('total_points_required')
        while levels[indx].xp_needed_to_level_up_to_next_level < points and indx < len(levels):
            points -= levels[indx].xp_needed_to_level_up_to_next_level
            indx += 1

        return points

    @sync_to_async
    def increment_points(self):
        alert_user = False
        if self._message_counts_towards_points():
            point = random.randint(15, 25)
            self.points += point
            self.level_up_specific_points += point
            self.message_count += 1
            if self.level_number < 100:
                current_level = Level.objects.get(number=self.level_number)
                if self.level_up_specific_points >= current_level.xp_needed_to_level_up_to_next_level:
                    self.level_up_specific_points -= current_level.xp_needed_to_level_up_to_next_level
                    self.level_number += 1
                    alert_user = True
            self.latest_time_xp_was_earned_epoch = datetime.datetime.now().timestamp()
            self.save()
        return alert_user

    @sync_to_async
    def get_rank(self):
        users_above_in_rank = []
        for user in UserPoint.objects.all().order_by('-points'):
            if user.user_id != self.user_id:
                users_above_in_rank.append(user)
            else:
                return len(users_above_in_rank)+1
        return len(users_above_in_rank)+1

    @sync_to_async
    def get_xp_needed_to_level_up_to_next_level(self):
        return Level.objects.get(number=self.level_number).xp_needed_to_level_up_to_next_level

    @sync_to_async
    def hide_xp(self):
        self.hidden = True
        self.save()

    @sync_to_async
    def show_xp(self):
        self.hidden = False
        self.save()

    @staticmethod
    @sync_to_async
    def user_points_have_been_imported():
        return len(list(UserPoint.objects.all()[:1])) == 1

    @staticmethod
    @sync_to_async
    def clear_all_entries():
        UserPoint.objects.all().delete()

    def _message_counts_towards_points(self):
        return datetime.datetime.fromtimestamp(
            self.latest_time_xp_was_earned_epoch,
            pytz.timezone(django_db_orm_settings.TIME_ZONE)
        ) + datetime.timedelta(minutes=1) < datetime.datetime.now(tz=pytz.timezone(django_db_orm_settings.TIME_ZONE))

    @staticmethod
    @sync_to_async
    def load_to_dict():
        return {user_point.user_id: user_point for user_point in UserPoint.objects.all()}


class Level(models.Model):
    number = models.PositiveBigIntegerField(
        unique=True
    )  # xp_level
    total_points_required = models.PositiveBigIntegerField(

    )  # xp_level_points_required

    xp_needed_to_level_up_to_next_level = models.PositiveBigIntegerField(

    )

    role_id = models.PositiveBigIntegerField(
        null=True,
        unique=True
    )
    role_name = models.CharField(
        max_length=500,
        null=True,
        unique=True
    )  # xp_role_name

    @staticmethod
    @sync_to_async
    def create_level(number, total_points_required, xp_needed_to_level_up_to_next_level,
                     role_id=None, role_name=None):
        level = Level(
            number=number, total_points_required=total_points_required,
            xp_needed_to_level_up_to_next_level=xp_needed_to_level_up_to_next_level,
            role_id=role_id, role_name=role_name
        )
        level.save()
        return level

    @sync_to_async
    def async_save(self):
        self.save()

    @staticmethod
    @sync_to_async
    def level_points_have_been_imported():
        return len(list(Level.objects.all()[:1])) == 1

    @staticmethod
    @sync_to_async
    def clear_all_entries():
        Level.objects.all().delete()

    @staticmethod
    @sync_to_async
    def load_to_dict():
        return {level.number: level for level in Level.objects.all()}

    @sync_to_async
    def set_level_name(self, new_role_name, role_id):
        self.role_name = new_role_name
        self.role_id = role_id
        self.save()

    @sync_to_async
    def rename_level_name(self, new_role_name):
        self.role_name = new_role_name
        self.save()

    @sync_to_async
    def remove_role(self):
        self.role_name = None
        self.role_id = None
        self.save()


class Reminder(models.Model):
    id = models.BigAutoField(
        primary_key=True
    )
    reminder_date_epoch = models.BigIntegerField(
        default=0
    )
    message = models.CharField(
        max_length=2000,
        default="INVALID"
    )
    author_id = models.BigIntegerField(
        default=0
    )

    def __str__(self):
        return f"Reminder for user {self.author_id} on date {self.reminder_date_epoch} with message {self.message}"

    @classmethod
    async def get_expired_reminders(cls):
        return await sync_to_async(cls._sync_get_expired_reminders, thread_sensitive=True)()

    @classmethod
    def _sync_get_expired_reminders(cls):
        return list(
            Reminder.objects.all().filter(
                reminder_date_epoch__lte=datetime.datetime.now(
                    tz=pytz.timezone(f"{settings.TIME_ZONE}")
                ).timestamp()
            )
        )

    @classmethod
    async def get_reminder_by_id(cls, reminder_id):
        if not f"{reminder_id}".isdigit():
            return None
        return await sync_to_async(cls._sync_get_reminder_by_id, thread_sensitive=True)(reminder_id)

    @classmethod
    def _sync_get_reminder_by_id(cls, reminder_id):
        reminders = Reminder.objects.all().filter(id=reminder_id)
        if len(reminders) == 0:
            return None
        else:
            return reminders[0]

    @classmethod
    async def delete_reminder_by_id(cls, reminder_id):
        await sync_to_async(cls._sync_delete_reminder_by_id, thread_sensitive=True)(reminder_id)

    @classmethod
    def _sync_delete_reminder_by_id(cls, reminder_to_delete):
        Reminder.objects.all().get(id=reminder_to_delete).delete()

    @classmethod
    async def delete_reminder(cls, reminder):
        await sync_to_async(cls._sync_delete_reminder, thread_sensitive=True)(reminder)

    @classmethod
    def _sync_delete_reminder(cls, reminder_to_delete):
        reminder_to_delete.delete()

    @classmethod
    async def get_reminder_by_author(cls, author_id):
        return await sync_to_async(
            cls._sync_get_reminder_by_author, thread_sensitive=True
        )(author_id)

    @classmethod
    def _sync_get_reminder_by_author(cls, author_id):
        return list(Reminder.objects.all().filter(author_id=author_id).order_by('reminder_date_epoch'))

    @classmethod
    async def get_all_reminders(cls):
        return await sync_to_async(cls._sync_get_all_reminders, thread_sensitive=True)()

    @classmethod
    def _sync_get_all_reminders(cls):
        return list(Reminder.objects.all().order_by('reminder_date_epoch'))

    @classmethod
    async def save_reminder(cls, reminder_to_save):
        await sync_to_async(cls._sync_save_reminder, thread_sensitive=True)(reminder_to_save)

    @classmethod
    def _sync_save_reminder(cls, reminder_to_save):
        reminder_to_save.save()

    def get_countdown(self):
        seconds = int(self.reminder_date_epoch - time.time())
        day = seconds // (24 * 3600)
        seconds = seconds % (24 * 3600)
        hour = seconds // 3600
        seconds %= 3600
        minutes = seconds // 60
        seconds %= 60

        message = "Reminder set for "
        if day > 0:
            message += f" {day} days"
        if hour > 0:
            message += f" {hour} hours"
        if minutes > 0:
            message += f" {minutes} minutes"
        if seconds > 0:
            message += f" {seconds} seconds"
        return f"{message} from now"
