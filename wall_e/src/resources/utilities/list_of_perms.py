# list of possible roles to check can be pulled from here
# https://discordpy.readthedocs.io/en/rewrite/api.html#discord.Permissions


async def get_list_of_user_permissions(ctx, user_id=False):
    if user_id is not False:
        user_perm_to_check = ctx.guild.get_member(id)
    else:
        user_perm_to_check = ctx.author
    roles = []
    if user_perm_to_check.guild_permissions.create_instant_invite:
        roles.append('create_instant_invite')
    if user_perm_to_check.guild_permissions.kick_members:
        roles.append('kick_members')
    if user_perm_to_check.guild_permissions.ban_members:
        roles.append('ban_members')
    if user_perm_to_check.guild_permissions.administrator:
        roles.append('administrator')
    if user_perm_to_check.guild_permissions.manage_channels:
        roles.append('manage_channels')
    if user_perm_to_check.guild_permissions.manage_guild:
        roles.append('manage_guild')
    if user_perm_to_check.guild_permissions.add_reactions:
        roles.append('add_reactions')
    if user_perm_to_check.guild_permissions.view_audit_log:
        roles.append('view_audit_log')
    if user_perm_to_check.guild_permissions.priority_speaker:
        roles.append('priority_speaker')
    if user_perm_to_check.guild_permissions.read_messages:
        roles.append('read_messages')
    if user_perm_to_check.guild_permissions.send_messages:
        roles.append('send_messages')
    if user_perm_to_check.guild_permissions.send_tts_messages:
        roles.append('send_tts_messages')
    if user_perm_to_check.guild_permissions.manage_messages:
        roles.append('manage_messages')
    if user_perm_to_check.guild_permissions.embed_links:
        roles.append('embed_links')
    if user_perm_to_check.guild_permissions.attach_files:
        roles.append('attach_files')
    if user_perm_to_check.guild_permissions.read_message_history:
        roles.append('read_message_history')
    if user_perm_to_check.guild_permissions.mention_everyone:
        roles.append('mention_everyone')
    if user_perm_to_check.guild_permissions.external_emojis:
        roles.append('external_emojis')
    if user_perm_to_check.guild_permissions.connect:
        roles.append('connect')
    if user_perm_to_check.guild_permissions.speak:
        roles.append('speak')
    if user_perm_to_check.guild_permissions.mute_members:
        roles.append('mute_members')
    if user_perm_to_check.guild_permissions.deafen_members:
        roles.append('deafen_members')
    if user_perm_to_check.guild_permissions.move_members:
        roles.append('move_members')
    if user_perm_to_check.guild_permissions.use_voice_activation:
        roles.append('use_voice_activation')
    if user_perm_to_check.guild_permissions.change_nickname:
        roles.append('change_nickname')
    if user_perm_to_check.guild_permissions.manage_nicknames:
        roles.append('manage_nicknames')
    if user_perm_to_check.guild_permissions.manage_roles:
        roles.append('manage_roles')
    if user_perm_to_check.guild_permissions.manage_webhooks:
        roles.append('manage_webhooks')
    if user_perm_to_check.guild_permissions.manage_emojis:
        roles.append('manage_emojis')
    return roles
