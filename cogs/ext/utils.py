from __future__ import annotations

from typing import List, Type

import discord
import os, sys, json
from discord.ext import commands
from discord import app_commands, Member, Role

from cogs.ext.config_manager import ConfigManager

configManager = ConfigManager("configs/config", "configs/messages",
                              "configs/warnings",
                              "configs/commands", "configs/levels")


async def setup(bot: commands.Bot):
    pass


async def _handleMessageResponse(msg: str | None, embed: discord.Embed | None, button_view: discord.ui.View | None,
                                 channel: discord.TextChannel | None, isEph: bool,
                                 interaction: discord.Interaction = None,
                                 ctx: discord.ext.commands.context.Context | None = None):
    if embed is not None:
        embed.title = embed.title.replace(configManager.getEphPlaceholder(), "")
        if interaction is not None:
            try:
                await interaction.response.send_message(embed=embed, ephemeral=isEph)

            except Exception:
                try:
                    await interaction.channel.send(embed=embed)
                except Exception:
                    pass

        elif ctx is not None:
            try:
                await ctx.reply(embed=embed, ephemeral=isEph)

            except Exception:
                try:
                    await ctx.send(embed=embed)
                except Exception:
                    pass

        if channel is not None:
            try:
                await channel.send(embed=embed)
            except Exception:
                pass

    if msg is not None and len(msg.replace(" ", "")) > 0:
        msg = msg.replace(configManager.getEphPlaceholder(), "")
        if interaction is not None:
            try:
                await interaction.response.send_message(msg, ephemeral=isEph)

            except Exception:
                try:
                    await interaction.channel.send(msg)
                except Exception:
                    pass

        elif ctx is not None:
            try:
                await ctx.reply(msg, ephemeral=isEph)

            except Exception:
                try:
                    await ctx.send(msg)
                except Exception:
                    pass

        if channel is not None:
            try:
                await channel.send(msg)
            except Exception:
                pass

    if button_view is not None:
        if interaction is not None:
            try:
                await interaction.response.send_message(view=button_view(), ephemeral=isEph)

            except Exception:
                try:
                    await interaction.channel.send(view=button_view())
                except Exception:
                    pass

        elif ctx is not None:
            try:
                await ctx.reply(view=button_view(), ephemeral=isEph)

            except Exception:
                try:
                    await ctx.send(view=button_view())
                except Exception:
                    pass

        if channel is not None:
            try:
                await channel.send(view=button_view())
            except Exception:
                pass


async def _sendResponse(interaction: discord.Interaction, mainData: dict, dm_user: discord.User):
    if len(mainData) == 0:
        return
    eph = configManager.getEphPlaceholder()
    if dm_user is None and interaction is not None:
        dm_user = interaction.user

    for message_name, data in mainData.items():
        messages: list = data.get("messages", [])
        embed: discord.Embed | None = data.get("embed", None)
        dm_messages: list = data.get("dm_messages", [])
        dm_embeds: list = data.get("dm_embeds", [])
        dm_buttons: list = data.get("dm_buttons", [])
        channel_embeds: list = data.get("channel_embeds", [])
        channel_messages: list = data.get("channel_messages", [])
        channel_buttons: list = data.get("channel_buttons", [])
        channel: discord.TextChannel | None = data.get("channel", None)
        button_view: discord.ui.View | None = data.get("button", None)

        await _handleMessageResponse(None, embed, None, None, embed is not None
                                     and configManager.isActivePlaceholder(eph)
                                     and eph in embed.title, interaction=interaction)

        for msg in messages:
            await _handleMessageResponse(msg, None, None, None, configManager.isActivePlaceholder(eph)
                                         and eph in msg, interaction=interaction)
        if dm_user is not None:
            for dm_emb in dm_embeds:
                await dm_user.send(embed=dm_emb)

            for dm in dm_messages:
                await dm_user.send(dm)

            for dm_but in dm_buttons:
                await dm_user.send(view=dm_but())

        if channel is not None:
            try:
                for ch_emb in channel_embeds:
                    await channel.send(embed=ch_emb)
            except Exception:
                pass
            try:
                for ch_msg in channel_messages:
                    await channel.send(ch_msg)
            except Exception:
                pass
            try:
                for ch_button in channel_buttons:
                    await channel.send(view=ch_button())
            except Exception:
                pass

        if button_view is not None:
            await _handleMessageResponse(None, None, button_view, None, button_view.is_active_placeholder,
                                         interaction=interaction)


