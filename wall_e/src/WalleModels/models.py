import datetime
import time

import pytz
from asgiref.sync import sync_to_async
from django.conf import settings
from django.db import models
from django.forms import model_to_dict


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
