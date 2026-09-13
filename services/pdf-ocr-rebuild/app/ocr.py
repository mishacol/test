import pymupdf
import pytesseract
from PIL import Image


def render_page_to_image(page: "pymupdf.Page", dpi: int) -> Image.Image:
    zoom = dpi / 72
    pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom))
    return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)


def ocr_page_words(image: Image.Image, lang: str) -> list:
    data = pytesseract.image_to_data(image, lang=lang, output_type=pytesseract.Output.DICT)
    words = []
    for i in range(len(data["text"])):
        text = data["text"][i].strip()
        try:
            conf = float(data["conf"][i])
        except (TypeError, ValueError):
            conf = -1.0
        if not text or conf < 0:
            continue
        words.append(
            {
                "text": text,
                "left": data["left"][i],
                "top": data["top"][i],
                "width": data["width"][i],
                "height": data["height"][i],
                "conf": conf,
                "line_key": (data["block_num"][i], data["par_num"][i], data["line_num"][i]),
            }
        )
    return words
