import asyncio
from servers.server import start_server
from data.postgres.postgres_manager import db_manager, Base

from data.postgres.entities.mashup import Mashup
from data.postgres.entities.contest import Contest
from data.postgres.entities.image import Image
from data.postgres.entities.mashup import Mashup
from data.postgres.entities.user import User

async def main():
    # await prefetch_async()
    Base.metadata.create_all(db_manager.engine)
    server_task = asyncio.to_thread(start_server)
    await asyncio.gather(server_task)


if __name__ == '__main__':
    asyncio.run(main())
