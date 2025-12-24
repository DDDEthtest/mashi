import asyncio

from fastapi import FastAPI, Response, status, Request

from bot.bot import MashiBot
from config.config import DISCORD_TOKEN, NOTIFY_API_ROUTE
from utils.io.test_data_io import save_test_mashi_data

app = FastAPI()


@app.on_event("startup")
async def startup():
    bot = MashiBot()
    asyncio.create_task(bot.start(DISCORD_TOKEN))


@app.post(NOTIFY_API_ROUTE)
async def release_notify(request: Request, response: Response):
    try:
        data = await request.json()
        if len(data) == 0:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {"message": "Invalid request"}

        await asyncio.gather(*[MashiBot.instance().release_notify(data)])
        response.status_code = status.HTTP_200_OK
        return {"message": "Data received"}

    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {"message": e}


@app.post("/api/test_mashi")
async def test_mashi(request: Request, response: Response):
    try:
        data = await request.json()
        save_test_mashi_data(data)

        response.status_code = status.HTTP_200_OK
        return {"message": "Data saved"}

    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {"message": e}

