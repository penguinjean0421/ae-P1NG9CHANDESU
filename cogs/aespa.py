import json
import os

import discord
from discord.ext import commands

class Aespa(commands.Cog) :
    def __init__(self, bot) :
        self.bot = bot

        base_path = os.path.dirname(os.path.abspath(__file__))
        self.data_file = os.path.join(base_path, "..", "data/aespa_data.json")

        with open(self.data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.aespa_data=data['aespa_data']
    
    async def send_aespa(self, ctx):
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

        await ctx.send(embed = embed)

    async def send_sns(self, ctx, name):
        data = self.aespa_data[name]
        embed = discord.Embed(title = f"{data['emoji']} Be my æ, {name}'s SNS", color =0xc88ddd)

        if(name == "aespa"):
            embed.add_field(name = "Facebook", value = f"[바로가기](https://www.facebook.com/{data['facebook']})", inline = False)
            embed.add_field(name = "Instagram", value = f"[바로가기](https://www.instagram.com/{data['instagram']})", inline = False)
            embed.add_field(name = "Tiktok", value = f"[바로가기](https://www.tiktok.com/{data['tiktok']})",inline = False)
            embed.add_field(name = "Twitter", value = f"[바로가기](https://www.x.com/{data['twitter']})", inline = False)
            embed.add_field(name = "Weibo", value = f"[바로가기](https://weibo.com/u/{data['weibo']})", inline = False)            
            embed.add_field(name = "Youtube", value = f"[바로가기](https://www.youtube.com/{data['youtube']})", inline = False)

        elif name in ["karina", "giselle", "winter"] : 
            embed.add_field(name = "Instagram", value = f"[바로가기](https://www.instagram.com/{data['instagram']})", inline = False)

        elif name == "ningning" :
            embed.add_field(name = "Instagram", value = f"[바로가기](https://www.instagram.com/{data['instagram']})", inline = False)
            embed.add_field(name = "Weibo", value = f"[바로가기](https://weibo.com/u/{data['weibo']})", inline = False)

        await ctx.send(embed = embed)

    @commands.command(name = "aespa", aliases = ['에스파'])
    async def aespa(self, ctx):
        # await self.send_aespa(ctx)
        await self.send_sns(ctx, "aespa")

    @commands.command(name = "karina", aliases = ['카리나'])
    async def karina(self, ctx) :
        await self.send_sns(ctx, "karina")

    @commands.command(name = "giselle", aliases = ['지젤'])
    async def giselle(self, ctx) :
        await self.send_sns(ctx, "giselle")

    @commands.command(name = "winter", aliases = [ '윈터'])
    async def winter(self, ctx) :
        await self.send_sns(ctx, "winter")

    @commands.command(name = "ningning", aliases = ['닝닝'])
    async def ningning(self, ctx) :
        await self.send_sns(ctx, "ningning")

async def setup(bot) :
    await bot.add_cog(Aespa(bot))