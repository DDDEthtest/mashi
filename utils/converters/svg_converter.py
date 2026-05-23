import io
import base64
import copy
import cv2
import numpy as np
import xml.etree.ElementTree as ET

ET.register_namespace("", "http://www.w3.org/2000/svg")
ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")


def _pretty_xml(elem, level=0):
    indent = "  "
    i = "\n" + level * indent

    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + indent

        for child in elem:
            _pretty_xml(child, level + 1)

        if not elem[-1].tail or not elem[-1].tail.strip():
            elem[-1].tail = i

    else:
        if not elem.text or not elem.text.strip():
            elem.text = None

    if level and (not elem.tail or not elem.tail.strip()):
        elem.tail = i


def extract_paint_style(style_str):
    """
    Keep only paint-related CSS properties.
    Prevents invisible layers caused by:
    - clip-path
    - filters
    - blend modes
    - isolation
    """

    if not style_str:
        return ""

    allowed = {
        "fill",
        "fill-opacity",
        "opacity",
        "stroke",
        "stroke-width",
        "stroke-opacity",
        "paint-order",
    }

    out = []

    for item in style_str.split(";"):

        if ":" not in item:
            continue

        k, v = item.split(":", 1)

        k = k.strip()
        v = v.strip()

        if k in allowed:
            out.append(f"{k}:{v}")

    return ";".join(out)


def build_contour_path(mask_bits, img_x=0, img_y=0):

    _, thresh = cv2.threshold(
        mask_bits,
        8,
        255,
        cv2.THRESH_BINARY
    )

    contours, hierarchy = cv2.findContours(
        thresh,
        cv2.RETR_CCOMP,
        cv2.CHAIN_APPROX_SIMPLE
    )

    if contours is None or len(contours) == 0:
        return ""

    path_parts = []

    for contour in contours:

        if cv2.contourArea(contour) < 2:
            continue

        pts = contour.reshape(-1, 2)

        if len(pts) < 3:
            continue

        path_parts.append(
            f"M {pts[0][0] + img_x} {pts[0][1] + img_y}"
        )

        for pt in pts[1:]:
            path_parts.append(
                f"L {pt[0] + img_x} {pt[1] + img_y}"
            )

        path_parts.append("Z")

    return " ".join(path_parts)


