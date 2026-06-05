import re
from playwright.async_api import async_playwright


def remove_redundant_metadata(data: bytes) -> bytes:
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


def replace_svg_colors(data: bytes, body_color: str, eyes_color: str, hair_color: str) -> bytes:
    svg_str = data.decode("utf-8")

    svg_str = re.sub(
        r"#00ff00|#0f0\b|\blime\b|rgb\s*\(\s*0\s*,\s*255\s*,\s*0\s*\)",
        body_color, svg_str, flags=re.IGNORECASE
    )

    svg_str = re.sub(
        r"#ffff00|#ff0\b|\byellow\b|rgb\s*\(\s*255\s*,\s*255\s*,\s*0\s*\)",
        eyes_color, svg_str, flags=re.IGNORECASE
    )

    svg_str = re.sub(
        r"#0000ff|#00f\b|\bblue\b|rgb\s*\(\s*0\s*,\s*0\s*,\s*255\s*\)",
        hair_color, svg_str, flags=re.IGNORECASE
    )
    return svg_str.replace('\n', '').encode("utf-8")


async def convert_svg_to_png(svg_bytes):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        svg = svg_bytes.decode("utf-8")

        await page.set_content(svg)

        png = await page.locator("svg").screenshot(
            type="png",
            omit_background=True
        )

        await browser.close()

        return png