async def _sendResponseCtx(ctx: discord.ext.commands.context.Context | None, mainData: dict, dm_user: discord.User):
    if len(mainData) == 0:
        return
    eph = configManager.getEphPlaceholder()
    if dm_user is None and ctx is not None:
        dm_user = ctx.author

    for message_name, data in mainData.items():
        messages: list = data.get("messages", [])
        embed: discord.Embed | None = data.get("embed", None)
        dm_messages: list = data.get("dm_messages", [])
        dm_embeds: list = data.get("dm_embeds", [])
        dm_buttons: list = data.get("dm_buttons", [])
        channel_embeds: list = data.get("channel_embeds", [])
        channel_messages: list = data.get("channel_messages", [])
        channel_buttons: list = data.get("channel_buttons", [])
        channel: discord.TextChannel | None = data.get("channel", None)
        button_view: discord.ui.View | None = data.get("button", None)

        await _handleMessageResponse(None, embed, None, None, embed is not None
                                     and configManager.isActivePlaceholder(eph)
                                     and eph in embed.title, ctx=ctx)

        for msg in messages:
            await _handleMessageResponse(msg, None, None,
                                         None, configManager.isActivePlaceholder(eph)
                                         and eph in msg, ctx=ctx)

        if dm_user is not None:
            for dm_emb in dm_embeds:
                await dm_user.send(embed=dm_emb)

            for dm in dm_messages:
                await dm_user.send(dm)

            for dm_but in dm_buttons:
                await dm_user.send(view=dm_but())

        if channel is not None:
            try:
                for ch_emb in channel_embeds:
                    await channel.send(embed=ch_emb)
            except Exception:
                pass
            try:
                for ch_msg in channel_messages:
                    await channel.send(ch_msg)
            except Exception:
                pass
            try:
                for ch_button in channel_buttons:
                    await channel.send(view=ch_button())
            except Exception:
                pass

        if button_view is not None:
            await _handleMessageResponse(None, None, button_view,
                                         None, button_view.is_active_placeholder, ctx=ctx)


def _usePlaceholders(msg: str, placeholders: dict) -> str:
    for placeholder, v in placeholders.items():
        if configManager.isActivePlaceholder(placeholder):
            msg = msg.replace(str(placeholder), str(v))
    return msg


def _buildChannelData(bot: commands.Bot, command_name: str, msg: str, placeholders: dict,
                      interaction: discord.Interaction = None,
                      ctx: discord.ext.commands.context.Context | None = None) -> tuple:
    channel_messages: list = configManager.getMessagesByChannel(msg).copy()
    channel_embeds: list = configManager.getEmbedsByChannel(msg).copy()
    channel_buttons: list = configManager.getButtonsByChannel(msg).copy()
    built_channel_embeds = []
    if len(channel_embeds) > 0:
        for emb_name in channel_embeds:
            emb = _buildEmbed(command_name, emb_name, placeholders)
            if emb is not None:
                built_channel_embeds.append(emb.copy())

    built_channel_messages = []
    if len(channel_messages) > 0:
        for msg_name in channel_messages:
            msg_data: list = configManager.getCommandMessages(command_name, msg_name).copy()
            if len(msg_data) > 0:
                for i in range(len(msg_data)):
                    built_channel_messages.append(_usePlaceholders(msg_data[i], placeholders))

    built_channel_buttons = []
    if len(channel_buttons) > 0:
        for buttn_name in channel_buttons:
            res = _buildButtonData(bot, buttn_name, placeholders)
            if res is not None:
                built_channel_buttons.append(res)

    channel_id: int = configManager.getChannelIdByName(msg)

    try:
        if bot is None:
            return (built_channel_embeds, built_channel_messages, None, built_channel_buttons)

        channel: discord.abc.GuildChannel | None = bot.get_channel(channel_id)
        if channel is None:
            if interaction is not None:
                channel = interaction.channel
            elif ctx is not None:
                channel = ctx.channel

        if type(channel) != discord.TextChannel:
            raise Exception()

        return (built_channel_embeds, built_channel_messages, channel, built_channel_buttons)

    except Exception:
        return (built_channel_embeds, built_channel_messages, None, built_channel_buttons)


def _buildMessageData(command_name: str, msg: str, placeholders: dict) -> list:
    message: list = configManager.getCommandMessages(command_name, msg).copy()
    if len(message) > 0:
        for i in range(len(message)):
            message[i] = _usePlaceholders(message[i], placeholders)
    return message


