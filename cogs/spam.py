import discord
from discord.ext import commands, tasks
import json
import os
from datetime import datetime, timedelta, timezone

class Spam(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        base_path = os.path.dirname(os.path.abspath(__file__))
        self.ban_file = os.path.join(base_path, "..", "data/spam_ban.json")
        self.banned_users = {}
        self.load_bans()

        self.check_temp_bans.start()

    def cog_unload(self):
        self.check_temp_bans.cancel()

    def load_bans(self):
        """임시 밴 데이터를 파일에서 불러옵니다."""
        if os.path.exists(self.ban_file):
            try:
                with open(self.ban_file, 'r', encoding='utf-8') as f:
                    self.banned_users = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.banned_users = {}
        else:
            self.banned_users = {}

    def save_bans(self):
        """임시 밴 데이터를 파일에 저장합니다."""
        try:
            with open(self.ban_file, 'w', encoding='utf-8') as f:
                json.dump(self.banned_users, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[SpamFilter] 파일 저장 중 오류 발생: {e}")

    @tasks.loop(seconds=10.0)
    async def check_temp_bans(self):
        """주기적으로 임시 밴 해제 시간이 된 유저를 확인하고 차단을 해제합니다."""
        await self.bot.wait_until_ready()
        now = datetime.now(timezone.utc).timestamp()

        unbanned_entries = []

        for guild_id_str, users in list(self.banned_users.items()):
            guild = self.bot.get_guild(int(guild_id_str))
            if not guild:
                continue

            for user_id_str, unban_time in list(users.items()):
                if now >= unban_time:
                    user_id = int(user_id_str)
                    try:
                        await guild.unban(discord.Object(id=user_id), reason="스팸 필터 임시 밴 만료")
                        unbanned_entries.append((guild, user_id))
                    except discord.NotFound:
                        unbanned_entries.append((guild, user_id))
                    except discord.Forbidden:
                        print(f"[SpamFilter] 권한 부족으로 {user_id}의 밴을 해제하지 못했습니다.")
                    except Exception as e:
                        print(f"[SpamFilter] 밴 해제 중 오류 발생: {e}")

        if unbanned_entries:
            for guild, user_id in unbanned_entries:
                guild_id_str = str(guild.id)
                user_id_str = str(user_id)
                
                if guild_id_str in self.banned_users and user_id_str in self.banned_users[guild_id_str]:
                    del self.banned_users[guild_id_str][user_id_str]
                    if not self.banned_users[guild_id_str]:
                        del self.banned_users[guild_id_str]

            self.save_bans()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        settings = self.bot.get_cog('Settings')
        logger = self.bot.get_cog('Logger')
        
        if not settings:
            return

        server_data = settings.get_server_data(message.guild)
        spam_channel_id = server_data.get("spam_filter_channel_id")

        if message.author.guild_permissions.administrator:
            return

        if spam_channel_id and message.channel.id == spam_channel_id:
            guild = message.guild
            member = message.author
            
            try:
                await message.delete()
            except discord.HTTPException:
                pass

            unban_time = datetime.now(timezone.utc) + timedelta(days=1)
            unban_timestamp = unban_time.timestamp()

            guild_id_str = str(guild.id)
            user_id_str = str(member.id)

            if guild_id_str not in self.banned_users:
                self.banned_users[guild_id_str] = {}
            
            self.banned_users[guild_id_str][user_id_str] = unban_timestamp
            self.save_bans()

            try:
                await guild.ban(member, reason="스팸 메시지 작성 (1일 임시 밴)", delete_message_days=1)
                
                if logger:
                    embed = discord.Embed(
                        title="🔨 임시 밴 처벌",
                        description=(
                            f"**대상:** {member.mention} ({member})\n"
                            "**사유:** 스팸 메시지 작성\n"
                            f"**기간:** 1일 (24시간)"
                            ),
                        color=0x808080
                    )
                    embed.set_thumbnail(url=member.display_avatar.url)
                    embed.add_field(name="해제 예정 시간", value=f"<t:{int(unban_timestamp)}:F>", inline=False)
                    await logger.send_log(guild, embed, type="punish")
            except discord.Forbidden:
                print(f"[SpamFilter] 권한이 부족하여 밴을 수행할 수 없습니다: {member}")
            return

        if message.mention_everyone:
            guild = message.guild
            member = message.author

            try:
                await message.delete()
            except discord.HTTPException:
                pass

            duration = timedelta(hours=1)
            timeout_until = datetime.now(timezone.utc) + duration

            try:
                await member.timeout(duration, reason="전체 멘션 금지 위반")

                if logger:
                    embed = discord.Embed(
                        title="🔇 타임아웃 처벌",
                        description=(
                            f"**대상:** {member.mention} ({member})\n"
                            "**사유:** @everyone / @here 멘션\n"
                            "**기간:** 1시간"
                            ),
                        color=0x808080
                    )
                    embed.set_thumbnail(url=member.display_avatar.url)
                    embed.add_field(name="해제 예정 시간", value=f"<t:{int(timeout_until.timestamp())}:F>", inline=False)
                    await logger.send_log(guild, embed, type="punish")
            except discord.Forbidden:
                print(f"[SpamFilter] 권한이 부족하여 타임아웃을 수행할 수 없습니다: {member}")
            except Exception as e:
                print(f"[SpamFilter] 타임아웃 중 오류 발생: {e}")


async def setup(bot):
    await bot.add_cog(Spam(bot))