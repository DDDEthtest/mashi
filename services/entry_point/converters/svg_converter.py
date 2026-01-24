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

    path_d = ""
    mask_elem = root.find(".//svg:mask", ns)

    # 1. Get raw contours without blur or sub-pixel shifts
    if mask_elem is not None:
        img_elem = mask_elem.find(".//svg:image", ns)
        if img_elem is not None:
            href = img_elem.get('{http://www.w3.org/1999/xlink}href') or img_elem.get('href')
            if 'base64,' in href:
                b64_str = "".join(href.split('base64,')[1].split())
                b64_str += '=' * (-len(b64_str) % 4)

                decoded = base64.b64decode(b64_str)
                nparr = np.frombuffer(decoded, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)

                if img is not None:
                    # Use Alpha channel if available
                    mask_bits = img[:, :, 3] if img.shape[2] == 4 else cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

                    # Back to simple threshold, no blur
                    _, thresh = cv2.threshold(mask_bits, 127, 255, cv2.THRESH_BINARY)

                    # Using raw points (CHAIN_APPROX_NONE) for maximum "line" accuracy
                    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

                    for c in contours:
                        pts = c.reshape(-1, 2)
                        if len(pts) > 0:
                            path_d += f"M {pts[0][0]} {pts[0][1]} "
                            for i in range(1, len(pts)):
                                path_d += f"L {pts[i][0]} {pts[i][1]} "
                            path_d += "Z "

    # 2. Swap logic while PRESERVING the Group's location
    for parent in root.iter():
        for child in list(parent):
            if child.get('mask') == 'url(#mh)':
                new_path = ET.Element('{http://www.w3.org/2000/svg}path')
                new_path.set('d', path_d)
                new_path.set('fill', '#0000ff')

                # CRITICAL: If the <g> had a transform, we MUST keep it or the path shifts
                if 'transform' in child.attrib:
                    new_path.set('transform', child.attrib['transform'])

                # If the <rect> inside had x/y, we apply them here if they weren't in the path
                rect = child.find(".//svg:rect", ns)
                if rect is not None:
                    if 'x' in rect.attrib or 'y' in rect.attrib:
                        # If the rect is shifted, the mask usually is too.
                        # Only use this if the path still looks "offset"
                        pass

                idx = list(parent).index(child)
                parent.insert(idx, new_path)
                parent.remove(child)

    # 3. Cleanup defs
    defs = root.find(".//svg:defs", ns)
    if defs is not None:
        root.remove(defs)

    return ET.tostring(root, encoding='utf-8')