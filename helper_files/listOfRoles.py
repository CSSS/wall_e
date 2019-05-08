# list of possible roles to check can be pulled from here
# https://discordpy.readthedocs.io/en/rewrite/api.html#discord.Permissions


async def getListOfUserPerms(ctx, userID=False):
    if userID is not False:
        userPermToCheck = ctx.guild.get_member(id)
    else:
        userPermToCheck = ctx.author
    roles = []
    if userPermToCheck.guild_permissions.create_instant_invite:
        roles.append('create_instant_invite')
    if userPermToCheck.guild_permissions.kick_members:
        roles.append('kick_members')
    if userPermToCheck.guild_permissions.ban_members:
        roles.append('ban_members')
    if userPermToCheck.guild_permissions.administrator:
        roles.append('administrator')
    if userPermToCheck.guild_permissions.manage_channels:
        roles.append('manage_channels')
    if userPermToCheck.guild_permissions.manage_guild:
        roles.append('manage_guild')
    if userPermToCheck.guild_permissions.add_reactions:
        roles.append('add_reactions')
    if userPermToCheck.guild_permissions.view_audit_log:
        roles.append('view_audit_log')
    if userPermToCheck.guild_permissions.priority_speaker:
        roles.append('priority_speaker')
    if userPermToCheck.guild_permissions.read_messages:
        roles.append('read_messages')
    if userPermToCheck.guild_permissions.send_messages:
        roles.append('send_messages')
    if userPermToCheck.guild_permissions.send_tts_messages:
        roles.append('send_tts_messages')
    if userPermToCheck.guild_permissions.manage_messages:
        roles.append('manage_messages')
    if userPermToCheck.guild_permissions.embed_links:
        roles.append('embed_links')
    if userPermToCheck.guild_permissions.attach_files:
        roles.append('attach_files')
    if userPermToCheck.guild_permissions.read_message_history:
        roles.append('read_message_history')
    if userPermToCheck.guild_permissions.mention_everyone:
        roles.append('mention_everyone')
    if userPermToCheck.guild_permissions.external_emojis:
        roles.append('external_emojis')
    if userPermToCheck.guild_permissions.connect:
        roles.append('connect')
    if userPermToCheck.guild_permissions.speak:
        roles.append('speak')
    if userPermToCheck.guild_permissions.mute_members:
        roles.append('mute_members')
    if userPermToCheck.guild_permissions.deafen_members:
        roles.append('deafen_members')
    if userPermToCheck.guild_permissions.move_members:
        roles.append('move_members')
    if userPermToCheck.guild_permissions.use_voice_activation:
        roles.append('use_voice_activation')
    if userPermToCheck.guild_permissions.change_nickname:
        roles.append('change_nickname')
    if userPermToCheck.guild_permissions.manage_nicknames:
        roles.append('manage_nicknames')
    if userPermToCheck.guild_permissions.manage_roles:
        roles.append('manage_roles')
    if userPermToCheck.guild_permissions.manage_webhooks:
        roles.append('manage_webhooks')
    if userPermToCheck.guild_permissions.manage_emojis:
        roles.append('manage_emojis')
    return roles