def _buildDMData(bot: commands.Bot, command: str, msg: str, placeholders: dict) -> tuple:
    dm: list = configManager.getDMMessages(msg).copy()
    built_dm_msg = []
    if len(dm) > 0:
        for dm_msg in dm:
            message: list = configManager.getCommandMessages(command, dm_msg).copy()
            for i in range(len(dm)):
                built_dm_msg.append(_usePlaceholders(message[i], placeholders))

    dm_embeds: list = configManager.getDMEmbeds(msg).copy()
    built_dm_embeds = []
    if len(dm_embeds) > 0:
        for emb_name in dm_embeds:
            emb = _buildEmbed(command, emb_name, placeholders)
            if emb is not None:
                built_dm_embeds.append(emb.copy())

    dm_buttons: list = configManager.getDMViews(msg).copy()
    built_dm_buttons = []
    if len(dm_buttons) > 0:
        for dm_button in dm_buttons:
            res = _buildButtonData(bot, dm_button, placeholders)
            if res is not None:
                built_dm_buttons.append(res)

    return (built_dm_msg, built_dm_embeds, built_dm_buttons)


class ViewButton(discord.ui.Button):
    def __init__(self, data: dict, **kwargs):
        super().__init__(**kwargs)
        self.data = data.copy()
        self.args: dict = dict(data['args']).copy()
        # 'idk' -> [1, 2, 3]

        self.actionData: dict = dict()
        # 'idk' -> {'messages' : [....]}

        for action in self.args.keys():
            allActionData: dict = configManager.getActionData(action).copy()
            for actionName in allActionData.keys():
                if action in self.args.keys():
                        value = allActionData[actionName]
                        if type(value) is list:
                            for itemInd, item in enumerate(value):
                                for index, placeholder in enumerate(self.args.get(action)):
                                    value[itemInd] = str(item).replace("/" + str(index + 1) + "/", placeholder)
                        #else:
                        #    value = (str(value).replace("/" + str(index) + "/", placeholder))

            self.actionData[action] = allActionData


    async def handleActionMessages(self, interaction: discord.Interaction, messages_names: list):
        for msg in messages_names:
            await handleMessage(interaction.client, interaction, msg, dm_user=interaction.user)

    async def callback(self, interaction: discord.Interaction):
        for action in self.actionData.keys():
            for doing in self.actionData.get(action).keys():
                if doing == "messages":
                    await self.handleActionMessages(interaction, list(self.actionData.get(action).get("messages")))





class TempView(discord.ui.View):
    is_active_placeholder = False
    allButtonLabels = []
    view = ""
    timeout = None

    def __init__(self):
        super().__init__(timeout=self.timeout)
        if len(self.view) > 0:
            for label in self.allButtonLabels:
                comb = self.view.replace(" ", "") + " " + str(label).replace(" ", "")

                self.add_item(ViewButton(label=label,
                                         style=getattr(discord.ButtonStyle, configManager.getButtonStyle(comb)),
                                         custom_id=configManager.getButtonCustomID(comb),
                                         data={"args": configManager.getButtonArguments(self.view, label)}))

    if timeout is None:
        async def on_timeout(self):
            for child in self.children:
                child.disabled = False


def _buildButtonData(bot: commands.Bot, msg: str, placeholders: dict) -> discord.ui.View | None:
    if not configManager.hasButton(msg):
        return None

    eph = configManager.getEphPlaceholder()
    TempView.view = msg
    TempView.timeout = configManager.getButtonTimeout(msg)
    TempView.allButtonLabels = configManager.getButtonsByView(msg)
    TempView.is_active_placeholder = configManager.isActivePlaceholder(eph) and eph in msg
    return TempView


