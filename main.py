import asyncio
import os
from pathlib import Path
from typing import List

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()


class P1ng9chandesu(commands.Bot):
    def __init__(self):
        raw_prefixes = os.getenv("BOT_PREFIXES")
        prefixes: List[str] = [p.strip() for p in raw_prefixes.split(",")]

        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        intents.voice_states = True

        super().__init__(
            command_prefix=prefixes,
            intents=intents,
            help_command=None
        )

    async def setup_hook(self):
        """봇 실행 시 Cog 파일 자동 로드"""
        cogs_path = Path(__file__).parent / "cogs"

        if not cogs_path.exists():
            cogs_path.mkdir()
            print("📂 'cogs' 폴더가 없어 새로 생성합니다.")

        for filepath in cogs_path.glob("*.py"):
            if filepath.stem.startswith("__"):
                continue

            cog_name = f"cogs.{filepath.stem}"
            try:
                await self.load_extension(cog_name)
                print(f"✅ {cog_name} 로드 성공")
            except Exception as e:
                print(f"❌ {cog_name} 로드 실패 -> {e}")

    async def on_ready(self):
        print("-" * 30)
        print(f"🟢 {self.user.name} 온라인")
        print(f"🆔 ID: {self.user.id}")
        print(f"🔢 접두사: {', '.join(self.command_prefix)}")
        print("-" * 30)
        await self.change_presence()


async def main():
    bot = P1ng9chandesu()
    token = os.getenv("BOT_TOKEN")

    if not token:
        print("❌ 오류: BOT_TOKEN이 .env에서 설정되지 않았습니다.")
        return

    async with bot:
        try:
            await bot.start(token)
        except discord.LoginFailure:
            print("❌ 오류: 토큰이 유효하지 않음")
        except Exception as e:
            print(f"❌ 실행 중 오류 발생: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n종료 신호 감지, 봇 종료.")