import discord
from discord.ext import commands
from wall_e_models.models import HelpMessage
from utilities.embed import WallEColour, COLOUR_MAPPING


class EmbedHelpCommand(commands.DefaultHelpCommand):
    # Set the embed colour here

    def __init__(self):
        super(EmbedHelpCommand, self).__init__(
            show_parameter_descriptions=False, sort_commands=False)

    async def send_bot_help(self, mapping):
        embed = discord.Embed(title='Bot Text Commands', colour=COLOUR_MAPPING[WallEColour.INFO])
        description = self.context.bot.description
        if description:
            embed.description = description
        embed.set_footer(text=self.get_ending_note())

        cogs_ordered_by_value_length = {}
        filtered = await self.filter_commands(self.context.bot.commands)
        for mapped_cog, mapped_commands in mapping.items():
            commands_display = [
                f"\n.{command.name}: {command.brief}\n" if command.brief else f".{command.name}\u2002"
                for command in mapped_commands
                if command in filtered
            ]
            value = ''.join(commands_display)

            command_under_cog = mapped_cog is not None
            cog_has_commands_user_can_run = value.strip() != ""

            if cog_has_commands_user_can_run and command_under_cog:
                length_of_value = len(value)
                if length_of_value in commands_display:
                    cogs_ordered_by_value_length[length_of_value].append(
                        {"cog_name": mapped_cog.qualified_name, "cog_commands": value}
                    )
                else:
                    cogs_ordered_by_value_length[length_of_value] = [
                        {"cog_name": mapped_cog.qualified_name, "cog_commands": value}
                    ]

        sorted_cogs_keys = sorted(list(cogs_ordered_by_value_length.keys()))
        for sorted_cogs_key in sorted_cogs_keys:
            for mapped_cog in cogs_ordered_by_value_length[sorted_cogs_key]:
                embed.add_field(name=mapped_cog['cog_name'], value=mapped_cog['cog_commands'])
        msg = await self.get_destination().send(content=None, embed=embed, reference=self.context.message)

        await HelpMessage.insert_record(
            HelpMessage(
                message_id=msg.id, channel_name=msg.channel.name, channel_id=msg.channel.id,
                time_created=msg.created_at.timestamp()
            )
        )

    async def send_cog_help(self, cog):
        embed = discord.Embed(title=f'{cog.qualified_name} Commands', colour=COLOUR_MAPPING[WallEColour.INFO])

        for command in cog.get_commands():
            embed.add_field(name=self.get_command_signature(command), value=command.short_doc or '', inline=False)

        embed.set_footer(text=self.get_ending_note())
        msg = await self.get_destination().send(embed=embed, reference=self.context.message)
        await HelpMessage.insert_record(
            HelpMessage(
                message_id=msg.id, channel_name=msg.channel.name, channel_id=msg.channel.id,
                time_created=msg.created_at.timestamp()
            )
        )

    async def send_command_help(self, command):
        embed = discord.Embed(
            title=f".{command}{f' {command.usage}' if command.usage else ''}",
            colour=COLOUR_MAPPING[WallEColour.INFO],
            description=command.help,
        )
        embed.set_footer(text=self.get_ending_note())
        msg = await self.get_destination().send(embed=embed, reference=self.context.message)
        await HelpMessage.insert_record(
            HelpMessage(
                message_id=msg.id, channel_name=msg.channel.name, channel_id=msg.channel.id,
                time_created=msg.created_at.timestamp()
            )
        )

    async def send_error_message(self, error: str, /) -> None:
        embed = discord.Embed(
            title="ERROR", colour=COLOUR_MAPPING[WallEColour.INFO],
            description=error,
        )
        embed.set_footer(text=self.get_ending_note())
        msg = await self.get_destination().send(embed=embed, reference=self.context.message)
        await HelpMessage.insert_record(
            HelpMessage(
                message_id=msg.id, channel_name=msg.channel.name, channel_id=msg.channel.id,
                time_created=msg.created_at.timestamp()
            )
        )