def _addDefaultPlaceholder(placeholders: dict, interaction: discord.Interaction = None,
                           ctx: discord.ext.commands.context.Context | None = None):
    if interaction is not None:
        if configManager.getXPPlaceholder() not in placeholders.keys():
            placeholders[configManager.getXPPlaceholder()] = str(configManager.getUserXP(interaction.user.id))

        if configManager.getLevelPlaceholder() not in placeholders.keys():
            placeholders[configManager.getLevelPlaceholder()] = str(configManager.getUserLevel(interaction.user.id))

        if configManager.getUsernamePlaceholder() not in placeholders.keys():
            placeholders[configManager.getUsernamePlaceholder()] = interaction.user.name

        if configManager.getNumberPlaceholder() not in placeholders.keys():
            placeholders[configManager.getNumberPlaceholder()] = str(interaction.user.id)

    elif ctx is not None:
        if configManager.getXPPlaceholder() not in placeholders.keys():
            placeholders[configManager.getXPPlaceholder()] = str(configManager.getUserXP(ctx.author.id))

        if configManager.getLevelPlaceholder() not in placeholders.keys():
            placeholders[configManager.getLevelPlaceholder()] = str(configManager.getUserLevel(ctx.author.id))

        if configManager.getUsernamePlaceholder() not in placeholders.keys():
            placeholders[configManager.getUsernamePlaceholder()] = ctx.author.name

        if configManager.getNumberPlaceholder() not in placeholders.keys():
            placeholders[configManager.getNumberPlaceholder()] = str(ctx.author.id)

    return placeholders


def _handleErrorMainBuild(bot: commands.Bot, command_name: str, error_name: str,
                          placeholders: dict, interaction: discord.Interaction = None,
                          ctx: discord.ext.commands.context.Context | None = None):
    if len(error_name.replace(" ", "")) > 0:
        message: list = _buildMessageData(command_name, error_name, placeholders)
        (dm, dm_embeds, dm_buttons) = _buildDMData(bot, command_name, error_name, placeholders)
        if interaction is not None:
            (built_channel_embeds, built_channel_messages, channel, built_channel_buttons) = (
                _buildChannelData(bot, command_name, error_name, placeholders, interaction=interaction))

        elif ctx is not None:
            (built_channel_embeds, built_channel_messages, channel, built_channel_buttons) = (
                _buildChannelData(bot, command_name, error_name, placeholders, ctx=ctx))

        else:
            (built_channel_embeds, built_channel_messages, channel, built_channel_buttons) = (
                _buildChannelData(bot, command_name, error_name, placeholders))

        return {error_name: {"messages": message,
                             "embed": _buildEmbed(command_name, error_name, placeholders),
                             "dm_messages": dm,
                             "dm_embeds": dm_embeds,
                             "dm_buttons": dm_buttons,
                             "channel_embeds": built_channel_embeds,
                             "channel_messages": built_channel_messages,
                             "channel_buttons": built_channel_buttons,
                             "channel": channel,
                             "button": _buildButtonData(bot, error_name, placeholders)}}
    return {}


def _handleMultipleMessages(bot: commands.Bot, command_name: str,
                            placeholders: dict, interaction: discord.Interaction = None,
                            ctx: discord.ext.commands.context.Context | None = None):
    multi_message = dict()

    for msg in configManager.getCommandData(command_name).get("message_names", []):
        message: list = _buildMessageData(command_name, msg, placeholders)
        (dm, dm_embeds, dm_buttons) = _buildDMData(bot, command_name, msg, placeholders)

        if interaction is not None:
            (built_channel_embeds, built_channel_messages, channel, built_channel_buttons) = (
                _buildChannelData(bot, command_name, msg, placeholders, interaction=interaction))

        elif ctx is not None:
            (built_channel_embeds, built_channel_messages, channel, built_channel_buttons) = (
                _buildChannelData(bot, command_name, msg, placeholders, ctx=ctx))

        else:
            (built_channel_embeds, built_channel_messages, channel, built_channel_buttons) = (
                _buildChannelData(bot, command_name, msg, placeholders))

        multi_message[msg] = {"messages": message,
                              "embed": _buildEmbed(command_name, msg, placeholders),
                              "dm_messages": dm,
                              "dm_embeds": dm_embeds,
                              "dm_buttons": dm_buttons,
                              "channel_embeds": built_channel_embeds,
                              "channel_messages": built_channel_messages,
                              "channel_buttons": built_channel_buttons,
                              "channel": channel,
                              "button": _buildButtonData(bot, msg, placeholders)}

    return multi_message


def _MainBuild(bot: commands.Bot, command_name: str, error_name: str = "", placeholders: dict = dict(),
               interaction: discord.Interaction = None,
               ctx: discord.ext.commands.context.Context | None = None) -> dict:
    placeholders = _addDefaultPlaceholder(placeholders, interaction=interaction, ctx=ctx)
    error_data = _handleErrorMainBuild(bot, command_name, error_name, placeholders,
                                       interaction=interaction, ctx=ctx)
    return _handleMultipleMessages(bot, command_name, placeholders,
                                   interaction=interaction, ctx=ctx) if len(error_data) == 0 else error_data


