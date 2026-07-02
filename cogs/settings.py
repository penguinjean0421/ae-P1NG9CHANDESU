import json
import os
import re

import discord
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

    @commands.command(name="set")
    @commands.has_permissions(administrator=True)
    async def set_command(self, ctx, category: str = None, target: str = None, channel: discord.abc.GuildChannel = None):
        """서버 설정을 카테고리별로 지정합니다."""
        
        log_map = {
            "server": "server_log_channel_id",
            "punish": "punish_log_channel_id",
            "ticket": "ticket_log_channel_id"
        }
        cmd_map = {
            "bot": "command_channel_id",
            "emoji": "emoji_command_channel_id"
        }

        async def send_usage():
            embed = discord.Embed(title="❓ 사용법 안내", color=0x808080)
            embed.add_field(name="로그 설정", value=f"`{ctx.prefix}set log [server/punish/ticket] [#텍스트채널]`", inline=False)
            embed.add_field(name="명령어 채널 설정", value=f"`{ctx.prefix}set command [bot/emoji/ticket] [#텍스트채널]`", inline=False)
            embed.add_field(name="스팸 필터 채널 설정", value=f"`{ctx.prefix}set spam [#텍스트채널]`", inline=False)
            embed.add_field(name="🔊 음성 생성 채널 설정", value=f"`{ctx.prefix}set voice [생성채널ID 또는 음성채널이름]`", inline=False)
            return await ctx.send(embed=embed)

        if not category:
            return await send_usage()

        category = category.lower()

        if category not in ["spam", "voice"] and not target:
            return await send_usage()
        
        gid = str(ctx.guild.id)
        self.get_server_data(ctx.guild)

        if category == "log":
            target = target.lower()
            if target not in log_map:
                return await send_usage()
            
            target_channel = channel or ctx.channel
            self.server_configs[gid][log_map[target]] = target_channel.id
            embed = discord.Embed(
                title=f"✅ Log - {target.upper()} 채널 설정",
                description=f"{target.upper()} 채널이 {target_channel.mention}로 설정되었습니다.",
                color=0x808080
            )

        elif category == "command":
            target = target.lower()
            target_channel = channel or ctx.channel
            if target == "ticket":
                ticket_cog = self.bot.get_cog('Ticket')
                if ticket_cog:
                    await self.delete_ticket_panel(ctx.guild)
                    panel_msg = await ticket_cog.send_ticket_panel(target_channel)
                    if panel_msg:
                        self.server_configs[gid]["ticket_panel_channel_id"] = target_channel.id
                        self.server_configs[gid]["ticket_panel_msg_id"] = panel_msg.id
                        embed = discord.Embed(
                            title="✅ TICKET 채널 생성",
                            description=f"**TICKET** 채널이 {target_channel.mention}로 설정되었으며, 티켓 패널이 생성되었습니다.",
                            color=0x808080
                        )
                    else:
                        return await ctx.send(embed=discord.Embed(description="❌ 티켓 패널 메시지 생성에 실패했습니다.", color=0x808080))
                else:
                    return await ctx.send(embed=discord.Embed(description="❌ Ticket Cog가 로드되지 않아 패널을 생성할 수 없습니다.", color=0x808080))

            elif target in cmd_map:
                self.server_configs[gid][cmd_map[target]] = target_channel.id
                embed = discord.Embed(
                    title=f"✅ COMMAND - {target.upper()} 채널 설정",
                    description=f"{target.upper()} 채널이 {target_channel.mention}로 설정되었습니다.",
                    color=0x808080
                )
            else:
                return await send_usage()

        elif category == "spam":
            if target and not channel:
                channel_match = re.match(r"<#(\d+)>", target)
                if channel_match:
                    target_channel = ctx.guild.get_channel(int(channel_match.group(1)))
                elif target.isdigit():
                    target_channel = ctx.guild.get_channel(int(target))
                else:
                    target_channel = ctx.channel
            else:
                target_channel = channel or ctx.channel

            self.server_configs[gid]["spam_filter_channel_id"] = target_channel.id
            embed = discord.Embed(
                title="✅ **SPAM FILTER** 채널 설정",
                description=f"SPAM FILTER 채널이 {target_channel.mention}로 설정되었습니다.",
                color=0x808080
            )

        elif category == "voice":
            voice_channel = None
            if target:
                if target.isdigit():
                    voice_channel = ctx.guild.get_channel(int(target))
                else:
                    voice_channel = discord.utils.get(ctx.guild.voice_channels, name=target)

            if isinstance(channel, discord.VoiceChannel):
                voice_channel = channel

            if not isinstance(voice_channel, discord.VoiceChannel):
                embed=discord.Embed(
                    title="❌ 올바른 음성 채널 정보(ID 또는 이름)를 입력",
                    description=(
                        f"예시 1: `{ctx.prefix}set voice 1234567890`\n"
                        f"예시 2: `{ctx.prefix}set voice ➕방만들기`"
                        ),
                        color=0x808080
                )
                return await ctx.send(embed=embed)

            self.server_configs[gid]["create_voice_channel_id"] = voice_channel.id
            embed = discord.Embed(
                title="✅ **VOICE CREATOR** 채널 설정",
                description=f"방 만들기 전용 음성 채널이 {voice_channel.mention} (ID: `{voice_channel.id}`)로 지정되었습니다.",
                color=0x808080
            )

        else:
            return await send_usage()

        self.save_config()
        await ctx.send(embed=embed)

    @commands.command(name="reset")
    @commands.has_permissions(administrator=True)
    async def reset_command(self, ctx, category: str = None, target: str = None):
        """서버 설정을 초기화하거나 특정 설정을 제거합니다."""
        gid = str(ctx.guild.id)
        
        log_map = {
            "server": "server_log_channel_id",
            "punish": "punish_log_channel_id",
            "ticket": "ticket_log_channel_id"
        }
        cmd_map = {
            "bot": "command_channel_id",
            "emoji": "emoji_command_channel_id"
        }

        async def send_usage():
            embed = discord.Embed(title="❓ 사용법 안내", color=0x808080)
            embed.add_field(name="전체 초기화", value=f"`{ctx.prefix}reset all`", inline=False)
            embed.add_field(name="로그 제거", value=f"`{ctx.prefix}reset log [server/punish/ticket]`", inline=False)
            embed.add_field(name="명령어 채널 제거", value=f"`{ctx.prefix}reset command [bot/emoji/ticket]`", inline=False)
            embed.add_field(name="스팸 필터 제거", value=f"`{ctx.prefix}reset spam`", inline=False)
            embed.add_field(name="음성 생성 채널 제거", value=f"`{ctx.prefix}reset voice`", inline=False)
            return await ctx.send(embed=embed)

        if not category:
            return await send_usage()

        category = category.lower()

        if category == "all":
            await self.delete_ticket_panel(ctx.guild)
            self.server_configs.pop(gid, None)
            embed = discord.Embed(description="✅ 모든 설정이 초기화되었습니다.", color=0x808080)

        elif category == "log":
            if not target or target.lower() not in log_map:
                return await send_usage()
            target = target.lower()
            if gid in self.server_configs:
                self.server_configs[gid][log_map[target]] = None
                embed = discord.Embed(description=f"✅ **LOG -> {target.upper()}** 설정이 제거되었습니다.", color=0x808080)
            else:
                embed = discord.Embed(description="❌ 설정된 데이터가 없습니다.", color=0x808080)

        elif category == "command":
            if not target:
                return await send_usage()
            target = target.lower()
            if gid in self.server_configs:
                if target == "ticket":
                    await self.delete_ticket_panel(ctx.guild)
                    self.server_configs[gid]["ticket_panel_channel_id"] = None
                    self.server_configs[gid]["ticket_panel_msg_id"] = None
                    embed = discord.Embed(description="✅ **COMMAND - TICKET** 설정 및 티켓 패널이 제거되었습니다.", color=0x808080)
                elif target in cmd_map:
                    self.server_configs[gid][cmd_map[target]] = None
                    embed = discord.Embed(description=f"✅ **COMMAND - {target.upper()}** 설정이 제거되었습니다.", color=0x808080)
                else:
                    return await send_usage()
            else:
                embed = discord.Embed(description="❌ 설정된 데이터가 없습니다.", color=0x808080)
        
        elif category == "voice":
            if gid in self.server_configs:
                self.server_configs[gid]["create_voice_channel_id"] = None
                embed = discord.Embed(description="✅ **VOICE CREATOR** 설정이 제거되었습니다.", color=0x808080)
            else:
                embed = discord.Embed(description="❌ 설정된 데이터가 없습니다.", color=0x808080)


        elif category == "spam":
            if gid in self.server_configs:
                self.server_configs[gid]["spam_filter_channel_id"] = None
                embed = discord.Embed(description="✅ **SPAM FILTER** 설정이 제거되었습니다.", color=0x808080)
            else:
                embed = discord.Embed(description="❌ 설정된 데이터가 없습니다.", color=0x808080)
        
        else:
            return await send_usage()

        self.save_config()
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Settings(bot))