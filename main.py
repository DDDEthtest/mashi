import asyncio

from servers.main_server import start_http_server
from data.postgres.postgres_manager import db_manager, Base
from data.postgres.entities.user import User
from data.postgres.entities.mashup import Mashup
from data.postgres.entities.image import Image
from utils.caching.prefetching import prefetch


async def main():
    await prefetch()
    # Base.metadata.create_all(db_manager.engine)
    # server_task = asyncio.to_thread(start_http_server)
    # await asyncio.gather(server_task)


if __name__ == '__main__':
    asyncio.run(main())