async def handleMessage(bot: commands.Bot, interaction: discord.Interaction, command_name: str, error_name: str = "",
                        placeholders: dict = dict(), dm_user: discord.User = None):
    mainData: dict = _MainBuild(bot, command_name, error_name, placeholders, interaction=interaction)
    await _sendResponse(interaction, mainData, dm_user)


async def handleMessageCtx(bot: commands.Bot, ctx: discord.ext.commands.context.Context | None, command_name: str,
                           error_name: str = "",
                           placeholders: dict = dict(), dm_user: discord.User = None):
    mainData: dict = _MainBuild(bot, command_name, error_name, placeholders, ctx=ctx)
    await _sendResponseCtx(ctx, mainData, dm_user)


def _buildEmbed(command: str, message_key: str, placeholders: dict) -> discord.Embed | None:
    try:
        data: dict = configManager.getCommandEmbeds(command, message_key)

        title: str = str(data.get(configManager.getEmbedTitle(), configManager.getEmbedTitle()))
        author_name: str = str(data.get(configManager.getEmbedAuthorName(), configManager.getEmbedAuthorName()))
        author_url: str = str(data.get(configManager.getEmbedAuthorUrl(), configManager.getEmbedAuthorUrl()))
        author_icon_url: str = str(
            data.get(configManager.getEmbedAuthorIconUrl(), configManager.getEmbedAuthorIconUrl()))
        footer_text: str = str(data.get(configManager.getEmbedFooter(), configManager.getEmbedFooter()))
        footer_icon_url: str = str(
            data.get(configManager.getEmbedFooterIconUrl(), configManager.getEmbedFooterIconUrl()))
        image_url: str = str(data.get(configManager.getEmbedImageUrl(), configManager.getEmbedImageUrl()))
        desc: str = str(data.get(configManager.getEmbedDescription(), configManager.getEmbedDescription()))
        colour: str = str(data.get(configManager.getEmbedColor(), configManager.getEmbedColor()))

        title = _usePlaceholders(title, placeholders)
        author_name = _usePlaceholders(author_name, placeholders)
        author_url = _usePlaceholders(author_url, placeholders)
        author_icon_url = _usePlaceholders(author_icon_url, placeholders)
        footer_text = _usePlaceholders(footer_text, placeholders)
        footer_icon_url = _usePlaceholders(footer_icon_url, placeholders)
        image_url = _usePlaceholders(image_url, placeholders)
        desc = _usePlaceholders(desc, placeholders)

        embed = discord.Embed(title=title,
                              colour=discord.Colour.random() if colour == "random" else discord.Colour.from_str(colour),
                              description=desc)

        embed.set_author(name=author_name,
                         url=author_url,
                         icon_url=author_icon_url)

        embed.set_footer(text=footer_text,
                         icon_url=footer_icon_url)

        embed.set_image(url=image_url)

        for k, v in data.get(configManager.getEmbedFields()).items():
            embed.add_field(name=k, value=v)

        return embed.copy()

    except Exception:
        return None


def getMember(interaction: discord.Interaction, member_id: int) -> Member | None:
    if member_id == 0:
        return None
    return interaction.guild.get_member(member_id)


async def handleInvalidMember(bot: commands.Bot, interaction: discord.Interaction, command: str):
    await handleMessage(bot, interaction, command,
                        error_name=configManager.getInvalidMemberKey(),
                        placeholders={configManager.getUsernamePlaceholder(): configManager.getInvalidMember()})


async def handleInvalidRole(bot: commands.Bot, interaction: discord.Interaction, command: str):
    await handleMessage(bot, interaction, command,
                        error_name=configManager.getInvalidRoleKey(),
                        placeholders={configManager.getRoleNamePlaceholder(): configManager.getInvalidRole()})


async def handleInvalidArg(bot: commands.Bot, interaction: discord.Interaction, command: str):
    await handleMessage(bot, interaction, command,
                        error_name=configManager.getInvalidArgsKey(),
                        placeholders={configManager.getErrorPlaceholder(): configManager.getInvalidArg()})


async def handleErrors(bot: commands.Bot, interaction: discord.Interaction, command: str, error):
    await handleMessage(bot, interaction, command,
                        error_name=configManager.getUnknownErrorKey(),
                        placeholders={configManager.getErrorPlaceholder(): error})


