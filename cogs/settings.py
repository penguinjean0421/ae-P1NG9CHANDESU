import json
import os
import re

import discord
from discord import app_commands
from discord.ext import commands


class Settings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        base_path = os.path.dirname(os.path.abspath(__file__))
        self.config_file = os.path.join(base_path, "..", "data/config.json")
        self.server_configs = {}
        self.load_config()

    def load_config(self):
        """설정 파일(JSON)을 로드합니다."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.server_configs = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.server_configs = {}
        else:
            self.server_configs = {}

    def save_config(self):
        """현재 설정을 파일에 저장합니다."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.server_configs, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"파일 저장 중 오류 발생: {e}")

    def get_server_data(self, guild):
        """서버별 데이터 구조를 반환하며, 없을 경우 초기화합니다."""
        gid = str(guild.id)

        if gid not in self.server_configs:
            self.server_configs[gid] = {
                "server_name": guild.name,
                "owner_id": guild.owner_id,
                "owner_name": str(guild.owner),
                "spam_filter_channel_id": None,
                "create_voice_channel_id": None,
                "server_log_channel_id": None,
                "punish_log_channel_id": None,
                "ticket_log_channel_id": None,
                "command_channel_id": None,
                "emoji_command_channel_id": None,
                "ticket_panel_channel_id": None,
                "ticket_panel_msg_id": None,
                "ticket_count": 0
                }
        else:
            keys = ["ticket_panel_channel_id", "ticket_panel_msg_id", "ticket_count", "create_voice_channel_id"]
            for key in keys:
                if key not in self.server_configs[gid]:
                    self.server_configs[gid][key] = 0 if "count" in key else None
            self.server_configs[gid]["server_name"] = guild.name

        self.save_config()
        return self.server_configs[gid]

    async def delete_ticket_panel(self, guild):
        """저장된 티켓 패널 메시지를 물리적으로 삭제합니다."""
        gid = str(guild.id)
        config = self.server_configs.get(gid)
        if not config:
            return

        msg_id = config.get("ticket_panel_msg_id")
        chn_id = config.get("ticket_panel_channel_id")

        if msg_id and chn_id:
            channel = self.bot.get_channel(chn_id)
            if not channel:
                try:
                    channel = await self.bot.fetch_channel(chn_id)
                except Exception:
                    return

            try:
                msg = await channel.fetch_message(msg_id)
                await msg.delete()
            except discord.NotFound:
                pass
            except Exception as e:
                print(f"패널 삭제 오류: {e}")

    # --- /set 명령어 그룹 ---
    set_group = app_commands.Group(name="set", description="서버 설정을 구성합니다.")

    @set_group.command(name="log", description="로그 채널을 설정합니다.")
    @app_commands.choices(target=[
        app_commands.Choice(name="server (서버 로그)", value="server"),
        app_commands.Choice(name="punish (처벌 로그)", value="punish"),
        app_commands.Choice(name="ticket (티켓 로그)", value="ticket")
    ])
    @app_commands.describe(target="설정할 로그 종류", channel="기록할 텍스트 채널 (생략 시 현재 채널)")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_log(self, interaction: discord.Interaction, target: str, channel: discord.TextChannel = None):
        log_map = {
            "server": "server_log_channel_id",
            "punish": "punish_log_channel_id",
            "ticket": "ticket_log_channel_id"
            }
        gid = str(interaction.guild.id)
        self.get_server_data(interaction.guild)

        target_channel = channel or interaction.channel
        self.server_configs[gid][log_map[target]] = target_channel.id
        self.save_config()

        embed = discord.Embed(
            title=f"✅ Log - {target.upper()} 채널 설정",
            description=f"{target.upper()} 채널이 {target_channel.mention}로 설정되었습니다.",
            color=0x808080
            )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @set_group.command(name="command", description="봇 명령어 전용 채널을 설정합니다.")
    @app_commands.choices(target=[
        app_commands.Choice(name="bot (일반 봇 명령어)", value="bot"),
        app_commands.Choice(name="emoji (이모지 명령어)", value="emoji"),
        app_commands.Choice(name="ticket (티켓 패널 생성)", value="ticket")
    ])
    @app_commands.describe(target="설정할 명령어 카테고리", channel="사용할 텍스트 채널 (생략 시 현재 채널)")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_command(self, interaction: discord.Interaction, target: str, channel: discord.TextChannel = None):
        gid = str(interaction.guild.id)
        self.get_server_data(interaction.guild)
        target_channel = channel or interaction.channel

        if target == "ticket":
            ticket_cog = self.bot.get_cog('Ticket')
            if ticket_cog:
                await interaction.response.defer(ephemeral=True)
                await self.delete_ticket_panel(interaction.guild)
                panel_msg = await ticket_cog.send_ticket_panel(target_channel)
                if panel_msg:
                    self.server_configs[gid]["ticket_panel_channel_id"] = target_channel.id
                    self.server_configs[gid]["ticket_panel_msg_id"] = panel_msg.id
                    self.save_config()
                    embed = discord.Embed(
                        title="✅ TICKET 채널 생성",
                        description=f"**TICKET** 채널이 {target_channel.mention}로 설정되었으며, 티켓 패널이 생성되었습니다.",
                        color=0x808080
                        )

                    return await interaction.followup.send(embed=embed)
                else:
                    embed=discord.Embed(description="❌ 티켓 패널 메시지 생성에 실패했습니다.", color=0x808080)
                    return await interaction.followup.send(embed=embed)
            else:
                embed=discord.Embed(description="❌ Ticket Cog가 로드되지 않아 패널을 생성할 수 없습니다.", color=0x808080)
                return await interaction.response.send_message(embed=embed, ephemeral=True)
        cmd_map = {
            "bot": "command_channel_id",
            "emoji": "emoji_command_channel_id"
            }
        if target in cmd_map:
            self.server_configs[gid][cmd_map[target]] = target_channel.id
            self.save_config()
            embed = discord.Embed(
                title=f"✅ COMMAND - {target.upper()} 채널 설정",
                description=f"{target.upper()} 채널이 {target_channel.mention}로 설정되었습니다.",
                color=0x808080
                )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @set_group.command(name="spam", description="스팸 필터 채널을 설정합니다.")
    @app_commands.describe(channel="스팸을 감지할 텍스트 채널 (생략 시 현재 채널)")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_spam(self, interaction: discord.Interaction, channel: discord.TextChannel = None):
        gid = str(interaction.guild.id)
        self.get_server_data(interaction.guild)
        target_channel = channel or interaction.channel

        self.server_configs[gid]["spam_filter_channel_id"] = target_channel.id
        self.save_config()

        embed = discord.Embed(
            title="✅ **SPAM FILTER** 채널 설정",
            description=f"SPAM FILTER 채널이 {target_channel.mention}로 설정되었습니다.",
            color=0x808080
            )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @set_group.command(name="voice", description="음성 채널 생성(방 만들기)용 음성 채널을 설정합니다.")
    @app_commands.describe(voice_channel="유저가 들어가면 방이 생성되는 대상 음성 채널")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_voice(self, interaction: discord.Interaction, voice_channel: discord.VoiceChannel):
        gid = str(interaction.guild.id)
        self.get_server_data(interaction.guild)

        self.server_configs[gid]["create_voice_channel_id"] = voice_channel.id
        self.save_config()

        embed = discord.Embed(
            title="✅ **VOICE CREATOR** 채널 설정",
            description=f"방 만들기 전용 음성 채널이 {voice_channel.mention} (ID: `{voice_channel.id}`)로 지정되었습니다.",
            color=0x808080
            )
        await interaction.response.send_message(embed=embed, ephemeral=True)


    # --- /reset 명령어 그룹 ---
    reset_group = app_commands.Group(name="reset", description="서버 설정을 초기화합니다.")

    @reset_group.command(name="all", description="서버의 모든 설정을 초기화합니다.")
    @app_commands.checks.has_permissions(administrator=True)
    async def reset_all(self, interaction: discord.Interaction):
        gid = str(interaction.guild.id)
        await interaction.response.defer(ephemeral=True)
        await self.delete_ticket_panel(interaction.guild)
        self.server_configs.pop(gid, None)
        self.save_config()

        embed = discord.Embed(description="✅ 모든 설정이 초기화되었습니다.", color=0x808080)
        await interaction.followup.send(embed=embed)

    @reset_group.command(name="log", description="특정 로그 설정을 제거합니다.")
    @app_commands.choices(target=[
        app_commands.Choice(name="server", value="server"),
        app_commands.Choice(name="punish", value="punish"),
        app_commands.Choice(name="ticket", value="ticket")
    ])
    @app_commands.checks.has_permissions(administrator=True)
    async def reset_log(self, interaction: discord.Interaction, target: str):
        log_map = {
            "server": "server_log_channel_id",
            "punish": "punish_log_channel_id",
            "ticket": "ticket_log_channel_id"
            }
        gid = str(interaction.guild.id)
        if gid in self.server_configs and target in log_map:
            self.server_configs[gid][log_map[target]] = None
            self.save_config()
            embed = discord.Embed(description=f"✅ **LOG -> {target.upper()}** 설정이 제거되었습니다.", color=0x808080)
        else:
            embed = discord.Embed(description="❌ 설정된 데이터가 없거나 올바르지 않습니다.", color=0x808080)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @reset_group.command(name="command", description="특정 명령어 채널 설정을 제거합니다.")
    @app_commands.choices(target=[
        app_commands.Choice(name="bot", value="bot"),
        app_commands.Choice(name="emoji", value="emoji"),
        app_commands.Choice(name="ticket", value="ticket")
    ])
    @app_commands.checks.has_permissions(administrator=True)
    async def reset_command(self, interaction: discord.Interaction, target: str):
        gid = str(interaction.guild.id)
        cmd_map = {
            "bot": "command_channel_id",
            "emoji": "emoji_command_channel_id"
            }
        if gid in self.server_configs:
            if target == "ticket":
                await interaction.response.defer(ephemeral=True)
                await self.delete_ticket_panel(interaction.guild)
                self.server_configs[gid]["ticket_panel_channel_id"] = None
                self.server_configs[gid]["ticket_panel_msg_id"] = None
                self.save_config()
                embed = discord.Embed(description="✅ **COMMAND - TICKET** 설정 및 티켓 패널이 제거되었습니다.", color=0x808080)
                return await interaction.followup.send(embed=embed)
            elif target in cmd_map:
                self.server_configs[gid][cmd_map[target]] = None
                self.save_config()
                embed = discord.Embed(description=f"✅ **COMMAND - {target.upper()}** 설정이 제거되었습니다.", color=0x808080)
            else:
                embed = discord.Embed(description="❌ 올바르지 않은 대상입니다.", color=0x808080)
        else:
            embed = discord.Embed(description="❌ 설정된 데이터가 없습니다.", color=0x808080)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @reset_group.command(name="voice", description="음성 채널 생성 설정을 제거합니다.")
    @app_commands.checks.has_permissions(administrator=True)
    async def reset_voice(self, interaction: discord.Interaction):
        gid = str(interaction.guild.id)
        if gid in self.server_configs:
            self.server_configs[gid]["create_voice_channel_id"] = None
            self.save_config()
            embed = discord.Embed(description="✅ **VOICE CREATOR** 설정이 제거되었습니다.", color=0x808080)
        else:
            embed = discord.Embed(description="❌ 설정된 데이터가 없습니다.", color=0x808080)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @reset_group.command(name="spam", description="스팸 필터 채널 설정을 제거합니다.")
    @app_commands.checks.has_permissions(administrator=True)
    async def reset_spam(self, interaction: discord.Interaction):
        gid = str(interaction.guild.id)
        if gid in self.server_configs:
            self.server_configs[gid]["spam_filter_channel_id"] = None
            self.save_config()
            embed = discord.Embed(description="✅ **SPAM FILTER** 설정이 제거되었습니다.", color=0x808080)
        else:
            embed = discord.Embed(description="❌ 설정된 데이터가 없습니다.", color=0x808080)
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Settings(bot))