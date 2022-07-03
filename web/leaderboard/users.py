import csv
import os
import discord
import pandas


class UsersClient(discord.Client):
    async def on_ready(self):
        df = pandas.DataFrame(((member.id, str(member) + ''.join([]
                                                                 if not member.nick else
                                                                 [' ', member.display_name]))
                               for member in self.guilds[0].members),
                              columns=['user_id', 'user_name'])
        df.to_csv('/srv/shiny-server/leaderboard/users.csv', index=False, quoting=csv.QUOTE_ALL)
        await self.close()


users_client = UsersClient(intents=discord.Intents.all())
users_client.run(os.getenv('TOKEN'))
