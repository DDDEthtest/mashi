from io import BytesIO

import uvicorn
from fastapi import FastAPI, Response, status, Request, HTTPException
from starlette.responses import StreamingResponse

from services.combiner.configs.config import GENERATOR_SERVER_PORT
from services.combiner.data.repos.mashi_repo import MashiRepo

app = FastAPI()


@app.post("/gif")
async def gif(request: Request, response: Response):
    try:
        res = await request.json()
        if len(res) == 0:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {"message": "Invalid request"}

        data = await MashiRepo.instance().get_composite(res, img_type=1)

        if not data or not isinstance(data, bytes):
            raise HTTPException(status_code=404, detail="No mashup found for this wallet")

        buffer = BytesIO(data)
        buffer.seek(0)
        return StreamingResponse(buffer, media_type="image/gif")

    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {"message": e}


@app.post("/png")
async def gif(request: Request, response: Response):
    try:
        res = await request.json()
        if len(res) == 0:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {"message": "Invalid request"}

        data = await MashiRepo.instance().get_composite(res)

        if not data or not isinstance(data, bytes):
            raise HTTPException(status_code=404, detail="No mashup found for this wallet")

        buffer = BytesIO(data)
        buffer.seek(0)
        return StreamingResponse(buffer, media_type="image/png")

    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {"message": e}


def start_http_server():
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=GENERATOR_SERVER_PORT,
        log_level="info",
        access_log=True
    )
