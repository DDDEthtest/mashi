import io
import base64
import cv2
import numpy as np
import xml.etree.ElementTree as ET
import copy

ET.register_namespace("", "http://www.w3.org/2000/svg")
ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")

def _pretty_xml(elem, level=0):
    """In-place pretty formatter that also trims useless whitespace."""
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

def process_svg(input_bytes):
    tree = ET.parse(io.BytesIO(input_bytes))
    root = tree.getroot()

    ns = {
        'svg': 'http://www.w3.org/2000/svg',
        'xlink': 'http://www.w3.org/1999/xlink'
    }

    # --- 1. Map every Mask ID to its calculated path data ---
    mask_definitions = {}

    for mask_elem in root.findall(".//svg:mask", ns):
        mask_id = mask_elem.get('id')
        if not mask_id:
            continue

        combined_path_d = ""

        for img_elem in mask_elem.findall(".//svg:image", ns):
            href = img_elem.get('{http://www.w3.org/1999/xlink}href') or img_elem.get('href')
            if not href or 'base64,' not in href:
                continue

            # Decode Base64
            try:
                b64_str = "".join(href.split('base64,')[1].split())
                b64_str += '=' * (-len(b64_str) % 4)
                nparr = np.frombuffer(base64.b64decode(b64_str), np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)
            except:
                continue

            if img is None:
                continue

            h, w = img.shape[:2]
            if img.ndim == 3 and img.shape[2] == 4:
                mask_bits = img[:, :, 3]
            else:
                mask_bits = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            _, thresh = cv2.threshold(mask_bits, 127, 255, cv2.THRESH_BINARY)
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            img_x = float(img_elem.get('x', 0))
            img_y = float(img_elem.get('y', 0))

            for c in contours:
                if cv2.contourArea(c) < 10:
                    continue

                pts = c.reshape(-1, 2)
                combined_path_d += f"M {pts[0][0] + img_x} {pts[0][1] + img_y} "
                for i in range(1, len(pts)):
                    combined_path_d += f"L {pts[i][0] + img_x} {pts[i][1] + img_y} "
                combined_path_d += "Z "

        if combined_path_d:
            mask_definitions[f"url(#{mask_id})"] = combined_path_d.strip()

    # --- 2. Replace masked elements with vector paths ---
    for parent in root.iter():
        # Iterate over a static list of children to avoid issues while modifying
        children = list(parent)
        for i, child in enumerate(children):
            mask_attr = child.get('mask')
            if mask_attr not in mask_definitions:
                continue

            path_d = mask_definitions.get(mask_attr)
            fill_color = child.get('fill')
            opacity = child.get('opacity') or child.get('fill-opacity')

            if not fill_color or fill_color == 'none':
                inner_shape = child.find(".//*[@fill]", ns)
                if inner_shape is not None:
                    fill_color = inner_shape.get('fill')
                    opacity = opacity or inner_shape.get('opacity') or inner_shape.get('fill-opacity')

            new_path = ET.Element('{http://www.w3.org/2000/svg}path')
            new_path.set('d', path_d)
            new_path.set('fill', fill_color if fill_color else "#000000")
            new_path.set('fill-rule', 'evenodd')
            if opacity: new_path.set('opacity', opacity)
            if 'transform' in child.attrib: new_path.set('transform', child.attrib['transform'])

            # Direct replacement by index
            parent[i] = new_path

    # --- 3. Replace <use> tags with actual elements ---
    defs_map = {f"#{elem.get('id')}": elem for elem in root.iter() if elem.get('id')}

    for parent in root.iter():
        children = list(parent)
        for i, use_elem in enumerate(children):
            if use_elem.tag != f"{{{ns['svg']}}}use":
                continue

            href = use_elem.get('href') or use_elem.get(f"{{{ns['xlink']}}}href")
            if href in defs_map:
                referenced_node = copy.deepcopy(defs_map[href])

                # Handle positioning
                ux, uy = use_elem.get('x', '0'), use_elem.get('y', '0')
                if ux != '0' or uy != '0':
                    exist_tr = referenced_node.get('transform', '')
                    referenced_node.set('transform', f"translate({ux}, {uy}) {exist_tr}".strip())

                # Inherit attributes from <use>
                for attr, val in use_elem.attrib.items():
                    if attr not in ['href', f"{{{ns['xlink']}}}href", 'x', 'y', 'id']:
                        referenced_node.set(attr, val)

                # Direct replacement by index
                parent[i] = referenced_node

    # --- 4. Cleanup ---
    for defs in root.findall(".//svg:defs", ns):
        # We only remove direct children of <defs> to avoid ValueError
        # for images nested inside masks or groups within defs.
        for img in list(defs.findall("svg:image", ns)):
            defs.remove(img)

        for m in list(defs.findall("svg:mask", ns)):
            defs.remove(m)

    # Remove clipPathUnits
    for clip_path in root.findall(".//svg:clipPath", ns):
        if 'clipPathUnits' in clip_path.attrib:
            del clip_path.attrib['clipPathUnits']

    # --- 5. Finalize ---
    _pretty_xml(root)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True, method="xml")