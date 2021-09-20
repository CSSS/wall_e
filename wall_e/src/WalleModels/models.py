import datetime

from asgiref.sync import sync_to_async
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
        max_length=2000
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
    reminder_id = models.BigAutoField(
        primary_key=True
    )
    reminder_date_epoch = models.BigIntegerField(
        default=0
    )
    message = models.CharField(
        max_length=2000,
        default="INVALID"
    )
    author_id = models.CharField(
        max_length=500,
        default="INVALID"
    )
    author_name = models.CharField(
        max_length=500,
        default="INVALID"
    )
    message_id = models.CharField(
        max_length=200,
        default="INVALID"
    )
