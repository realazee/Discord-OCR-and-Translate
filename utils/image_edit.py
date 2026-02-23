from __future__ import annotations

import logging
import math
import os
import textwrap
from io import BytesIO
from typing import TYPE_CHECKING

import numpy as np
from PIL import Image, ImageDraw, ImageFont

if TYPE_CHECKING:
    from utils.ocr import TextRegion

log = logging.getLogger(__name__)

# Try to locate a bundled Noto Sans font for broad script support
_FONT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fonts")
_FONT_PATHS = [
    os.path.join(_FONT_DIR, "NotoSans-Regular.ttf"),
    os.path.join(_FONT_DIR, "NotoSansCJKsc-Regular.otf"),
]


def _find_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Load a bundled font at the given size, falling back to default."""
    for path in _FONT_PATHS:
        if os.path.isfile(path):
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    # Try common system fonts
    for name in ["Arial.ttf", "DejaVuSans.ttf", "Helvetica.ttc",
                 "/System/Library/Fonts/Helvetica.ttc",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    log.warning("No TrueType font found, using Pillow default (limited quality).")
    return ImageFont.load_default()


def _sample_background_color(
    image: Image.Image, bbox: list[list[int]], border_px: int = 4
) -> tuple[int, int, int]:
    """
    Estimate the background color around a text bounding box by sampling
    pixels along the edges of the region.
    """
    img_array = np.array(image)
    h, w = img_array.shape[:2]

    x_coords = [pt[0] for pt in bbox]
    y_coords = [pt[1] for pt in bbox]

    x_min = max(0, min(x_coords) - border_px)
    x_max = min(w - 1, max(x_coords) + border_px)
    y_min = max(0, min(y_coords) - border_px)
    y_max = min(h - 1, max(y_coords) + border_px)

    border_pixels = []

    # Top edge
    if y_min >= 0:
        for y in range(max(0, y_min - border_px), min(h, y_min + 1)):
            for x in range(x_min, x_max + 1):
                border_pixels.append(img_array[y, x])
    # Bottom edge
    if y_max < h:
        for y in range(max(0, y_max), min(h, y_max + border_px + 1)):
            for x in range(x_min, x_max + 1):
                border_pixels.append(img_array[y, x])
    # Left edge
    if x_min >= 0:
        for x in range(max(0, x_min - border_px), min(w, x_min + 1)):
            for y in range(y_min, y_max + 1):
                border_pixels.append(img_array[y, x])
    # Right edge
    if x_max < w:
        for x in range(max(0, x_max), min(w, x_max + border_px + 1)):
            for y in range(y_min, y_max + 1):
                border_pixels.append(img_array[y, x])

    if not border_pixels:
        return (255, 255, 255)  # fallback to white

    colors = np.array(border_pixels)
    median = np.median(colors, axis=0).astype(int)
    return (int(median[0]), int(median[1]), int(median[2]))


def _get_text_color(bg_color: tuple[int, int, int]) -> tuple[int, int, int]:
    """Choose black or white text based on background luminance."""
    luminance = 0.299 * bg_color[0] + 0.587 * bg_color[1] + 0.114 * bg_color[2]
    return (0, 0, 0) if luminance > 128 else (255, 255, 255)


def _fit_text_in_bbox(
    draw: ImageDraw.ImageDraw,
    text: str,
    bbox: list[list[int]],
    text_color: tuple[int, int, int],
) -> None:
    """
    Render text within a bounding box, auto-sizing and wrapping as needed.
    """
    x_coords = [pt[0] for pt in bbox]
    y_coords = [pt[1] for pt in bbox]
    box_x = min(x_coords)
    box_y = min(y_coords)
    box_w = max(x_coords) - box_x
    box_h = max(y_coords) - box_y

    if box_w <= 0 or box_h <= 0:
        return

    # Start with a font size proportional to box height, then shrink to fit
    font_size = max(8, int(box_h * 0.85))
    min_font_size = max(6, int(box_h * 0.2))
    padding = 2

    while font_size >= min_font_size:
        font = _find_font(font_size)

        # Estimate characters per line
        avg_char_w = font_size * 0.6  # rough average character width
        chars_per_line = max(1, int((box_w - 2 * padding) / avg_char_w))

        wrapped = textwrap.fill(text, width=chars_per_line)
        lines = wrapped.split("\n")

        # Measure actual text dimensions
        text_bbox = draw.multiline_textbbox((0, 0), wrapped, font=font)
        text_w = text_bbox[2] - text_bbox[0]
        text_h = text_bbox[3] - text_bbox[1]

        if text_w <= box_w - 2 * padding and text_h <= box_h - 2 * padding:
            # Center text in the bounding box
            text_x = box_x + (box_w - text_w) // 2
            text_y = box_y + (box_h - text_h) // 2
            draw.multiline_text(
                (text_x, text_y), wrapped, fill=text_color, font=font, align="center"
            )
            return

        font_size -= 1

    # If we exhausted sizes, draw at minimum size anyway
    font = _find_font(min_font_size)
    avg_char_w = min_font_size * 0.6
    chars_per_line = max(1, int((box_w - 2 * padding) / avg_char_w))
    wrapped = textwrap.fill(text, width=chars_per_line)
    text_bbox = draw.multiline_textbbox((0, 0), wrapped, font=font)
    text_w = text_bbox[2] - text_bbox[0]
    text_h = text_bbox[3] - text_bbox[1]
    text_x = box_x + (box_w - text_w) // 2
    text_y = box_y + (box_h - text_h) // 2
    draw.multiline_text(
        (text_x, text_y), wrapped, fill=text_color, font=font, align="center"
    )


def render_translated_image(
    image_bytes: bytes,
    regions: list[TextRegion],
    translated_texts: list[str],
) -> bytes:
    """
    Replace original text in the image with translated text.

    For each region:
      1. Fill the bounding box with the estimated background color.
      2. Render the translated text inside the box.

    Args:
        image_bytes: Original image bytes.
        regions: Detected text regions from OCR.
        translated_texts: Translated strings, one per region.

    Returns:
        Modified image as PNG bytes.
    """
    image = Image.open(BytesIO(image_bytes)).convert("RGB")
    draw = ImageDraw.Draw(image)

    for region, translated in zip(regions, translated_texts):
        bbox = region.bbox

        # 1. Sample background color and fill the text region
        bg_color = _sample_background_color(image, bbox)
        polygon = [(pt[0], pt[1]) for pt in bbox]
        draw.polygon(polygon, fill=bg_color)

        # 2. Choose contrasting text color and render
        text_color = _get_text_color(bg_color)
        _fit_text_in_bbox(draw, translated, bbox, text_color)

    # Save as PNG
    output = BytesIO()
    image.save(output, format="PNG")
    output.seek(0)
    return output.read()
