import asyncio

import uvicorn

from data.db import db
from server.http_server import http_app
from server.server import app

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

def start_uvicorn():
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=443,
        log_level="info",
        ssl_keyfile="/etc/letsencrypt/live/katzemon.com/privkey.pem",
        ssl_certfile="/etc/letsencrypt/live/katzemon.com/fullchain.pem",
        access_log=True
    )


def start_uvicorn_80():
    uvicorn.run(http_app, host="0.0.0.0", port=80)


async def main():
    db.init()

    server_task = asyncio.to_thread(start_uvicorn)
    http_server_task = asyncio.to_thread(start_uvicorn_80)

    await asyncio.gather(server_task, http_server_task)


if __name__ == '__main__':
    asyncio.run(main())
