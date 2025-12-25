import re

def generate_minted_svg(nft_name: str) -> bytes:
    pattern = r"(.+)\s+by\s+(.+)"
    match = re.match(pattern, nft_name)
    if match:
        before_by = match.group(1)  # Text before "by"
    else:
        before_by = nft_name

    if len(before_by) > 16 + 3 + 4:
        index = before_by.find("#")
        before_by = f"{before_by[:16]}... {before_by[index:]}"

    return (f"""<svg xmlns="http://www.w3.org/2000/svg" width="1104" height="1472">
    <defs>
        <style type="text/css">
            .custom-text {{
                font-family: sans-serif;
                font-size: 68px;
                font-weight: 900;
                fill: white;
                stroke: black;
                stroke-width: 3px;
            }}
        </style>
    </defs>
    <rect width="100%" height="100%" fill="none"/>
    <text 
        x="48" 
        y="{1472 - 48}" 
        class="custom-text" 
    >
        {before_by}
    </text>
</svg>""".encode("utf-8"))