async def handleInvalidChannels(bot: commands.Bot, interaction: discord.Interaction, command: str):
    await handleMessage(bot, interaction, command,
                        error_name=configManager.getInvalidChannelKey(),
                        placeholders={configManager.getChannelNamePlaceholder(): configManager.getInvalidChannel()})


def get_role_id_from_mention(role_mention: str) -> int:
    try:
        return int(role_mention.replace("<@&", "")[:-1])
    except Exception:
        return 0


def get_member_id_from_mention(member_mention: str) -> int:
    try:
        return int(member_mention.replace("<@", "")[:-1])
    except Exception:
        return 0


def getRole(interaction: discord.Interaction, role_id: int) -> None | discord.Role:
    if role_id == 0:
        return None
    return interaction.guild.get_role(role_id)


def get_channel_id_from_mention(channel_mention: str) -> int:
    try:
        return int(channel_mention.replace("<#", "")[:-1])
    except Exception:
        return 0


def getVoiceChannel(interaction: discord.Interaction, channel_id: int) -> None | discord.VoiceChannel:
    if channel_id == 0:
        return None
    channel = interaction.guild.get_channel(channel_id)
    return channel if type(channel) is discord.VoiceChannel else None


def addWordsToBlacklist(words: list):
    configManager.getBlacklistedWords().extend(words)
    configManager.updateBlacklistWords(configManager.getBlacklistedWords())
    configManager.saveConfigJSON()


def removeWordsFromBlacklist(words: list):
    configManager.updateBlacklistWords([i for i in configManager.getBlacklistedWords() if i not in words])
    configManager.saveConfigJSON()


def getRoleIdFromRoles(roles: List[Role]) -> list:
    userRolesId = []
    for r in roles:
        userRolesId.append(r.id)
    return userRolesId


def getUserWarningLevel(user: discord.Member) -> int:
    lastIndex = 0
    for i in range(1, configManager.getWarningLevels() + 1):
        warning_data: dict = configManager.getWarningDataForLevel(i)
        if len(warning_data) == 0:
            continue

        roles_id: list | None = warning_data.get("roles_id", None)
        userRolesId = getRoleIdFromRoles(user.roles)
        if roles_id is not None:
            roles_id.sort()
            userRolesId.sort()

            if roles_id == userRolesId and lastIndex < i:
                lastIndex = i
    return lastIndex


def anyRolesContains(roles_id: list, roles_id2: list) -> bool:
    for role_id in roles_id:
        if role_id in roles_id2:
            return True
    return False


def getWarningRolesFromLevel(interaction: discord.Interaction, level: int) -> List[Role]:
    warning_data: dict = configManager.getWarningDataForLevel(level)

    warningRoles = []
    if len(warning_data) == 0:
        return warningRoles

    roles_id: list | None = warning_data.get("roles_id", None)

    if roles_id is not None:
        for r_id in roles_id:
            r = interaction.guild.get_role(r_id)
            if r is not None:
                warningRoles.append(r)
    return warningRoles


def isUserRestricted(interaction: discord.Interaction, commandName: str) -> str:
    res = configManager.getCommandRestrictions(commandName)
    reason = ""
    if res.get("all", None) is not None:
        if res.get("all"):
            return reason
        else:
            reason += "all;"

    usersId: list | None = res.get("users_id", None)
    if usersId is not None and interaction.user.id not in usersId:
        reason += "user id;"

    userRoleId: list = getRoleIdFromRoles(interaction.user.roles)
    anyRolesId: list | None = res.get("any_roles_id", None)
    if anyRolesId is not None and anyRolesContains(anyRolesId, userRoleId):
        reason += "any roles;"

    allRolesId: list | None = res.get("all_roles_id", None)
    if allRolesId is not None:
        allRolesId.sort()
        userRoleId.sort()
        if allRolesId != userRoleId:
            reason += "all roles;"

    channels_id = res.get("channels_id", None)
    if channels_id is not None and interaction.channel.id not in channels_id:
        reason += "channel id;"

    return reason


