import csv
import os
import discord
import pandas
from datetime import datetime, timedelta, timezone


class UsersClient(discord.Client):
    def __init__(self, users_csv: str, **options):
        self.users_csv = users_csv
        super().__init__(**options)

    async def on_ready(self):
        df = pandas.DataFrame(((member.id, str(member) + ''.join([]
                                                                 if not member.nick else
                                                                 [' ', member.display_name]))
                               for member in self.guilds[0].members),
                              columns=['user_id', 'user_name'])
        df.to_csv(self.users_csv, index=False, quoting=csv.QUOTE_ALL)
        await self.close()


def file_expired(file: str, expiry: timedelta):
    st_info = os.stat(file)
    dt_mtime = datetime.fromtimestamp(st_info.st_mtime, timezone.utc)
    dt_now = datetime.now(timezone.utc)
    return dt_now - dt_mtime > expiry or not st_info.st_size


f_out = '/srv/shiny-server/leaderboard/users.csv'
f_max_age = timedelta(hours=1)
if file_expired(f_out, f_max_age):
    users_client = UsersClient(f_out, intents=discord.Intents.all())
    users_client.run(os.getenv('TOKEN'))
