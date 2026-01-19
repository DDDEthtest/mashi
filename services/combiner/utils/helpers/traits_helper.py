import asyncio

from configs.config import ANIM_STEP
from utils.modules.apng_module import get_apng_t, is_apng
from utils.modules.gif_module import is_gif, get_gif_t
from utils.modules.webp_module import is_webp, get_webp_t


async def process_trait(trait):
    if is_gif(trait):
        total_duration = await asyncio.to_thread(get_gif_t, trait)
        return total_duration
    elif is_webp(trait):
        total_duration = await asyncio.to_thread(get_webp_t, trait)
        return total_duration
    elif is_apng(trait):
        total_duration = await asyncio.to_thread(get_apng_t, trait)
        return total_duration
    else:
        return ANIM_STEP


async def get_traits_info(sorted_traits):
    tasks = [process_trait(trait) for trait in sorted_traits]
    results = await asyncio.gather(*tasks)
    total_ts = list(results)
    return total_ts
