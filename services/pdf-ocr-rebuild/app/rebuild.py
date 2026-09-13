import statistics
from collections import defaultdict
from pathlib import Path

import pymupdf

FONT_PATH = Path(__file__).resolve().parent / "fonts" / "DejaVuSans.ttf"
FONT_NAME = "DejaVuSans"

MIN_FONT_SIZE = 4
MAX_FONT_SIZE = 72


def build_pdf_from_pages(pages_data: list, min_confidence: float) -> "pymupdf.Document":
    doc = pymupdf.open()

    for page_info in pages_data:
        page = doc.new_page(width=page_info["width_pt"], height=page_info["height_pt"])
        page.insert_font(fontname=FONT_NAME, fontfile=str(FONT_PATH))

        scale = 72 / page_info["dpi"]
        words = [w for w in page_info["words"] if w["conf"] >= min_confidence]

        lines = defaultdict(list)
        for word in words:
            lines[word["line_key"]].append(word)

        for line_words in lines.values():
            line_top = min(w["top"] for w in line_words) * scale
            line_height = statistics.median(w["height"] for w in line_words) * scale
            font_size = max(MIN_FONT_SIZE, min(MAX_FONT_SIZE, line_height * 0.8))
            baseline_y = line_top + line_height * 0.85

            for word in line_words:
                x = word["left"] * scale
                page.insert_text(
                    (x, baseline_y),
                    word["text"],
                    fontsize=font_size,
                    fontname=FONT_NAME,
                )

    return doc
