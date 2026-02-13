import asyncio
from io import BytesIO

import uvicorn
from fastapi import FastAPI, Response, status, Request, HTTPException
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import StreamingResponse

from balancer.balancer import Balancer
from bot.bot import MashiBot
from configs.config import DISCORD_TOKEN, HTTP_PORT
from data.postgres.daos.image_dao import ImageDao
from data.remote.images_api import ImagesApi
from utils.converters.apng_converter import apng_bytes_to_webp_bytes
from utils.converters.svg_converter import process_svg

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://mash-it.io", "https://www.mash-it.io","http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

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


@app.post("/api/mashi/approval_notify")
async def approval_notify(request: Request, response: Response):
    try:
        data = await request.json()
        if len(data) == 0:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {"message": "Invalid request"}

        await asyncio.gather(*[MashiBot.instance().notify(data, is_release=False)])
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

@app.get("/api/apng/{image_id}")
async def get_apng(image_id: str):
    try:
        url = f"https://ipfs.filebase.io/ipfs/{image_id}"
        src = ImageDao().get_webp_image(url)

        if src is None:
            apng_bytes = ImagesApi().get_image_src(url)
            src = apng_bytes_to_webp_bytes(apng_bytes)
            ImageDao().add_webp_image(url, src)

        return StreamingResponse(BytesIO(src), media_type="image/webp")
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Failed to convert image")

@app.get("/api/svg/{image_id}")
async def get_svg(image_id: str):
    try:
        url = f"https://ipfs.filebase.io/ipfs/{image_id}"
        src = ImageDao().get_svg_image(url)

        if src is None:
            svg_bytes = ImagesApi().get_image_src(url)
            src = process_svg(svg_bytes)
            ImageDao().add_svg_image(url, src)

        return StreamingResponse(BytesIO(src), media_type="image/svg+xml")
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Failed to convert image")


def start_http_server():
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=HTTP_PORT,
        log_level="info",
        access_log=True
    )
