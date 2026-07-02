import discord
from discord.ext import commands
import json
import os

class Voice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        base_path = os.path.dirname(os.path.abspath(__file__))
        self.temp_file = os.path.join(base_path, "..", "data/temp_channels.json")
        self.temp_channels = {}
        self.load_temp_channels()

    def load_temp_channels(self):
        """임시 채널 데이터를 파일에서 불러옵니다."""
        if os.path.exists(self.temp_file):
            try:
                with open(self.temp_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.temp_channels = {}
                    for g_id, channels in data.items():
                        self.temp_channels[g_id] = {int(ch_id): u_id for ch_id, u_id in channels.items()}
            except (json.JSONDecodeError, IOError):
                self.temp_channels = {}
        else:
            self.temp_channels = {}

    def save_temp_channels(self):
        """임시 채널 데이터를 파일에 저장합니다."""
        try:
            with open(self.temp_file, 'w', encoding='utf-8') as f:
                json.dump(self.temp_channels, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[Voice] 파일 저장 중 오류 발생: {e}")

    async def log_event(self, guild, embed):
        logger = self.bot.get_cog('Logger')
        if logger:
            await logger.send_log(guild, embed)

    def _get_creator_id(self, guild_id: int, channel_id: int):
        """특정 서버의 특정 채널에 지정된 방장 ID를 가져옵니다. 없으면 None 반환"""
        return self.temp_channels.get(str(guild_id), {}).get(channel_id)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot:
            return

        settings = self.bot.get_cog('Settings')
        if not settings:
            return

        guild = member.guild
        gid_str = str(guild.id)
        server_data = settings.get_server_data(guild)
        create_channel_id = server_data.get("create_voice_channel_id")

        if after.channel and after.channel.id == create_channel_id:
            category = after.channel.category

            overwrites = {
                guild.default_role: discord.PermissionOverwrite(connect=True),
                member: discord.PermissionOverwrite(
                    manage_channels=True,
                    move_members=True,
                    mute_members=True
                )
            }

            new_channel = await guild.create_voice_channel(
                name=f"🎙️ {member.display_name}의 방",
                category=category,
                overwrites=overwrites
            )

            if gid_str not in self.temp_channels:
                self.temp_channels[gid_str] = {}
            
            self.temp_channels[gid_str][new_channel.id] = member.id
            self.save_temp_channels()

            await member.move_to(new_channel)
            
            embed = discord.Embed(
                title="🔨 음성 채널 생성",
                description=f"**방장:** {member.mention} ({member})\n**채널:** {new_channel.mention}",
                color=0x808080
            )
            await self.log_event(guild, embed)

        if before.channel:
            creator_id = self._get_creator_id(guild.id, before.channel.id)
            
            if creator_id and len(before.channel.members) == 0:
                chn_name = before.channel.name
                creator = guild.get_member(creator_id)
                creator_text = f"<@{creator_id}>" if not creator else f"{creator.mention} ({creator})"

                try:
                    await before.channel.delete()

                    if gid_str in self.temp_channels and before.channel.id in self.temp_channels[gid_str]:
                        del self.temp_channels[gid_str][before.channel.id]
                        if not self.temp_channels[gid_str]:
                            del self.temp_channels[gid_str]
                    
                    self.save_temp_channels()

                    embed = discord.Embed(
                        title="🧹 빈 채널이 되어 자동으로 삭제되었습니다.",
                        description=f"**방장:** {creator_text}\n**채널명:** `{chn_name}`",
                        color=0x808080
                    )
                    await self.log_event(guild, embed)

                except discord.NotFound:
                    if gid_str in self.temp_channels and before.channel.id in self.temp_channels[gid_str]:
                        del self.temp_channels[gid_str][before.channel.id]
                        if not self.temp_channels[gid_str]:
                            del self.temp_channels[gid_str]
                        self.save_temp_channels()

    @commands.command(name="named", aliases=["이름"])
    async def change_name(self, ctx, *, new_name: str):
        """방장이 자신이 속한 음성 채널의 이름을 변경합니다."""
        if not ctx.author.voice or not ctx.author.voice.channel:
            return await ctx.send("❌ 먼저 변경할 음성 채널에 입장해 주세요.", delete_after=3)

        voice_channel = ctx.author.voice.channel
        creator_id = self._get_creator_id(ctx.guild.id, voice_channel.id)

        if not creator_id:
            return await ctx.send("❌ 이 채널은 이름을 변경할 수 있는 채널이 아닙니다.", delete_after=3)

        if creator_id != ctx.author.id:
            return await ctx.send("❌ 방장만 채널 이름을 변경할 수 있습니다.", delete_after=3)

        old_name = voice_channel.name

        await voice_channel.edit(name=new_name)
        await ctx.send(f"✅ 음성 채널 이름이 `{new_name}`(으)로 변경되었습니다.", delete_after=3)

        embed = discord.Embed(
            title="✏️ 채널 이름 변경",
            description=f"**변경자:** {ctx.author.mention}\n**채널:** {voice_channel.mention}",
            color=0x808080
        )
        embed.add_field(name="변경 전", value=f"`{old_name}`", inline=True)
        embed.add_field(name="변경 후", value=f"`{new_name}`", inline=True)
        await self.log_event(ctx.guild, embed)

    @commands.command(name="limit", aliases=["인원"])
    async def change_limit(self, ctx, limit: int):
        """방장이 자신이 속한 음성 채널의 인원 제한을 변경합니다. (0은 무제한)"""
        if not ctx.author.voice or not ctx.author.voice.channel:
            return await ctx.send("❌ 먼저 변경할 음성 채널에 입장해 주세요.", delete_after=3)

        voice_channel = ctx.author.voice.channel
        creator_id = self._get_creator_id(ctx.guild.id, voice_channel.id)

        if not creator_id:
            return await ctx.send("❌ 이 채널은 인원을 변경할 수 있는 임시 채널이 아닙니다.", delete_after=3)
        
        if creator_id != ctx.author.id:
            return await ctx.send("❌ 방장만 인원 제한을 변경할 수 있습니다.", delete_after=3)

        if limit < 0 or limit > 99:
            return await ctx.send("❌ 인원 제한은 0(무제한)에서 99명 사이로 설정해 주세요.", delete_after=3)

        old_limit = voice_channel.user_limit
        old_limit_text = "무제한" if old_limit == 0 else f"{old_limit}명"

        await voice_channel.edit(user_limit=limit)
        limit_text = "무제한" if limit == 0 else f"{limit}명"
        await ctx.send(f"✅ 음성 채널 인원 제한이 `{limit_text}`(으)로 변경되었습니다.", delete_after=3)

        embed = discord.Embed(
            title="👥 임시 채널 인원 설정 변경",
            description=f"**변경자:** {ctx.author.mention}\n**채널:** {voice_channel.mention}",
            color=0x3498DB
        )
        embed.add_field(name="변경 전", value=f"`{old_limit_text}`", inline=True)
        embed.add_field(name="변경 후", value=f"`{limit_text}`", inline=True)
        await self.log_event(ctx.guild, embed)


async def setup(bot):
    await bot.add_cog(Voice(bot))