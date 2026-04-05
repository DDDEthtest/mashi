import asyncio

from fastapi import Response, status, Request, APIRouter

from bots.mashi.mashi_bot import MashiBot

notification_router = APIRouter()

@notification_router.post("/api/mashi/release_notify")
async def release_notify(request: Request, response: Response):
    try:
        data = await request.json()
        if len(data) == 0:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {"message": "Invalid request"}

        await asyncio.gather(*[MashiBot.instance().notify_async(data)])
        response.status_code = status.HTTP_200_OK
        return {"message": "Data received"}

    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {"message": e}


@notification_router.post("/api/mashi/approval_notify")
async def approval_notify(request: Request, response: Response):
    try:
        data = await request.json()
        if len(data) == 0:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {"message": "Invalid request"}

        await asyncio.gather(*[MashiBot.instance().notify_async(data, is_release=False)])
        response.status_code = status.HTTP_200_OK
        return {"message": "Data received"}

    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {"message": e}