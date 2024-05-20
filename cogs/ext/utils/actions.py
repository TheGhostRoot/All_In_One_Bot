from __future__ import annotations

import asyncio
import threading
from datetime import datetime
from typing import List

import discord
from discord import Member
from discord.ext import commands
import cogs.ext.utils.utils as utils
import cogs.ext.utils.messages as messages


async def handleActionMessages(interaction: discord.Interaction, messages_names: list):
    for msg in messages_names:
        await messages.handleMessage(interaction.client, interaction,
                                     usePlaceholders(msg, interaction), DMUser=interaction.user)


async def handleCogCommandExecution(cog: commands.Cog, interaction: discord.Interaction,
                                    commandName: str,
                                    command: discord.app_commands.commands.ContextMenu, finalArgs: list):
    for co in cog.get_app_commands():
        if co.name == commandName:
            try:
                await command.callback(cog, interaction, *finalArgs)
            except Exception as e:
                await messages.handleErrors(interaction.client, interaction, commandName, e)
            break


def usePlaceholders(msg: str, interaction: discord.Interaction) -> str:
    msg = msg.replace("@user.id", str(interaction.user.id))
    msg = msg.replace("@user.name", str(interaction.user.name))
    msg = msg.replace("@user.avatar.is_animated", str(interaction.user.avatar.is_animated()))

    msg = msg.replace("@channel.id", str(interaction.channel.id))
    msg = msg.replace("@channel.name", str(interaction.channel.name))
    msg = msg.replace("@channel.type", str(interaction.channel.type.name))

    botUser: discord.ClientUser | None = interaction.client
    if botUser is not None:
        msg = msg.replace("@bot.id", str(botUser.id))
        msg = msg.replace("@bot.name", str(botUser.name))
        msg = msg.replace("@bot.latency", str(interaction.client.latency))

    msg = msg.replace("@guild.id", str(interaction.guild.id))
    msg = msg.replace("@guild.name", str(interaction.guild.name))

    for roleManager in utils.configManager.getRoleManagements():
        botRoleManager: str = "@bot." + roleManager
        userRoleManager: str = "@user." + roleManager
        guildRoleManager: str = "@guild." + roleManager
        if botRoleManager in msg and botUser is not None:
            botMember: Member | None = interaction.guild.get_member(botUser.id)
            if botMember is not None and checkIf(roleManager, utils.getRoleIdFromRoles(botMember.roles.copy()).copy()):
                msg = msg.replace(botRoleManager, roleManager)

        elif userRoleManager in msg:
            if checkIf(roleManager, utils.getRoleIdFromRoles(interaction.user.roles.copy()).copy()):
                msg = msg.replace(userRoleManager, roleManager)

        elif guildRoleManager in msg:
            if checkIf(roleManager, utils.getRoleIdFromRoles(list(interaction.guild.roles).copy()).copy()):
                msg = msg.replace(userRoleManager, roleManager)
    return msg


def checkIf(roleManager: str, hasRoles: list) -> bool:
    return (utils.allRolesContains(utils.configManager.getAllRolesIDByRoleManager(roleManager).copy(), hasRoles) or
            utils.anyRolesContains(hasRoles, utils.configManager.getAnyRolesIDByRoleManager(roleManager).copy()))


async def handleActionCommands(interaction: discord.Interaction, commandsData: dict):
    for command in commandsData.keys():
        comm: discord.app_commands.commands.ContextMenu | None = interaction.client.tree.get_command(command)
        if comm is not None:
            final_args = []
            for arg in commandsData.get(command):
                final_args.append(usePlaceholders(arg, interaction))

            for name, file_name in utils.configManager.getCogData().items():
                cog: commands.Cog = interaction.client.get_cog(name)
                executed = False
                for cogCommand in cog.get_app_commands():
                    if cogCommand.name == comm.name:
                        try:
                            await interaction.client.load_extension(f"cogs.{file_name}")
                        except commands.ExtensionAlreadyLoaded:
                            await handleCogCommandExecution(cog, interaction, command, comm, final_args)
                        executed = True
                        break
                if executed:
                    break


