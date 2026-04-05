from io import BytesIO
from fastapi import Response, status, HTTPException, APIRouter
from starlette.responses import StreamingResponse
from balancer.balancer import request_composite_async
from data.models.download_type import DownloadType

mashup_router = APIRouter()


@mashup_router.get("/api/mashi/mashup/{wallet}")
async def get_mashup(response: Response, wallet: str, download_type: str = "png"):
    try:
        if download_type == "png":
            media_type = "image/png"
        elif download_type == "gif":
            media_type = "image/gif"
        else:
            raise HTTPException(status_code=500, detail="Wrong download type: should be either png or gif")

        download_type = DownloadType(download_type.upper())

        data = await request_composite_async(wallet, download_type=download_type)

        if not data or not isinstance(data, bytes):
            raise HTTPException(status_code=404, detail="No mashup found for this wallet")

        buffer = BytesIO(data)
        buffer.seek(0)
        return StreamingResponse(buffer, media_type=media_type)

    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {"message": e}
