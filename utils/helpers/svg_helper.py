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


def _parse_svg_dimensions(svg: str) -> tuple[int, int]:
    """Extract width and height from SVG root element attributes or viewBox."""
    # Try width/height attributes first
    w_match = re.search(r'<svg[^>]+\bwidth=["\']([0-9.]+)(px)?["\']', svg, re.IGNORECASE)
    h_match = re.search(r'<svg[^>]+\bheight=["\']([0-9.]+)(px)?["\']', svg, re.IGNORECASE)

    if w_match and h_match:
        return int(float(w_match.group(1))), int(float(h_match.group(1)))

    # Fall back to viewBox
    vb_match = re.search(r'viewBox=["\']([0-9.\s,]+)["\']', svg, re.IGNORECASE)
    if vb_match:
        parts = re.split(r'[\s,]+', vb_match.group(1).strip())
        if len(parts) == 4:
            return int(float(parts[2])), int(float(parts[3]))

    # Last resort: default
    return 760, 1200


async def convert_svg_to_png(svg_bytes: bytes) -> bytes:
    async with async_playwright() as p:
        svg = svg_bytes.decode("utf-8")
        width, height = _parse_svg_dimensions(svg)

        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": width, "height": height})

        await page.set_content(svg)

        # Ensure the SVG fills the page exactly
        await page.add_style_tag(content="html, body { margin: 0; padding: 0; overflow: hidden; }")

        png = await page.locator("svg").screenshot(
            type="png",
            omit_background=True,
        )

        await browser.close()
        return png