def isUserRestrictedCtx(ctx: discord.ext.commands.context.Context, commandName: str) -> str:
    res = configManager.getCommandRestrictions(commandName)
    reason = ""
    if res.get("all", None) is not None:
        if res.get("all"):
            return reason
        else:
            reason += "all;"

    usersId: list | None = res.get("users_id", None)
    if usersId is not None and ctx.author.id not in usersId:
        reason += "user id;"

    userRoleId: list = getRoleIdFromRoles(ctx.author.roles)
    anyRolesId: list | None = res.get("any_roles_id", None)
    if anyRolesId is not None and anyRolesContains(anyRolesId, userRoleId):
        reason += "any roles;"

    allRolesId: list | None = res.get("all_roles_id", None)
    if allRolesId is not None:
        allRolesId.sort()
        userRoleId.sort()
        if allRolesId != userRoleId:
            reason += "all roles;"

    channels_id = res.get("channels_id", None)
    if channels_id is not None and ctx.channel.id not in channels_id:
        reason += "channel id;"

    return reason


async def handleRestricted(bot: commands.Bot, interaction: discord.Interaction, commandName: str) -> bool:
    reason = isUserRestricted(interaction, commandName)
    if len(reason) > 0:
        await handleMessage(bot, interaction, commandName,
                            error_name=configManager.getRestrictedKey(),
                            placeholders={configManager.getReasonPlaceholder(): reason})

        return True
    return False


async def handleRestrictedCtx(bot: commands.Bot, ctx: discord.ext.commands.context.Context, commandName: str) -> bool:
    reason = isUserRestrictedCtx(ctx, commandName)
    if len(reason) > 0:
        await handleMessageCtx(bot, ctx, commandName,
                               error_name=configManager.getRestrictedKey(),
                               placeholders={configManager.getReasonPlaceholder(): reason})

        return True
    return False


def getUserLevel(user: discord.Member, isMax: bool) -> int:
    if isMax:
        res: int | None = configManager.getLevelExceptionalUserMax(user.id)
    else:
        res: int | None = configManager.getLevelExceptionalUserMin(user.id)

    if res is not None:
        return int(res)

    userRoleIds: list = getRoleIdFromRoles(user.roles)
    if len(userRoleIds) == 0:
        return configManager.getLevelGlobalMax() if isMax else configManager.getLevelGlobalMin()

    biggest_limit: int | None = None
    for role_id in userRoleIds:
        if isMax:
            role_max: int | None = configManager.getLevelExceptionalRoleMax(role_id)
            if (role_max is not None) and ((biggest_limit is None) or (role_max > biggest_limit)):
                biggest_limit = role_max
        else:
            role_max: int | None = configManager.getLevelExceptionalRoleMin(role_id)
            if (role_max is not None) and ((biggest_limit is None) or (role_max < biggest_limit)):
                biggest_limit = role_max

    return biggest_limit if biggest_limit is not None else (
        configManager.getLevelGlobalMax() if isMax else configManager.getLevelGlobalMin())


def getLevelByXP(xp: int):
    level = 0
    while True:
        if xp == configManager.getLevelXP(level) or xp < configManager.getLevelXP(level + 1):
            break
        level += 1
    return level


def setUserXP(user: discord.Member, xp: int):
    maxLevel = getUserLevel(user, True)
    minLevel = getUserLevel(user, False)
    currentLevel = configManager.getUserLevel(user.id)

    if minLevel > currentLevel or currentLevel > maxLevel or maxLevel == minLevel:
        configManager.setUserLevel(user.id, minLevel)
        configManager.setUserXP(user.id, configManager.getLevelXP(minLevel))
        configManager.saveLevelJSON()
        return

    configManager.setUserXP(user.id, xp)
    configManager.setUserLevel(user.id, getLevelByXP(xp))

    configManager.saveLevelJSON()


def handleUserLevelingOnMessage(user: discord.Member):
    maxLevel = getUserLevel(user, True)
    minLevel = getUserLevel(user, False)
    currentLevel = configManager.getUserLevel(user.id)
    nextLevel = currentLevel + 1
    totalXP = configManager.getUserXP(user.id) + configManager.getXPPerMessages()

    if minLevel > currentLevel or currentLevel > maxLevel or maxLevel == minLevel:
        configManager.setUserLevel(user.id, minLevel)
        configManager.setUserXP(user.id, configManager.getLevelXP(minLevel))
        configManager.saveLevelJSON()
        return

    configManager.setUserXP(user.id, totalXP)
    if totalXP >= configManager.getLevelXP(nextLevel) and minLevel <= nextLevel <= maxLevel:
        configManager.setUserLevel(user.id, nextLevel)

    configManager.saveLevelJSON()
