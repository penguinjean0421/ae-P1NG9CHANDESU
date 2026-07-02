import io
import re

import aiohttp
import discord
from discord.ext import commands


class EmojiHelper(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.emoji_pattern = re.compile(r"<(a?):(\w+):(\d+)>")
        self.session = aiohttp.ClientSession()
        self.webhook_cache = {}

    async def cog_unload(self):
        await self.session.close()

    async def get_webhook(self, channel):
        if channel.id in self.webhook_cache:
            return self.webhook_cache[channel.id]

        try:
            webhooks = await channel.webhooks()
            webhook = discord.utils.get(
                webhooks, 
                user=self.bot.user, 
                name="EmojiEnlarger"
            )

            if not webhook:
                webhook = await channel.create_webhook(name="EmojiEnlarger")

            self.webhook_cache[channel.id] = webhook
            return webhook
        except discord.Forbidden:
            return None

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        content = message.content.strip()
        match = self.emoji_pattern.fullmatch(content)

        if match:
            is_animated = bool(match.group(1))
            emoji_id = match.group(3)
            ext = "gif" if is_animated else "png"
            emoji_url = (
                f"https://cdn.discordapp.com/emojis/{emoji_id}.{ext}?size=1024"
            )

            try:
                webhook = await self.get_webhook(message.channel)
                if not webhook:
                    return

                async with self.session.get(emoji_url) as resp:
                    if resp.status == 200:
                        data = await resp.read()

                        if message.guild.me.guild_permissions.manage_messages:
                            try:
                                await message.delete()
                            except discord.NotFound:
                                pass

                        file = discord.File(
                            io.BytesIO(data), 
                            filename=f"emoji.{ext}"
                        )
                        await webhook.send(
                            file=file,
                            username=message.author.display_name,
                            avatar_url=message.author.display_avatar.url
                        )
            except Exception as e:
                print(f"[오류] 이모지 확대 실패: {e}")

    @commands.command(name="addemoji")
    async def add_emoji(self, ctx, name: str, source: str = None):
        settings_cog = self.bot.get_cog('Settings')
        if settings_cog:
            guild_data = settings_cog.get_server_data(ctx.guild)
            allowed_channel_id = guild_data.get("emoji_command_channel_id")

            if allowed_channel_id and ctx.channel.id != allowed_channel_id:
                return await ctx.send(
                    f"❌ 이 명령어는 지정된 명령어 채널(<#{allowed_channel_id}>)에서만 사용할 수 있습니다.",
                    delete_after=5
                )
            
        if not re.fullmatch(r"^\w{2,32}$", name):
            return await ctx.send("❌ 이모지 이름은 2~32자의 영문, 숫자, 밑줄(_)만 가능합니다.")

        target_url = ""

        if ctx.message.attachments:
            target_url = ctx.message.attachments[0].url
        elif source:
            emoji_match = self.emoji_pattern.search(source)
            if emoji_match:
                is_animated = bool(emoji_match.group(1))
                ext = "gif" if is_animated else "png"
                target_url = (
                    f"https://cdn.discordapp.com/emojis/"
                    f"{emoji_match.group(3)}.{ext}"
                )
            else:
                target_url = source
        else:
            return await ctx.send("❌ 이미지 파일, URL, 또는 이모지를 입력해주세요.")

        async with ctx.typing():
            try:
                async with self.session.get(target_url) as response:
                    if response.status != 200:
                        return await ctx.send("❌ 이미지를 불러올 수 없습니다.")

                    if "image" not in response.content_type:
                        return await ctx.send("❌ 올바른 이미지 파일 형식이 아닙니다.")

                    image_data = await response.read()
                    if len(image_data) > 256000:
                        return await ctx.send("❌ 파일 용량이 너무 큽니다 (256KB 제한).")

                    new_emoji = await ctx.guild.create_custom_emoji(
                        name=name, 
                        image=image_data
                    )
                    embed = discord.Embed(
                        title="✅ 등록 완료!",
                        description=f"{new_emoji} (`:{name}:`)",
                        color=0x808080
                    )
                    await ctx.send(embed=embed)

            except discord.Forbidden:
                await ctx.send("❌ 봇에게 '이모지 관리' 권한이 없습니다.")
            except discord.HTTPException as e:
                await ctx.send(f"❌ 등록 실패 (슬롯 부족 또는 파일 문제): {e}")
            except Exception as e:
                await ctx.send(f"❌ 오류 발생: {e}")

    @commands.command(name="delemoji")
    @commands.has_permissions(administrator=True)
    async def delete_emoji(self, ctx, name: str):
        settings_cog = self.bot.get_cog('Settings')
        if settings_cog:
            guild_data = settings_cog.get_server_data(ctx.guild)
            allowed_channel_id = guild_data.get("emoji_command_channel_id")

            if allowed_channel_id and ctx.channel.id != allowed_channel_id:
                return await ctx.send(
                    f"❌ 이 명령어는 지정된 명령어 채널(<#{allowed_channel_id}>)에서만 사용할 수 있습니다.",
                    delete_after=5
                )

        emoji = discord.utils.get(ctx.guild.emojis, name=name)

        if not emoji:
            return await ctx.send(f"❌ `{name}` 이름을 가진 이모지를 찾을 수 없습니다.")

        async with ctx.typing():
            try:
                await emoji.delete(reason=f"{ctx.author}에 의한 이모지 삭제")
                
                embed = discord.Embed(
                    title="🗑️ 삭제 완료",
                    description=f"이모지 `:{name}:` 가 성공적으로 삭제되었습니다.",
                    color=0x808080
                )
                await ctx.send(embed=embed)

            except discord.Forbidden:
                await ctx.send("❌ 봇에게 '이모지 관리' 권한이 없습니다.")
            except discord.HTTPException as e:
                await ctx.send(f"❌ 삭제 실패: {e}")
            except Exception as e:
                await ctx.send(f"❌ 오류 발생: {e}")

async def setup(bot):
    await bot.add_cog(EmojiHelper(bot))