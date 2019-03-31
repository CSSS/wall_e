#list of possible roles to check can be pulled from here https://discordpy.readthedocs.io/en/rewrite/api.html#discord.Permissions

async def getListOfUserPerms(ctx):
	roles=[]
	if ctx.author.guild_permissions.create_instant_invite:
		roles.append('create_instant_invite')
	if ctx.author.guild_permissions.kick_members:
		roles.append('kick_members')
	if ctx.author.guild_permissions.ban_members:
		roles.append('ban_members')
	if ctx.author.guild_permissions.administrator:
		roles.append('administrator')
	if ctx.author.guild_permissions.manage_channels:
		roles.append('manage_channels')
	if ctx.author.guild_permissions.manage_guild:
		roles.append('manage_guild')
	if ctx.author.guild_permissions.add_reactions:
		roles.append('add_reactions')
	if ctx.author.guild_permissions.view_audit_log:
		roles.append('view_audit_log')
	if ctx.author.guild_permissions.priority_speaker:
		roles.append('priority_speaker')
	if ctx.author.guild_permissions.read_messages:
		roles.append('read_messages')
	if ctx.author.guild_permissions.send_messages:
		roles.append('send_messages')
	if ctx.author.guild_permissions.send_tts_messages:
		roles.append('send_tts_messages')
	if ctx.author.guild_permissions.manage_messages:
		roles.append('manage_messages')
	if ctx.author.guild_permissions.embed_links:
		roles.append('embed_links')
	if ctx.author.guild_permissions.attach_files:
		roles.append('attach_files')
	if ctx.author.guild_permissions.read_message_history:
		roles.append('read_message_history')
	if ctx.author.guild_permissions.mention_everyone:
		roles.append('mention_everyone')
	if ctx.author.guild_permissions.external_emojis:
		roles.append('external_emojis')
	if ctx.author.guild_permissions.connect:
		roles.append('connect')
	if ctx.author.guild_permissions.speak:
		roles.append('speak')
	if ctx.author.guild_permissions.mute_members:
		roles.append('mute_members')
	if ctx.author.guild_permissions.deafen_members:
		roles.append('deafen_members')
	if ctx.author.guild_permissions.move_members:
		roles.append('move_members')
	if ctx.author.guild_permissions.use_voice_activation:
		roles.append('use_voice_activation')
	if ctx.author.guild_permissions.change_nickname:
		roles.append('change_nickname')
	if ctx.author.guild_permissions.manage_nicknames:
		roles.append('manage_nicknames')
	if ctx.author.guild_permissions.manage_roles:
		roles.append('manage_roles')
	if ctx.author.guild_permissions.manage_webhooks:
		roles.append('manage_webhooks')
	if ctx.author.guild_permissions.manage_emojis:
		roles.append('manage_emojis')
	return roles