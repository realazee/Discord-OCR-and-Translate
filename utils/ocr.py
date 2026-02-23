from __future__ import annotations

import logging
from dataclasses import dataclass
from io import BytesIO

import numpy as np
from PIL import Image

log = logging.getLogger(__name__)

# Lazy-initialized readers for different script families
_readers: dict[str, object] = {}

# EasyOCR requires compatible language groups — CJK can't be mixed with Latin.
# We define separate reader groups for each script family.
_READER_CONFIGS = {
    "latin": ["en"],
    "chinese": ["ch_sim", "en"],
    "japanese": ["ja", "en"],
    "korean": ["ko", "en"],
    "cyrillic": ["ru", "uk", "be", "bg", "mn"],
    "arabic": ["ar", "fa", "ur"],
    "devanagari": ["hi", "mr", "ne"],
}


@dataclass
class TextRegion:
    """A detected text region in an image."""

    bbox: list[list[int]]  # 4 corner points [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
    text: str
    confidence: float


def _get_reader(group: str) -> object:
    """Lazily initialize an EasyOCR reader for the given script group."""
    if group not in _readers:
        import easyocr

        langs = _READER_CONFIGS[group]
        log.info("Initializing EasyOCR reader for '%s' (%s)...", group, langs)
        _readers[group] = easyocr.Reader(langs, gpu=False)
        log.info("EasyOCR '%s' reader initialized.", group)
    return _readers[group]


def _run_reader(reader: object, image_np: np.ndarray) -> list[TextRegion]:
    """Run a single reader and return TextRegion results."""
    results = reader.readtext(image_np)  # type: ignore
    regions = []
    for bbox, text, confidence in results:
        bbox_int = [[int(pt[0]), int(pt[1])] for pt in bbox]
        if text.strip():
            regions.append(TextRegion(bbox=bbox_int, text=text.strip(), confidence=confidence))
    return regions


def detect_text(image_bytes: bytes) -> tuple[list[TextRegion], str]:
    """
    Detect text regions in an image using multiple script readers.

    Tries Latin, Chinese, Japanese, Korean, Cyrillic, Arabic, and Devanagari.
    Returns the results from whichever reader detected the most text with
    the highest average confidence.

    Args:
        image_bytes: Raw image bytes (PNG, JPEG, etc.)

    Returns:
        Tuple of (list of TextRegion, detected script group name).
    """
    image = Image.open(BytesIO(image_bytes)).convert("RGB")
    image_np = np.array(image)

    best_regions: list[TextRegion] = []
    best_score: float = 0.0
    best_group: str = "unknown"

    for group in _READER_CONFIGS:
        try:
            reader = _get_reader(group)
            regions = _run_reader(reader, image_np)

            if not regions:
                continue

            # Score = number of regions * average confidence
            avg_conf = sum(r.confidence for r in regions) / len(regions)
            score = len(regions) * avg_conf

            log.info(
                "Reader '%s': %d region(s), avg confidence %.2f, score %.2f",
                group, len(regions), avg_conf, score,
            )

            if score > best_score:
                best_score = score
                best_regions = regions
                best_group = group

        except Exception:
            log.exception("Error with '%s' reader, skipping", group)
            continue

    log.info("Best result: %d text region(s) from '%s' (score %.2f)", len(best_regions), best_group, best_score)
    return best_regions, best_group
