from io import BytesIO

from fastapi import HTTPException, APIRouter
from starlette.responses import StreamingResponse

from data.models.image_type import ImageType
from data.postgres.daos.image_dao import ImageDao
from data.remote.ipfs_api import get_image_src
from utils.converters.apng_converter import convert_apng_to_webp
from utils.converters.svg_converter import process_svg
from utils.helpers.image_helper import get_image_type


correction_router = APIRouter()

@correction_router.get("/api/apng/{image_id}")
async def convert_apng_async(image_id: str):
    image_dao = ImageDao()
    try:
        url = f"https://ipfs.io/ipfs/{image_id}"
        src = image_dao.get_webp_image(url)

        if src is None:
            apng_bytes = get_image_src(url)
            src = convert_apng_to_webp(apng_bytes)

            if get_image_type(src) is ImageType.WEBP:
                image_dao.add_webp_image(url, src)

        return StreamingResponse(BytesIO(src), media_type="image/webp")
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Failed to convert apng to webp")

@correction_router.get("/api/svg/{image_id}")
async def correct_svg_async(image_id: str):
    image_dao = ImageDao()

    try:
        url = f"https://ipfs.io/ipfs/{image_id}"
        src = image_dao.get_svg_image(url)

        if src is None:
            svg_bytes = get_image_src(url)
            src = process_svg(svg_bytes)

            if get_image_type(src) is ImageType.SVG:
                image_dao.add_svg_image(url, src)

        return StreamingResponse(BytesIO(src), media_type="image/svg+xml")
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Failed to correct svg")
