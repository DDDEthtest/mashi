import io
import base64
import cv2
import numpy as np
import xml.etree.ElementTree as ET

ET.register_namespace("", "http://www.w3.org/2000/svg")
ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")


def process_svg(input_bytes):
    tree = ET.parse(io.BytesIO(input_bytes))
    root = tree.getroot()
    ns = {'svg': 'http://www.w3.org/2000/svg', 'xlink': 'http://www.w3.org/1999/xlink'}

    # 1. Map every Mask ID to its calculated path data
    mask_definitions = {}

    for mask_elem in root.findall(".//svg:mask", ns):
        mask_id = mask_elem.get('id')
        if not mask_id:
            continue

        combined_path_d = ""

        # Process every image contributing to this specific mask
        for img_elem in mask_elem.findall(".//svg:image", ns):
            href = img_elem.get('{http://www.w3.org/1999/xlink}href') or img_elem.get('href')
            if href and 'base64,' in href:
                # Decode B64
                b64_str = "".join(href.split('base64,')[1].split())
                b64_str += '=' * (-len(b64_str) % 4)

                nparr = np.frombuffer(base64.b64decode(b64_str), np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)

                if img is not None:
                    h, w = img.shape[:2]
                    # Get Alpha or convert Grayscale
                    mask_bits = img[:, :, 3] if img.shape[2] == 4 else cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

                    # Thresholding (adjust 127 if mask is very light)
                    _, thresh = cv2.threshold(mask_bits, 127, 255, cv2.THRESH_BINARY)
                    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                    # Get positional offsets of the image within the mask
                    img_x = float(img_elem.get('x', 0))
                    img_y = float(img_elem.get('y', 0))

                    for c in contours:
                        bx, by, bw, bh = cv2.boundingRect(c)
                        # Avoid tracing the image frame (prevents "solid block" output)
                        if bw >= w - 1 and bh >= h - 1:
                            continue
                        # Filter noise
                        if cv2.contourArea(c) < 5:
                            continue

                        pts = c.reshape(-1, 2)
                        combined_path_d += f"M {pts[0][0] + img_x} {pts[0][1] + img_y} "
                        for i in range(1, len(pts)):
                            combined_path_d += f"L {pts[i][0] + img_x} {pts[i][1] + img_y} "
                        combined_path_d += "Z "

        mask_definitions[f"url(#{mask_id})"] = combined_path_d

    # 2. Iterate through all elements to find those using the masks
    for parent in root.iter():
        for child in list(parent):
            mask_attr = child.get('mask')

            if mask_attr in mask_definitions and mask_definitions[mask_attr]:
                # --- COLOR EXTRACTION LOGIC ---
                # Check child attributes first, then look inside for a rect/path
                fill_color = child.get('fill')
                opacity = child.get('opacity') or child.get('fill-opacity')

                if not fill_color or fill_color == 'none':
                    # Look for a nested shape that might have the fill
                    inner_shape = child.find(".//*[@fill]", ns)
                    if inner_shape is not None:
                        fill_color = inner_shape.get('fill')
                        opacity = opacity or inner_shape.get('opacity') or inner_shape.get('fill-opacity')

                # Create the new Path replacement
                new_path = ET.Element('{http://www.w3.org/2000/svg}path')
                new_path.set('d', mask_definitions[mask_attr])
                new_path.set('fill', fill_color if fill_color else "#000000")
                new_path.set('fill-rule', 'evenodd')

                if opacity:
                    new_path.set('opacity', opacity)

                # Transfer transformations from the original masked group/element
                if 'transform' in child.attrib:
                    new_path.set('transform', child.attrib['transform'])

                # Replace the masked element with our new vector path
                idx = list(parent).index(child)
                parent.insert(idx, new_path)
                parent.remove(child)

    # 3. Clean up used mask definitions
    for defs in root.findall(".//svg:defs", ns):
        for m in defs.findall("svg:mask", ns):
            defs.remove(m)

    return ET.tostring(root, encoding='utf-8')