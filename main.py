import asyncio

from bot.bot import MashiBot
from configs.config import DISCORD_TOKEN


async def main():
    bot = MashiBot()
    await asyncio.create_task(bot.start(DISCORD_TOKEN))

if __name__ == '__main__':
    asyncio.run(main())