async def handleUser(interaction: discord.Interaction, userData: dict):
    for userDo in userData.keys():
        userDoData: dict = dict(userData.get(userDo, {}))
        duration: int = int(userDoData.get("duration", -1))
        loop = asyncio.get_running_loop()
        if userDo == "ban":
            res: bool = await utils.banUser(interaction.user, str(userDoData.get("reason", "")))
            if not res:
                continue
            if duration > 0:
                async def wait(duration2: int, reason: str, user: discord.Member):
                    try:
                        await asyncio.sleep(duration2)
                        await utils.unbanUser(user, reason=reason)
                    except Exception:
                        pass

                threading.Thread(target=utils.separateThread, args=(loop, wait, duration,
                                                                    str(userDoData.get("unban_reason", "")),
                                                                    interaction.user), daemon=True).start()
        elif userDo == "unban":
            member: discord.Member | None = utils.getMember(interaction,
                                                            utils.getMemberIdFromMention(
                                                                str(userDoData.get("id", "0"))))
            if member is not None:
                res: bool = await utils.unbanUser(member, str(userDoData.get("reason", "")))
                if not res:
                    continue
                duration: int = int(userDoData.get("duration", -1))
                if duration > 0:
                    async def wait(duration2: int, member2: discord.Member, reason: str):
                        try:
                            await asyncio.sleep(duration2)
                            await utils.banUser(member2, reason)
                        except Exception:
                            pass

                    threading.Thread(target=utils.separateThread, args=(loop, wait, duration, member,
                                                                        str(userDoData.get("ban_reason", ""))),
                                     daemon=True).start()
        elif userDo == "kick":
            await utils.kickUser(interaction.user, reason=str(userDoData.get("kick_reason", "")))
        elif userDo == "role_add":
            role: discord.Role | None = utils.getRole(interaction,
                                                      utils.getRoleIdFromMention(
                                                          str(userDoData.get("id", 0))))
            if role is not None:
                res: bool = await utils.addRole(interaction.user, role, reason=str(userDoData.get("reason", "")))
                if not res:
                    continue
                if duration > 0:
                    async def wait(duration2: int, reason: str, user: discord.Member, userRole: discord.Role):
                        try:
                            await asyncio.sleep(duration2)
                            await utils.removeRole(user, userRole, reason=reason)
                        except Exception:
                            pass

                    threading.Thread(target=utils.separateThread, args=(loop, wait, duration,
                                                                        str(userDoData.get("role_remove_reason",
                                                                                           "")),
                                                                        interaction.user, role),
                                     daemon=True).start()
        elif userDo == "role_remove":
            role: discord.Role | None = utils.getRole(interaction,
                                                      utils.getRoleIdFromMention(
                                                          str(userDoData.get("id", 0))))
            if role is not None:
                res: bool = await utils.removeRole(interaction.user, role, reason=str(userDoData.get("reason", "")))
                if not res:
                    continue
                if duration > 0:
                    async def wait(duration2: int, reason: str, user: discord.Member, userRole: discord.Role):
                        try:
                            await asyncio.sleep(duration2)
                            await utils.addRole(user, userRole, reason=reason)
                        except Exception:
                            pass

                    threading.Thread(target=utils.separateThread, args=(loop, wait, duration,
                                                                        str(userDoData.get("role_add_reason",
                                                                                           "")),
                                                                        interaction.user, role),
                                     daemon=True).start()
        elif userDo == "timeout":
            res: bool = await utils.timeoutUser(interaction.user, datetime.strptime(str(userDoData
                                                                                        .get("reason", "")),
                                                                                    "YYYY-MM-DDTHH:MM:SS"),
                                                reason=str(userDoData.get("reason", "")))
            if not res:
                continue
            duration: int = int(userDoData.get("duration", -1))
            if duration > 0:
                async def wait(duration2: int, reason: str, user: discord.Member):
                    try:
                        await asyncio.sleep(duration2)
                        await utils.removeTimeoutUser(user, reason=reason)
                    except Exception:
                        pass

                threading.Thread(target=utils.separateThread, args=(loop, wait, duration,
                                                                    str(userDoData.get("timeout_remove_reason",
                                                                                       "")),
                                                                    interaction.user), daemon=True).start()
        elif userDo == "deafen":
            res: bool = await utils.userDeafen(interaction.user, True,
                                               reason=str(userDoData.get("reason", "")))
            if not res:
                continue

            duration: int = int(userDoData.get("duration", -1))
            if duration > 0:
                async def wait(duration2: int, reason: str, user: discord.Member):
                    try:
                        await asyncio.sleep(duration2)
                        await utils.userDeafen(user, False, reason=reason)
                    except Exception:
                        pass

                threading.Thread(target=utils.separateThread, args=(loop, wait, duration,
                                                                    str(userDoData.get("deafen_remove_reason", "")),
                                                                    interaction.user), daemon=True).start()
        elif userDo == "deafen_remove":
            res: bool = await utils.userDeafen(interaction.user, False,
                                               reason=str(userDoData.get("reason", "")))
            if not res:
                continue
            duration: int = int(userDoData.get("duration", -1))
            if duration > 0:
                async def wait(duration2: int, reason: str, user: discord.Member):
                    try:
                        await asyncio.sleep(duration2)
                        await utils.userDeafen(user, True, reason=reason)
                        await user.edit(deafen=True, reason=reason)
                    except Exception:
                        pass

                threading.Thread(target=utils.separateThread, args=(loop, wait, duration,
                                                                    str(userDoData.get("deafen_reason", "")),
                                                                    interaction.user), daemon=True).start()
        elif userDo == "mute":
                res: bool = await utils.userMute(interaction.user, True,
                                                 reason=str(userDoData.get("reason", "")))
                if not res:
                    continue
                duration: int = int(userDoData.get("duration", -1))
                if duration > 0:
                    async def wait(duration2: int, reason: str, user: discord.Member):
                        try:
                            await asyncio.sleep(duration2)
                            await utils.userMute(user, False, reason=reason)
                        except Exception:
                            pass

                    threading.Thread(target=utils.separateThread, args=(loop, wait, duration,
                                                                        str(userDoData.get("mute_remove_reason", "")),
                                                                        interaction.user), daemon=True).start()
        elif userDo == "mute_remove":
                res: bool = await utils.userMute(interaction.user, False,
                                                 reason=str(userDoData.get("reason", "")))
                if not res:
                    continue
                duration: int = int(userDoData.get("duration", -1))
                if duration > 0:
                    async def wait(duration2: int, reason: str, user: discord.Member):
                        try:
                            await asyncio.sleep(duration2)
                            await utils.userMute(user, True, reason=reason)
                        except Exception:
                            pass

                    threading.Thread(target=utils.separateThread, args=(loop, wait, duration,
                                                                        str(userDoData.get("mute_reason", "")),
                                                                        interaction.user), daemon=True).start()


