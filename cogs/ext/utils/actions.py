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
        user = interaction.user
        if userDo == "ban":
            res: bool = await utils.banUser(user, str(userDoData.get("reason", "")))
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
                                                                    user), daemon=True).start()
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
            await utils.kickUser(user, reason=str(userDoData.get("kick_reason", "")))
        elif userDo == "role_add":
            role: discord.Role | None = utils.getRole(interaction,
                                                      utils.getRoleIdFromMention(
                                                          str(userDoData.get("id", 0))))
            if role is not None:
                res: bool = await utils.addRole(user, role, reason=str(userDoData.get("reason", "")))
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
                                                                        user, role),
                                     daemon=True).start()
        elif userDo == "role_remove":
            role: discord.Role | None = utils.getRole(interaction,
                                                      utils.getRoleIdFromMention(
                                                          str(userDoData.get("id", 0))))
            if role is not None:
                res: bool = await utils.removeRole(user, role, reason=str(userDoData.get("reason", "")))
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
                                                                        user, role),
                                     daemon=True).start()
        elif userDo == "timeout":
            res: bool = await utils.timeoutUser(user, datetime.strptime(str(userDoData
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
                                                                    user), daemon=True).start()
        elif userDo == "deafen":
            res: bool = await utils.userDeafen(user, True,
                                               reason=str(userDoData.get("reason", "")))
            if not res:
                continue

            duration: int = int(userDoData.get("duration", -1))
            if duration > 0:
                async def wait(duration2: int, reason: str, userD: discord.Member):
                    try:
                        await asyncio.sleep(duration2)
                        await utils.userDeafen(userD, False, reason=reason)
                    except Exception:
                        pass

                threading.Thread(target=utils.separateThread, args=(loop, wait, duration,
                                                                    str(userDoData.get("deafen_remove_reason", "")),
                                                                    user), daemon=True).start()
        elif userDo == "deafen_remove":
            res: bool = await utils.userDeafen(user, False,
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
                                                                    user), daemon=True).start()
        elif userDo == "mute":
            res: bool = await utils.userMute(user, True,
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
                                                                    user), daemon=True).start()
        elif userDo == "mute_remove":
            res: bool = await utils.userMute(user, False,
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
                                                                    user), daemon=True).start()


async def handleGuild(interaction: discord.Interaction, guildData: dict):
    for guildToDo in guildData.keys():
        loop = asyncio.get_running_loop()
        # TODO finish this
        guild = interaction.guild
        if guildToDo == "role_create":
            for rolesToCreate in list(guildData.get(guildToDo, [])):
                duration: int = int(rolesToCreate.get("duration", -1))
                role = await utils.createRoleWithDisplayIcon(rolesToCreate, guild)
                if role is None:
                    role = await utils.createRoleNoDisplayIcon(rolesToCreate, guild)
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
                roles: list = await utils.deleteRole(rolesToDelete, guild)
                if len(roles) == 0:
                    continue

                if duration > 0:
                    async def wait(duration2: int, guildD: discord.Guild, rolesToCreate2: List[discord.Role],
                                   reason: str, give_back_roles_to_users: bool, give_back_reason: str):
                        try:
                            await asyncio.sleep(duration2)
                            for roleToCreate in rolesToCreate2:
                                roleData: dict = utils.getRoleData(roleToCreate)
                                roleData["reason"] = reason
                                if not give_back_roles_to_users:
                                    roleData.pop("users")
                                roleCreated = await utils.createRoleWithDisplayIcon(roleData, guildD)
                                if roleCreated is None:
                                    roleCreated = await utils.createRoleNoDisplayIcon(roleData, guildD)
                                    if roleCreated is None:
                                        continue
                                if "users" not in roleData.keys() or len(roleData.get("users", [])) == 0:
                                    continue
                                for userId in roleData.get("users", []):
                                    member: discord.Member | None = utils.getMemberGuild(guildD, userId)
                                    if member is None:
                                        continue
                                    await utils.addRole(member, roleCreated, reason=give_back_reason)
                        except Exception:
                            pass

                    threading.Thread(target=utils.separateThread, args=(loop, wait, duration, guild,
                                                                        roles,
                                                                        str(rolesToDelete.get("create_reason", "")),
                                                                        bool(rolesToDelete.get(
                                                                            "give_back_roles_to_users", False)),
                                                                        str(rolesToDelete.get("give_back_reason", ""))),
                                     daemon=True).start()
        elif guildToDo == "role_edit":
            for rolesToEdit in list(guildData.get(guildToDo, [])):
                roles: List[discord.Role] = utils.getRoles(rolesToEdit, guild)
                edited: dict[discord.Role, dict] = dict()
                for role in roles:
                    prevStatus: dict = utils.getRoleData(role)
                    res: bool = await utils.editRole(rolesToEdit, role, guild)
                    if res:
                        edited[role] = prevStatus
                duration: int = int(rolesToEdit.get("duration", -1))
                if duration > 0:
                    async def wait(duration2: int, guildD: discord.Guild, editedRoles: dict[discord.Role, dict],
                                   editReason: str):
                        try:
                            await asyncio.sleep(duration2)
                            for editedRole, prevData in editedRoles.items():
                                prevData["reason"] = editReason
                                prevDataName = prevData["name"]
                                prevData.pop("name")
                                prevData["new_name"] = prevDataName
                                await utils.editRole(prevData, editedRole, guildD)
                        except Exception:
                            pass

                    threading.Thread(target=utils.separateThread, args=(loop, wait, duration, guild,
                                                                        edited, str(rolesToEdit.get("edit_reason", ""))),
                                     daemon=True).start()
        elif guildToDo == "overview":
            overviewData: dict = dict(guildData.get(guildToDo, {}))
            prevData: dict = utils.getGuildData(guild)
            res: bool = await utils.editGuild(overviewData, guild)
            if not res:
                continue
            duration: int = int(overviewData.get("duration", -1))
            if duration > 0:
                async def wait(duration2: int, guildD: discord.Guild, prevDataGuild: dict, reason: str):
                    try:
                        await asyncio.sleep(duration2)
                        # TODO Finish this
                        await utils.editGuild(prevDataGuild, guildD, reason=reason)
                    except Exception as e:
                        pass

                threading.Thread(target=utils.separateThread, args=(loop, wait, duration, guild, prevData,
                                                                    str(overviewData.get("reason", ""))),
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


