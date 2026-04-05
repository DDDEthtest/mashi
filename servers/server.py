import asyncio
import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from bots.mashi.mashi_bot import MashiBot
from configs.bot_config import MASHI_BOT_TOKEN
from configs.server_config import HTTP_PORT
from servers.routers.correction_router import correction_router
from servers.routers.mashup_router import mashup_router
from servers.routers.notifications_router import notification_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://mash-it.io", "https://www.mash-it.io", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    bot = MashiBot()
    asyncio.create_task(bot.start(MASHI_BOT_TOKEN))


app.include_router(mashup_router)
app.include_router(correction_router)
app.include_router(notification_router)


def start_server():
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=HTTP_PORT,
        log_level="info",
        access_log=True
    )
