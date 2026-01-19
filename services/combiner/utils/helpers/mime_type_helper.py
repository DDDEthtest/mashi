from services.combiner.utils.modules.gif_module import is_gif
from services.combiner.utils.modules.svg_module import is_svg
from services.combiner.utils.modules.webp_module import is_webp


def get_mime_type(data: bytes) -> str:
    if is_svg(data): return "image/svg+xml"
    if is_webp(data): return "image/webp"
    if is_gif(data): return "image/gif"
    return "image/png"