def process_svg(input_bytes):

    tree = ET.parse(io.BytesIO(input_bytes))
    root = tree.getroot()

    ns = {
        "svg": "http://www.w3.org/2000/svg",
        "xlink": "http://www.w3.org/1999/xlink"
    }

    SVG_NS = "http://www.w3.org/2000/svg"

    # =========================================================
    # 1. Build mask -> contour path map
    # =========================================================

    mask_definitions = {}

    for mask_elem in root.findall(".//svg:mask", ns):

        mask_id = mask_elem.get("id")

        if not mask_id:
            continue

        combined_paths = []

        for img_elem in mask_elem.findall(".//svg:image", ns):

            href = (
                img_elem.get("{http://www.w3.org/1999/xlink}href")
                or img_elem.get("href")
            )

            if not href or "base64," not in href:
                continue

            try:
                b64_str = "".join(
                    href.split("base64,")[1].split()
                )

                b64_str += "=" * (-len(b64_str) % 4)

                img_bytes = base64.b64decode(b64_str)

                nparr = np.frombuffer(
                    img_bytes,
                    np.uint8
                )

                img = cv2.imdecode(
                    nparr,
                    cv2.IMREAD_UNCHANGED
                )

            except Exception:
                continue

            if img is None:
                continue

            # Use alpha if available
            if img.ndim == 3 and img.shape[2] == 4:
                mask_bits = img[:, :, 3]
            else:
                mask_bits = cv2.cvtColor(
                    img,
                    cv2.COLOR_BGR2GRAY
                )

            img_x = float(img_elem.get("x", 0))
            img_y = float(img_elem.get("y", 0))

            path_d = build_contour_path(
                mask_bits,
                img_x,
                img_y
            )

            if path_d:
                combined_paths.append(path_d)

        if combined_paths:
            mask_definitions[
                f"url(#{mask_id})"
            ] = " ".join(combined_paths)

    # =========================================================
    # 2. Replace masked elements
    # =========================================================

    DRAWABLE_TAGS = {
        "path",
        "rect",
        "circle",
        "ellipse",
        "polygon",
        "polyline",
    }

    VISUAL_ATTRS = [
        "fill",
        "fill-opacity",
        "opacity",
        "stroke",
        "stroke-width",
        "stroke-opacity",
        "paint-order",
        "style",
        "class",
        "transform",
    ]

    for parent in root.iter():

        children = list(parent)

        for i, child in enumerate(children):

            mask_attr = child.get("mask")

            if mask_attr not in mask_definitions:
                continue

            path_d = mask_definitions[mask_attr]

            # -------------------------------------------------
            # Find drawable style source
            # -------------------------------------------------

            style_source = child

            local_tag = child.tag.split("}")[-1]

            if local_tag == "g":

                for inner in child.iter():

                    inner_tag = inner.tag.split("}")[-1]

                    if inner_tag in DRAWABLE_TAGS:
                        style_source = inner
                        break

            # -------------------------------------------------
            # Create replacement path
            # -------------------------------------------------

            new_path = ET.Element(
                f"{{{SVG_NS}}}path"
            )

            # -------------------------------------------------
            # Parent styles first
            # -------------------------------------------------

            for attr in VISUAL_ATTRS:

                val = child.get(attr)

                if val is None:
                    continue

                if attr == "style":
                    val = extract_paint_style(val)

                    if not val:
                        continue

                new_path.set(attr, val)

            # -------------------------------------------------
            # Drawable styles second
            # -------------------------------------------------

            for attr in VISUAL_ATTRS:

                if attr in new_path.attrib:
                    continue

                val = style_source.get(attr)

                if val is None:
                    continue

                if attr == "style":
                    val = extract_paint_style(val)

                    if not val:
                        continue

                new_path.set(attr, val)

            # -------------------------------------------------
            # Geometry
            # -------------------------------------------------

            new_path.set("d", path_d)

            new_path.set(
                "fill-rule",
                "evenodd"
            )

            # -------------------------------------------------
            # Replace original node
            # -------------------------------------------------

            parent[i] = new_path

    # =========================================================
    # 3. Replace <use> with actual nodes
    # =========================================================

    defs_map = {
        f"#{elem.get('id')}": elem
        for elem in root.iter()
        if elem.get("id")
    }

    for parent in root.iter():

        children = list(parent)

        for i, use_elem in enumerate(children):

            if use_elem.tag != f"{{{SVG_NS}}}use":
                continue

            href = (
                use_elem.get("href")
                or use_elem.get(
                    f"{{{ns['xlink']}}}href"
                )
            )

            if href not in defs_map:
                continue

            referenced_node = copy.deepcopy(
                defs_map[href]
            )

            ux = use_elem.get("x", "0")
            uy = use_elem.get("y", "0")

            transforms = []

            if ux != "0" or uy != "0":
                transforms.append(
                    f"translate({ux},{uy})"
                )

            existing_transform = referenced_node.get(
                "transform"
            )

            if existing_transform:
                transforms.append(existing_transform)

            if transforms:
                referenced_node.set(
                    "transform",
                    " ".join(transforms)
                )

            for attr, val in use_elem.attrib.items():

                if attr not in [
                    "href",
                    f"{{{ns['xlink']}}}href",
                    "x",
                    "y",
                    "id"
                ]:
                    referenced_node.set(attr, val)

            parent[i] = referenced_node

    # =========================================================
    # 4. Cleanup defs
    # =========================================================

    for defs in root.findall(".//svg:defs", ns):

        for img in list(defs.findall("svg:image", ns)):
            defs.remove(img)

        for mask in list(defs.findall("svg:mask", ns)):
            defs.remove(mask)

    for clip_path in root.findall(".//svg:clipPath", ns):

        if "clipPathUnits" in clip_path.attrib:
            del clip_path.attrib["clipPathUnits"]

    # =========================================================
    # 5. Final XML
    # =========================================================

    _pretty_xml(root)

    return ET.tostring(
        root,
        encoding="utf-8",
        xml_declaration=True,
        method="xml"
    )