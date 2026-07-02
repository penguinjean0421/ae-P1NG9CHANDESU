import asyncio
import re
from datetime import timedelta

import discord
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

    async def cog_check(self, ctx):
        """명령어 실행 전 채널 및 권한을 확인합니다."""
        if not ctx.guild:
            return False

        settings = self.bot.get_cog('Settings')
        if settings:
            data = settings.get_server_data(ctx.guild)
            cmd_id = data.get("command_channel_id")
            if cmd_id and ctx.channel.id != cmd_id:
                return ctx.author.guild_permissions.administrator
        return True

    # --- 처벌(Sanction) 명령어 ---

    @commands.command(name="mute")
    @commands.has_permissions(administrator=True)
    async def server_mute(self, ctx, member: discord.Member = None, time: str = None):
        if not member or not member.voice:
            embed = discord.Embed(
                description="❌ 대상을 찾을 수 없거나 음성 채널에 없습니다.",
                color=0x808080
            )
            return await ctx.send(embed=embed)

        seconds = self.parse_time(time)
        reason_str = f"실행자: {ctx.author} ({time or '무기한'})"
        await member.edit(mute=True, reason=reason_str)

        embed = discord.Embed(
            description=f"🔇 {member.mention} 마이크 차단 ({time or '무기한'})",
            color=0x808080
        )
        await ctx.send(embed=embed)

        logger = self.bot.get_cog('Logger')
        if logger:
            await logger.send_log(ctx.guild, embed, type="punish")

        if seconds:
            await asyncio.sleep(seconds)
            if member.voice:
                await member.edit(mute=False)
                unmute_embed = discord.Embed(
                    description=f"🔊 {member.mention} 뮤트 해제 (시간 종료)",
                    color=0x808080
                )
                if logger:
                    await logger.send_log(ctx.guild, unmute_embed, type="punish")

    @commands.command(name="unmute")
    @commands.has_permissions(administrator=True)
    async def server_unmute(self, ctx, member: discord.Member = None):
        if not member or not member.voice:
            embed = discord.Embed(description="❌ 대상이 음성 채널에 없습니다.", color=0x808080)
            return await ctx.send(embed=embed)

        await member.edit(mute=False)
        embed = discord.Embed(description=f"🔊 {member.mention} 마이크 차단 해제", color=0x808080)
        await ctx.send(embed=embed)

        logger = self.bot.get_cog('Logger')
        if logger:
            await logger.send_log(ctx.guild, embed, type="punish")

    @commands.command(name="deafen")
    @commands.has_permissions(administrator=True)
    async def server_deafen(self, ctx, member: discord.Member = None, time: str = None):
        if not member or not member.voice:
            embed = discord.Embed(
                description="❌ 대상을 찾을 수 없거나 음성 채널에 없습니다.",
                color=0x808080
            )
            return await ctx.send(embed=embed)

        seconds = self.parse_time(time)
        reason_str = f"실행자: {ctx.author} ({time or '무기한'})"
        await member.edit(deafen=True, reason=reason_str)

        embed = discord.Embed(
            description=f"🔇 {member.mention} 헤드셋 차단 ({time or '무기한'})",
            color=0x808080
        )
        await ctx.send(embed=embed)

        logger = self.bot.get_cog('Logger')
        if logger:
            await logger.send_log(ctx.guild, embed, type="punish")

        if seconds:
            await asyncio.sleep(seconds)
            if member.voice:
                await member.edit(deafen=False)
                log_embed = discord.Embed(
                    description=f"🔊 {member.mention} 헤드셋 차단 해제 (시간 종료)",
                    color=0x808080
                )
                if logger:
                    await logger.send_log(ctx.guild, log_embed, type="punish")

    @commands.command(name="undeafen")
    @commands.has_permissions(administrator=True)
    async def server_undeafen(self, ctx, member: discord.Member = None):
        if not member or not member.voice:
            embed = discord.Embed(description="❌ 대상이 음성 채널에 없습니다.", color=0x808080)
            return await ctx.send(embed=embed)

        await member.edit(deafen=False)
        embed = discord.Embed(description=f"🔊 {member.mention} 헤드셋 차단 해제", color=0x808080)
        await ctx.send(embed=embed)

        logger = self.bot.get_cog('Logger')
        if logger:
            await logger.send_log(ctx.guild, embed, type="punish")

    @commands.command(name="vckick")
    @commands.has_permissions(administrator=True)
    async def server_vckick(self, ctx, member: discord.Member = None, *, reason="사유 없음"):
        if not member or not member.voice:
            embed = discord.Embed(description="❌ 대상이 음성 채널에 없습니다.", color=0x808080)
            return await ctx.send(embed=embed)

        await member.move_to(None, reason=f"실행자: {ctx.author}")
        embed = discord.Embed(
            title="👟 음성 강제 퇴장",
            description=f"{member.mention} 퇴장됨\n사유: {reason}",
            color=0x808080
        )
        await ctx.send(embed=embed)

        logger = self.bot.get_cog('Logger')
        if logger:
            await logger.send_log(ctx.guild, embed, type="punish")

    @commands.command(name="timeout")
    @commands.has_permissions(administrator=True)
    async def server_timeout(self, ctx, member: discord.Member = None,
                             time: str = None, *, reason="사유 없음"):
        seconds = self.parse_time(time)
        if not member or not seconds:
            embed = discord.Embed(
                description=(
                    f"❓ 사용법: `{ctx.prefix}timeout @유저 [시간] [사유]`\n"
                    f"예: `{ctx.prefix}timeout @유저 10m 도배`"
                ),
                color=0x808080
            )
            return await ctx.send(embed=embed)

        try:
            duration = timedelta(seconds=seconds)
            await member.timeout(duration, reason=f"실행자: {ctx.author} | {reason}")

            embed = discord.Embed(
                title="⏳ 타임아웃",
                description=f"{member.mention} ({time})\n사유: {reason}",
                color=0x808080
            )
            await ctx.send(embed=embed)

            logger = self.bot.get_cog('Logger')
            if logger:
                await logger.send_log(ctx.guild, embed, type="punish")
        except Exception as e:
            err_embed = discord.Embed(description=f"❌ 오류: {e}", color=0x808080)
            await ctx.send(embed=err_embed)

    @commands.command(name="untimeout")
    @commands.has_permissions(administrator=True)
    async def server_untimeout(self, ctx, member: discord.Member = None, *, reason="관리자에 의한 해제"):
        if not member:
            embed=discord.Embed(description=f"❓ 사용법: `{ctx.prefix}untimeout @유저`", color=0x808080)
            return await ctx.send(embed=embed)

        if not member.timed_out_until:
            embed = discord.Embed(
                description=f"❌ {member.mention} 님은 현재 타임아웃 상태가 아닙니다.",
                color=0x808080
            )
            return await ctx.send(embed=embed)

        try:
            await member.timeout(None, reason=f"실행자: {ctx.author} | {reason}")
            embed = discord.Embed(
                title="✅ 타임아웃 해제",
                description=f"{member.mention} 님의 타임아웃이 해제되었습니다.",
                color=0x808080
            )
            await ctx.send(embed=embed)

            logger = self.bot.get_cog('Logger')
            if logger:
                await logger.send_log(ctx.guild, embed, type="punish")
        except Exception as e:
            err_embed = discord.Embed(description=f"❌ 오류 발생: {e}", color=0x808080)
            await ctx.send(embed=err_embed)

    @commands.command(name="kick")
    @commands.has_permissions(kick_members=True)
    async def server_kick(self, ctx, member: discord.Member = None, *, reason="사유 없음"):
        if not member:
            usage = f"❓ 사용법: `{ctx.prefix}kick @유저 [사유]`"
            return await ctx.send(embed=discord.Embed(description=usage, color=0x808080))

        await member.kick(reason=f"실행자: {ctx.author} | {reason}")
        embed = discord.Embed(
            title="👞 추방 완료",
            description=f"{member.mention} 추방됨\n사유: {reason}",
            color=0x808080
        )
        await ctx.send(embed=embed)

        logger = self.bot.get_cog('Logger')
        if logger:
            await logger.send_log(ctx.guild, embed, type="punish")

    @commands.command(name="ban")
    @commands.has_permissions(ban_members=True)
    async def server_ban(self, ctx, member: discord.Member = None, *, reason="사유 없음"):
        if not member:
            usage = f"❓ 사용법: `{ctx.prefix}ban [유저멘션/ID] [사유]`"
            return await ctx.send(embed=discord.Embed(description=usage, color=0x808080))

        await member.ban(
            reason=f"실행자: {ctx.author} | {reason}",
            delete_message_seconds=86400
        )
        embed = discord.Embed(
            title="🚫 차단 완료",
            description=f"{member.mention} 차단됨\n사유: {reason}",
            color=0x808080
        )
        await ctx.send(embed=embed)

        logger = self.bot.get_cog('Logger')
        if logger:
            await logger.send_log(ctx.guild, embed, type="punish")

    @commands.command(name="unban")
    @commands.has_permissions(ban_members=True)
    async def server_unban(self, ctx, *, user_spec: str = None):
        if not user_spec:
            embed=discord.Embed(description=f"❓ 사용법: `{ctx.prefix}unban [이름#태그] 또는 [ID]`", color=0x808080)
            return await ctx.send(embed=embed)

        async for entry in ctx.guild.bans():
            if user_spec in [str(entry.user.id), str(entry.user)]:
                await ctx.guild.unban(entry.user)
                embed = discord.Embed(
                    title="✅ 차단 해제",
                    description=f"{entry.user} 해제됨",
                    color=0x808080
                )
                await ctx.send(embed=embed)

                logger = self.bot.get_cog('Logger')
                if logger:
                    await logger.send_log(ctx.guild, embed, type="punish")
                return

        error_embed = discord.Embed(description="❌ 차단 목록에서 찾을 수 없습니다.", color=0x808080)
        await ctx.send(embed=error_embed)


async def setup(bot):
    await bot.add_cog(Moderation(bot))