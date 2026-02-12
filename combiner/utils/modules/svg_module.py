import io
import re
import cairosvg
from PIL import Image

resample_mode = Image.Resampling.LANCZOS


def is_svg(svg_bytes) -> bool:
    return b"<svg" in svg_bytes.lstrip()


def remove_redundant_info(svg_bytes) -> bytes:
    svg = svg_bytes.decode("utf-8")
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


def replace_colors(svg_bytes, body_color: str, eyes_color: str, hair_color: str) -> bytes:
    svg_str = svg_bytes.decode("utf-8")
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


def svg_bytes_to_png(svg_bytes, target_size=None):
    try:
        svg_bytes = remove_redundant_info(svg_bytes)
        png_bytes = cairosvg.svg2png(bytestring=svg_bytes)

        img = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
        if target_size:
            img = img.resize(target_size, resample=resample_mode)

        output = io.BytesIO()
        img.save(output, format="PNG")
        return output.getvalue()
    except Exception as e:
        print(e)
