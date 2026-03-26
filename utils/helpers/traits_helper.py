import asyncio
from configs.img_config import ANIM_STEP
from data.models.image_type import ImageType
from utils.helpers.image_helper import get_image_type, get_gif_duration, get_webp_duration, get_apng_duration


async def _get_duration(data: bytes) -> float:
    image_type = get_image_type(data)

    if image_type is ImageType.GIF:
        duration = await asyncio.to_thread(get_gif_duration, data)
        return duration

    if image_type is ImageType.WEBP:
        duration = await asyncio.to_thread(get_webp_duration, data)
        return duration

    if image_type is ImageType.APNG:
        duration = await asyncio.to_thread(get_apng_duration, data)
        return duration

    return ANIM_STEP


async def get_durations(traits: list[bytes]) -> list[float]:
    tasks = [_get_duration(trait) for trait in traits]
    results = await asyncio.gather(*tasks)
    return list(results)
