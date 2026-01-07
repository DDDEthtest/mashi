import asyncio
from io import BytesIO

import uvicorn
from fastapi import FastAPI, Response, status, Request, HTTPException
from starlette.responses import StreamingResponse

from bot.bot import MashiBot
from configs.config import DISCORD_TOKEN, HTTP_PORT
from data.repos.mashi_repo import MashiRepo

app = FastAPI()


@app.on_event("startup")
async def startup():
    bot = MashiBot()
    asyncio.create_task(bot.start(DISCORD_TOKEN))


@app.post("/api/mashi/release_notify")
async def release_notify(request: Request, response: Response):
    try:
        data = await request.json()
        if len(data) == 0:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {"message": "Invalid request"}

        await asyncio.gather(*[MashiBot.instance().notify(data)])
        response.status_code = status.HTTP_200_OK
        return {"message": "Data received"}

    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {"message": e}


@app.get("/api/mashi/mashup/{wallet}")
async def get_mashup(wallet: str, img_type: int = 0):
    if img_type == 0:
        media_type = "image/png"
    else:
        media_type = "image/gif"

    if img_type not in range(0, 3):
        raise HTTPException(status_code=404, detail="Wrong image type")

    data = await MashiRepo.instance().get_composite(wallet, img_type=img_type)

    if not data or not isinstance(data, bytes):
        raise HTTPException(status_code=404, detail="No mashup found for this wallet")

    buffer = BytesIO(data)
    buffer.seek(0)
    return StreamingResponse(buffer, media_type=media_type)


def start_http_server():
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=HTTP_PORT,
        log_level="info",
        access_log=True
    )
