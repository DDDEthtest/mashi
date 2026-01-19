import asyncio
from io import BytesIO

import uvicorn
from fastapi import FastAPI, Response, status, Request, HTTPException
from starlette.responses import StreamingResponse

from services.entry_point.balancer.balancer import Balancer
from services.entry_point.bot.bot import MashiBot
from services.entry_point.configs.config import DISCORD_TOKEN, HTTP_PORT

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
async def get_mashup(response: Response, wallet: str, img_type: int = 0):
    try:
        if img_type == 0:
            media_type = "image/png"
        else:
            media_type = "image/gif"

        if img_type not in range(0, 3):
            raise HTTPException(status_code=404, detail="Wrong image type")

        data = await Balancer.instance().get_composite(wallet, img_type=img_type)

        if not data or not isinstance(data, bytes):
            raise HTTPException(status_code=404, detail="No mashup found for this wallet")

        buffer = BytesIO(data)
        buffer.seek(0)
        return StreamingResponse(buffer, media_type=media_type)
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {"message": e}


def start_http_server():
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=HTTP_PORT,
        log_level="info",
        access_log=True
    )