async def handleGuild(interaction: discord.Interaction, guildData: dict):
    for guildToDo in guildData.keys():
        loop = asyncio.get_running_loop()
        # TODO finish this
        if guildToDo == "role_create":
            for rolesToCreate in list(guildData.get(guildToDo, [])):
                duration: int = int(rolesToCreate.get("duration", -1))
                role = await utils.createRoleWithDisplayIcon(rolesToCreate, interaction.guild)
                if role is None:
                    role = await utils.createRoleNoDisplayIcon(rolesToCreate, interaction.guild)
                    if role is None:
                        continue

                if duration > 0:
                    async def wait(duration2: int, roleToDelete: discord.Role, reason: str):
                        try:
                            await asyncio.sleep(duration2)
                            await utils.deleteRole(roleToDelete, reason=reason)
                        except Exception:
                            pass

                    threading.Thread(target=utils.separateThread, args=(loop, wait, duration, role,
                                                                        rolesToCreate.get("delete_reason", "")),
                                     daemon=True).start()
        elif guildToDo == "role_delete":
            for rolesToDelete in list(guildData.get(guildToDo, [])):
                duration: int = int(rolesToDelete.get("duration", -1))
                roles: list = await utils.deleteRole(rolesToDelete, interaction.guild)
                if len(roles) == 0:
                    continue

                if duration > 0:
                    async def wait(duration2: int, guild: discord.Guild, rolesToCreate2: List[discord.Role],
                                   reason: str, give_back_roles_to_users: bool):
                        try:
                            await asyncio.sleep(duration2)
                            for roleToCreate in rolesToCreate2:
                                roleData: dict = utils.getRoleData(roleToCreate)
                                roleData["reason"] = reason
                                if not give_back_roles_to_users:
                                    roleData.pop("users")
                                roleCreated = await utils.createRoleWithDisplayIcon(roleData, guild)
                                if roleCreated is None:
                                    roleCreated = await utils.createRoleNoDisplayIcon(roleData, guild)
                                    if roleCreated is None:
                                        continue

                        except Exception:
                            pass

                    threading.Thread(target=utils.separateThread, args=(loop, wait, duration, interaction.guild,
                                                                        roles,
                                                                        str(rolesToDelete.get("create_reason", "")),
                                                                        bool(rolesToDelete.get(
                                                                            "give_back_roles_to_users", False))),
                                     daemon=True).start()


async def handleAllActions(actionData: dict, interaction: discord.Interaction):
    for action in actionData.keys():
        for doing in actionData.get(action).keys():
            if doing == "messages":
                await handleActionMessages(interaction, list(actionData.get(action, {}).get(doing, [])).copy())

            elif doing == "commands":
                await handleActionCommands(interaction, dict(actionData.get(action, {}).get(doing, {})).copy())

            elif doing == "user":
                await handleUser(interaction, dict(actionData.get(action, {}).get(doing, {})).copy())

            elif doing == "guild":
                await handleGuild(interaction, dict(actionData.get(action, {}).get(doing, {})).copy())