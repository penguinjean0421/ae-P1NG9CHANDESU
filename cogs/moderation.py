import asyncio
import re
from datetime import timedelta

import discord
from discord import app_commands
from discord.ext import commands


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def parse_time(self, time_str: str):
        """시간 문자열(s, m, h, d)을 초 단위 정수로 변환합니다."""
        if not time_str:
            return None
        if time_str.isdigit():
            return int(time_str)

        match = re.match(r"(\d+)([smhd])", time_str.lower())
        if not match:
            return None

        amount, unit = int(match.group(1)), match.group(2)
        unit_map = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
        return amount * unit_map[unit]

    async def check_channel(self, interaction: discord.Interaction) -> bool:
        """설정된 명령어 채널인지 확인합니다. (관리자는 예외)"""
        if interaction.user.guild_permissions.administrator:
            return True

        settings = self.bot.get_cog('Settings')
        if settings:
            data = settings.get_server_data(interaction.guild)
            cmd_id = data.get("command_channel_id")
            if cmd_id and interaction.channel.id != cmd_id:
                await interaction.response.send_message(f"❌ 이 명령어는 지정된 명령어 채널(<#{cmd_id}>)에서만 사용할 수 있습니다.", ephemeral=True)
                return False
        return True

    # --- 처벌(Sanction) 명령어 ---

    @app_commands.command(name="mute", description="유저의 음성 마이크를 차단합니다.")
    @app_commands.describe(member="대상 유저", time="지속 시간 (예: 10s, 5m, 1h, 1d)")
    @app_commands.checks.has_permissions(administrator=True)
    async def server_mute(self, interaction: discord.Interaction, member: discord.Member, time: str = None):
        if not await self.check_channel(interaction):
            return

        if not member.voice:
            embed = discord.Embed(description="❌ 대상이 음성 채널에 없습니다.", color=0x808080)
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        seconds = self.parse_time(time) if time else None
        await member.edit(mute=True, reason=f"실행자: {interaction.user} ({time or '무기한'})")

        embed = discord.Embed(
            description=f"🔇 {member.mention} 마이크 차단 ({time or '무기한'})",
            color=0x808080
            )
        await interaction.response.send_message(embed=embed)

        logger = self.bot.get_cog('Logger')
        if logger:
            await logger.send_log(interaction.guild, embed, type="punish")

        if seconds:
            await asyncio.sleep(seconds)
            if member.voice:
                await member.edit(mute=False)
                embed = discord.Embed(
                    description=f"🔊 {member.mention} 뮤트 해제 (시간 종료)",
                    color=0x808080
                )
                if logger:
                    await logger.send_log(interaction.guild, embed, type="punish")

    @app_commands.command(name="unmute", description="유저의 음성 마이크 차단을 해제합니다.")
    @app_commands.describe(member="대상 유저")
    @app_commands.checks.has_permissions(administrator=True)
    async def server_unmute(self, interaction: discord.Interaction, member: discord.Member):
        if not await self.check_channel(interaction):
            return

        if not member.voice:
            embed = discord.Embed(description="❌ 대상이 음성 채널에 없습니다.", color=0x808080)
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        await member.edit(mute=False)
        embed = discord.Embed(
            description=f"🔊 {member.mention} 마이크 차단 해제", 
            color=0x808080
            )
        await interaction.response.send_message(embed=embed)

        logger = self.bot.get_cog('Logger')
        if logger:
            await logger.send_log(interaction.guild, embed, type="punish")

    @app_commands.command(name="deafen", description="유저의 헤드셋을 차단합니다.")
    @app_commands.describe(member="대상 유저", time="지속 시간 (예: 10s, 5m, 1h, 1d)")
    @app_commands.checks.has_permissions(administrator=True)
    async def server_deafen(self, interaction: discord.Interaction, member: discord.Member, time: str = None):
        if not await self.check_channel(interaction):
            return

        if not member.voice:
            embed = discord.Embed(description="❌ 대상이 음성 채널에 없습니다.", color=0x808080)
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        seconds = self.parse_time(time) if time else None
        await member.edit(deafen=True, reason=f"실행자: {interaction.user} ({time or '무기한'})")

        embed = discord.Embed(
            description=f"🔇 {member.mention} 헤드셋 차단 ({time or '무기한'})",
            color=0x808080
            )
        await interaction.response.send_message(embed=embed)

        logger = self.bot.get_cog('Logger')
        if logger:
            await logger.send_log(interaction.guild, embed, type="punish")

        if seconds:
            await asyncio.sleep(seconds)
            if member.voice:
                await member.edit(deafen=False)
                log_embed = discord.Embed(
                    description=f"🔊 {member.mention} 헤드셋 차단 해제 (시간 종료)",
                    color=0x808080
                    )
                if logger:
                    await logger.send_log(interaction.guild, log_embed, type="punish")

    @app_commands.command(name="undeafen", description="유저의 헤드셋 차단을 해제합니다.")
    @app_commands.describe(member="대상 유저")
    @app_commands.checks.has_permissions(administrator=True)
    async def server_undeafen(self, interaction: discord.Interaction, member: discord.Member):
        if not await self.check_channel(interaction):
            return

        if not member.voice:
            embed = discord.Embed(description="❌ 대상이 음성 채널에 없습니다.", color=0x808080)
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        await member.edit(deafen=False)
        embed = discord.Embed(description=f"🔊 {member.mention} 헤드셋 차단 해제", color=0x808080)
        await interaction.response.send_message(embed=embed)

        logger = self.bot.get_cog('Logger')
        if logger:
            await logger.send_log(interaction.guild, embed, type="punish")

    @app_commands.command(name="vckick", description="유저를 음성 채널에서 강제로 내보냅니다.")
    @app_commands.describe(member="대상 유저", reason="퇴장 사유")
    @app_commands.checks.has_permissions(administrator=True)
    async def server_vckick(self, interaction: discord.Interaction, member: discord.Member, reason: str = "사유 없음"):
        if not await self.check_channel(interaction):
            return

        if not member.voice:
            embed = discord.Embed(description="❌ 대상이 음성 채널에 없습니다.", color=0x808080)
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        await member.move_to(None, reason=f"실행자: {interaction.user}")
        embed = discord.Embed(
            title="👟 음성 강제 퇴장",
            description=f"{member.mention} 퇴장됨\n사유: {reason}",
            color=0x808080
            )
        await interaction.response.send_message(embed=embed)

        logger = self.bot.get_cog('Logger')
        if logger:
            await logger.send_log(interaction.guild, embed, type="punish")

    @app_commands.command(name="timeout", description="유저에게 타임아웃을 적용합니다.")
    @app_commands.describe(member="대상 유저", time="타임아웃 시간 (예: 10m, 1h)", reason="사유")
    @app_commands.checks.has_permissions(administrator=True)
    async def server_timeout(self, interaction: discord.Interaction, member: discord.Member, time: str, reason: str = "사유 없음"):
        if not await self.check_channel(interaction):
            return

        seconds = self.parse_time(time)
        if not seconds:
            embed = discord.Embed(
                description="❌ 올바른 시간 형식을 입력해주세요. (예: `10m`, `1h`, `1d`)",
                color=0x808080
                )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        try:
            duration = timedelta(seconds=seconds)
            await member.timeout(duration, reason=f"실행자: {interaction.user} | {reason}")

            embed = discord.Embed(
                title="⏳ 타임아웃",
                description=f"{member.mention} ({time})\n사유: {reason}",
                color=0x808080
            )
            await interaction.response.send_message(embed=embed)

            logger = self.bot.get_cog('Logger')
            if logger:
                await logger.send_log(interaction.guild, embed, type="punish")
        except Exception as e:
            embed = discord.Embed(description=f"❌ 오류: {e}", color=0x808080)
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="untimeout", description="유저의 타임아웃을 해제합니다.")
    @app_commands.describe(member="대상 유저", reason="해제 사유")
    @app_commands.checks.has_permissions(administrator=True)
    async def server_untimeout(self, interaction: discord.Interaction, member: discord.Member, reason: str = "관리자에 의한 해제"):
        if not await self.check_channel(interaction):
            return

        if not member.timed_out_until:
            embed = discord.Embed(
                description=f"❌ {member.mention} 님은 현재 타임아웃 상태가 아닙니다.",
                color=0x808080
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        try:
            await member.timeout(None, reason=f"실행자: {interaction.user} | {reason}")
            embed = discord.Embed(
                title="✅ 타임아웃 해제",
                description=f"{member.mention} 님의 타임아웃이 해제되었습니다.",
                color=0x808080
            )
            await interaction.response.send_message(embed=embed)

            logger = self.bot.get_cog('Logger')
            if logger:
                await logger.send_log(interaction.guild, embed, type="punish")
        except Exception as e:
            embed = discord.Embed(description=f"❌ 오류 발생: {e}", color=0x808080)
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="kick", description="서버에서 유저를 추방합니다.")
    @app_commands.describe(member="대상 유저", reason="추방 사유")
    @app_commands.checks.has_permissions(kick_members=True)
    async def server_kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = "사유 없음"):
        if not await self.check_channel(interaction):
            return

        await member.kick(reason=f"실행자: {interaction.user} | {reason}")
        embed = discord.Embed(
            title="👞 추방 완료",
            description=f"{member.mention} 추방됨\n사유: {reason}",
            color=0x808080
        )
        await interaction.response.send_message(embed=embed)

        logger = self.bot.get_cog('Logger')
        if logger:
            await logger.send_log(interaction.guild, embed, type="punish")

    @app_commands.command(name="ban", description="서버에서 유저를 차단합니다.")
    @app_commands.describe(member="대상 유저", reason="차단 사유")
    @app_commands.checks.has_permissions(ban_members=True)
    async def server_ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = "사유 없음"):
        if not await self.check_channel(interaction):
            return

        await member.ban(
            reason=f"실행자: {interaction.user} | {reason}",
            delete_message_seconds=86400
        )
        embed = discord.Embed(
            title="🚫 차단 완료",
            description=f"{member.mention} 차단됨\n사유: {reason}",
            color=0x808080
        )
        await interaction.response.send_message(embed=embed)

        logger = self.bot.get_cog('Logger')
        if logger:
            await logger.send_log(interaction.guild, embed, type="punish")

    @app_commands.command(name="unban", description="차단된 유저의 차단을 해제합니다.")
    @app_commands.describe(user_spec="유저 ID 또는 이름#태그")
    @app_commands.checks.has_permissions(ban_members=True)
    async def server_unban(self, interaction: discord.Interaction, user_spec: str):
        if not await self.check_channel(interaction):
            return

        async for entry in interaction.guild.bans():
            if user_spec in [str(entry.user.id), str(entry.user)]:
                await interaction.guild.unban(entry.user)
                embed = discord.Embed(
                    title="✅ 차단 해제",
                    description=f"{entry.user} 차단이 해제되었습니다.",
                    color=0x808080
                )
                await interaction.response.send_message(embed=embed)

                logger = self.bot.get_cog('Logger')
                if logger:
                    await logger.send_log(interaction.guild, embed, type="punish")
                return

        embed = discord.Embed(description="❌ 차단 목록에서 찾을 수 없습니다.", color=0x808080)
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Moderation(bot))