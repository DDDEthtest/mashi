from data.models.image_format import ImageFormat
from data.models.traits_info import TraitsInfo
from utils.helpers.apng_helper import get_apng_info, check_if_apng
from utils.helpers.gif_helper import is_gif


def get_traits_info(sorted_traits):
    traits_info = []
    total_ts = []

    for trait in sorted_traits:
        is_apng = check_if_apng(trait)
        gif = is_gif(trait)
        if is_apng:
            num_frames, total_duration = get_apng_info(trait)
            traits_info.append(
                TraitsInfo(
                    frames=num_frames,
                    frame_t=total_duration/num_frames,
                    total_t=total_duration,
                    is_animated=True,
                    img_format=ImageFormat.APNG,
                )
            )
            total_ts.append(total_duration)
        elif gif:
            traits_info.append(
                TraitsInfo(
                    frames=1,
                    frame_t=0.1,
                    total_t=0.1,
                    is_animated=False,
                    img_format=ImageFormat.GIF,
                )
            )
        else:
            traits_info.append(
                TraitsInfo(
                    frames=1,
                    frame_t=0.1,
                    total_t=0.1,
                    is_animated=False
                )
            )
            total_ts.append(0.1)

    return traits_info, total_ts