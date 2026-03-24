import io
import re
import cairosvg
from PIL import Image

resample_mode = Image.Resampling.LANCZOS


def is_svg(data: bytes) -> bool:
    return b"<svg" in data.lstrip()


def remove_redundant_info(data: bytes) -> bytes:
    svg = data.decode("utf-8")
    svg = re.sub(r'^\s*<\?xml[^>]*\?>', '', svg, flags=re.MULTILINE | re.IGNORECASE)
    svg = re.sub(r'<!DOCTYPE[^>]*>', '', svg, flags=re.IGNORECASE)
    svg = re.sub(r'serif:[^"]*"[^"]*"', '', svg)
    svg = re.sub(r'<sodipodi:namedview\b[^>]*?>[\s\S]*?<\/sodipodi:namedview>', '', svg)
    svg = re.sub(r"<sodipodi:namedview\b[^>]*/>", "", svg)
    svg = re.sub(r'\s*sodipodi:[^=]+="[^"]*"', '', svg)
    svg = re.sub(r'\s*inkscape:[^=]+="[^"]*"', '', svg)
    svg = re.sub(r'<SODI[^>]*>', '', svg)
    svg = re.sub(r'<!--.*?-->', '', svg, flags=re.DOTALL)
    return svg.lstrip().replace('\n', '').encode("utf-8")


def replace_colors(data: bytes, body_color: str, eyes_color: str, hair_color: str) -> bytes:
    svg_str = data.decode("utf-8")
    # replace body color
    svg_str = re.sub(
        r"#00ff00|#0f0\b|\blime\b|rgb\s*\(\s*0\s*,\s*255\s*,\s*0\s*\)",
        body_color, svg_str, flags=re.IGNORECASE
    )

    # replace eyes color
    svg_str = re.sub(
        r"#ffff00|#ff0\b|\byellow\b|rgb\s*\(\s*255\s*,\s*255\s*,\s*0\s*\)",
        eyes_color, svg_str, flags=re.IGNORECASE
    )

    # replace hair color
    svg_str = re.sub(
        r"#0000ff|#00f\b|\bblue\b|rgb\s*\(\s*0\s*,\s*0\s*,\s*255\s*\)",
        hair_color, svg_str, flags=re.IGNORECASE
    )
    return svg_str.replace('\n', '').encode("utf-8")


def convert_svg_to_png(data: bytes, target_size=None):
    try:
        data = remove_redundant_info(data)
        png_bytes = cairosvg.svg2png(bytestring=data)

        img = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
        if target_size:
            img = img.resize(target_size, resample=resample_mode)

        output = io.BytesIO()
        img.save(output, format="PNG")
        return output.getvalue()
    except Exception as e:
        print(e)
