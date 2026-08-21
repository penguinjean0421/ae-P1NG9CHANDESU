import json
import os

import discord
from discord import app_commands
from discord.ext import commands

class Aespa(commands.Cog) :
    def __init__(self, bot) :
        self.bot = bot

        base_path = os.path.dirname(os.path.abspath(__file__))
        self.data_file = os.path.join(base_path, "..", "data/aespa_data.json")

        with open(self.data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.aespa_data=data['aespa_data']
    
    async def send_aespa(self, interaction: discord.Interaction):
        data = self.aespa_data['aespa']
        embed = discord.Embed(title = f"{data['emoji']} Be my æ, aespa's SNS", color =0x9ceafe)

        embed.add_field(name = "aespa_exhibition", value = f"[바로가기](https://www.x.com/{data['aespa_exhibition']})", inline = False)
        embed.add_field(name = "aespa_WEEK", value = f"[바로가기](https://www.x.com/{data['aespa_week']})", inline = False)
        embed.add_field(name = "BiliBili", value = f"[바로가기](https://space.bilibili.com/{data['bilibili']})", inline = False)
        embed.add_field(name = "Douyin", value = f"[바로가기](https://v.douyin.com/{data['douyin']})", inline = False)
        embed.add_field(name = "Facebook", value = f"[바로가기](https://www.facebook.com/{data['facebook']})", inline = False)
        embed.add_field(name = "Homepage", value = f"[바로가기](https://{data['homepage']})", inline = False)
        embed.add_field(name = "Homepage JP", value = f"[바로가기](https://{data['homepagejp']})", inline = False)
        embed.add_field(name = "Instagram", value = f"[바로가기](https://www.instagram.com/{data['instagram']})", inline = False)
        embed.add_field(name = "Line", value = f"[바로가기](https://page.line.me/{data['line']})", inline = False)
        embed.add_field(name = "Pinterest", value = f"[바로가기](https://pinterest.com/{data['pinterest']})", inline = False)
        embed.add_field(name = "Snapchat", value = f"[바로가기](https://www.snapchat.com/@{data['snapchat']})", inline = False)
        embed.add_field(name = "Tiktok", value = f"[바로가기](https://www.tiktok.com/@{data['tiktok']})",inline = False)
        embed.add_field(name = "Twitter", value = f"[바로가기](https://www.x.com/{data['twitter']})", inline = False)
        embed.add_field(name = "Twitter JP", value = f"[바로가기](https://www.x.com/{data['twitterjp']})", inline = False)
        embed.add_field(name = "Weibo", value = f"[바로가기](https://weibo.com/u/{data['weibo']})", inline = False)
        embed.add_field(name = "Weverse", value = f"[바로가기](https://weverse.io/{data['weverse']})", inline = False)
        embed.add_field(name = "Xiaohongshu", value = f"[바로가기](https://www.xiaohongshu.com/user/profile/{data['xiaohongshu']})", inline = False)
        embed.add_field(name = "Youtube", value = f"[바로가기](https://www.youtube.com/@{data['youtube']})", inline = False)

        await interaction.response.send_message(embed=embed)

    async def send_sns(self, interaction: discord.Interaction, name):
        data = self.aespa_data[name]
        embed = discord.Embed(title = f"{data['emoji']} Be my æ, {name}'s SNS", color =0xc88ddd)

        if(name == "aespa"):
            embed.add_field(name = "Facebook", value = f"[바로가기](https://www.facebook.com/{data['facebook']})", inline = False)
            embed.add_field(name = "Instagram", value = f"[바로가기](https://www.instagram.com/{data['instagram']})", inline = False)
            embed.add_field(name = "Tiktok", value = f"[바로가기](https://www.tiktok.com/{data['tiktok']})",inline = False)
            embed.add_field(name = "Twitter", value = f"[바로가기](https://www.x.com/{data['twitter']})", inline = False)
            embed.add_field(name = "Weibo", value = f"[바로가기](https://weibo.com/u/{data['weibo']})", inline = False)            
            embed.add_field(name = "Youtube", value = f"[바로가기](https://www.youtube.com/{data['youtube']})", inline = False)

        elif name in ["karina", "giselle"] : 
            embed.add_field(name = "Instagram", value = f"[바로가기](https://www.instagram.com/{data['instagram']})", inline = False)

        elif name in ["winter"] : 
            embed.add_field(name = "Instagram", value = f"[바로가기](https://www.instagram.com/{data['instagram']})", inline = False)
            embed.add_field(name = "Pponyo's Instagram", value = f"[바로가기](https://www.instagram.com/{data['pponyo']})", inline = False)

        elif name == "ningning" :
            embed.add_field(name = "Instagram", value = f"[바로가기](https://www.instagram.com/{data['instagram']})", inline = False)
            embed.add_field(name = "Weibo", value = f"[바로가기](https://weibo.com/u/{data['weibo']})", inline = False)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name = "aespa", description="aespa's SNS")
    async def aespa(self, interaction: discord.Interaction):
        # await self.send_aespa(interaction)
        await self.send_sns(interaction, "aespa")

    @app_commands.command(name = "karina", description="KARINA's SNS")
    async def karina(self, interaction: discord.Interaction) :
        await self.send_sns(interaction, "karina")

    @app_commands.command(name = "giselle", description="GISELLE's SNS")
    async def giselle(self, interaction: discord.Interaction) :
        await self.send_sns(interaction, "giselle")

    @app_commands.command(name = "winter", description="WINTER's SNS")
    async def winter(self, interaction: discord.Interaction) :
        await self.send_sns(interaction, "winter")

    @app_commands.command(name = "ningning", description="NINGNING's SNS")
    async def ningning(self, interaction: discord.Interaction) :
        await self.send_sns(interaction, "ningning")

async def setup(bot) :
    await bot.add_cog(Aespa(bot))