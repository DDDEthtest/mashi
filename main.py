import asyncio
from servers.server import start_server
from data.postgres.postgres_manager import db_manager, Base


async def main():
    # await prefetch_async()
    Base.metadata.create_all(db_manager.engine)
    server_task = asyncio.to_thread(start_server)
    await asyncio.gather(server_task)


if __name__ == '__main__':
    asyncio.run(main())
