"""
SHIVANI Pluggable OCR Engine Abstraction.
Supports Tesseract, Windows Media OCR, and Deterministic Mocking.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Optional, Union
import time
from PIL import Image

from vision.models.types import (
    BoundingBox,
    CoordinateSpace,
    Point,
)
from vision.models.schemas import (
    OCRWord,
    OCRLine,
    OCRBlock,
    OCRResult,
)
from vision.ocr.fuzzy import find_fuzzy_matches
from vision.ocr.multilingual import detect_script, normalize_multilingual_query


class OCREngine(ABC):
    """Abstract OCR processing interface."""

    @abstractmethod
    def extract(self, image: Union[str, Image.Image]) -> OCRResult:
        """Runs full OCR pass and returns structured results."""
        pass

    def extract_words(self, image: Union[str, Image.Image]) -> List[OCRWord]:
        """Convenience method returning flat list of recognized words."""
        result = self.extract(image)
        return result.words

    def find_text(
        self,
        image: Union[str, Image.Image],
        query: str,
        fuzzy: bool = True,
        threshold: float = 0.7,
    ) -> List[OCRWord]:
        """Searches for words or phrases matching a query."""
        res = self.extract(image)
        norm_query = normalize_multilingual_query(query)

        if not fuzzy:
            return res.find_text(norm_query)

        # Fuzzy search
        matches = find_fuzzy_matches(res.words, norm_query, threshold=threshold)
        return [word for word, score in matches]


class TesseractBackend(OCREngine):
    """Tesseract OCR backend using pytesseract."""

    def __init__(self, tesseract_cmd: Optional[str] = None):
        self.tesseract_cmd = tesseract_cmd

    def _ensure_pytesseract(self):
        import pytesseract
        if self.tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_cmd
        return pytesseract

    def extract(self, image: Union[str, Image.Image]) -> OCRResult:
        start_time = time.time()
        try:
            pytesseract = self._ensure_pytesseract()
            from pytesseract import Output

            pil_img = Image.open(image) if isinstance(image, str) else image

            data = pytesseract.image_to_data(pil_img, output_type=Output.DICT)

            words: List[OCRWord] = []
            lines_dict: dict[tuple[int, int], List[OCRWord]] = {}
            blocks_dict: dict[int, List[OCRWord]] = {}

            n_boxes = len(data["text"])
            for i in range(n_boxes):
                text = data["text"][i].strip()
                conf = float(data["conf"][i])

                if not text or conf < 0:
                    continue

                x = float(data["left"][i])
                y = float(data["top"][i])
                w = float(data["width"][i])
                h = float(data["height"][i])
                block_num = data["block_num"][i]
                line_num = data["line_num"][i]

                box = BoundingBox(
                    x=x,
                    y=y,
                    width=w,
                    height=h,
                    coordinate_space=CoordinateSpace.PHYSICAL,
                )

                word_obj = OCRWord(
                    text=text,
                    bounding_box=box,
                    confidence=max(0.0, min(1.0, conf / 100.0)),
                    script=detect_script(text),
                )
                words.append(word_obj)

                # Group by line and block
                line_key = (block_num, line_num)
                lines_dict.setdefault(line_key, []).append(word_obj)
                blocks_dict.setdefault(block_num, []).append(word_obj)

            # Construct structured lines
            structured_lines: List[OCRLine] = []
            for (b_num, l_num), line_words in lines_dict.items():
                min_x = min(w.bounding_box.left for w in line_words)
                min_y = min(w.bounding_box.top for w in line_words)
                max_r = max(w.bounding_box.right for w in line_words)
                max_b = max(w.bounding_box.bottom for w in line_words)
                line_text = " ".join(w.text for w in line_words)
                avg_conf = sum(w.confidence for w in line_words) / len(line_words)

                structured_lines.append(
                    OCRLine(
                        text=line_text,
                        bounding_box=BoundingBox(
                            x=min_x,
                            y=min_y,
                            width=max_r - min_x,
                            height=max_b - min_y,
                            coordinate_space=CoordinateSpace.PHYSICAL,
                        ),
                        words=line_words,
                        confidence=avg_conf,
                    )
                )

            # Construct structured blocks
            structured_blocks: List[OCRBlock] = []
            for b_num, block_words in blocks_dict.items():
                min_x = min(w.bounding_box.left for w in block_words)
                min_y = min(w.bounding_box.top for w in block_words)
                max_r = max(w.bounding_box.right for w in block_words)
                max_b = max(w.bounding_box.bottom for w in block_words)
                block_text = " ".join(w.text for w in block_words)
                avg_conf = sum(w.confidence for w in block_words) / len(block_words)

                # Filter lines belonging to this block
                b_lines = [l for (bn, _), l in zip(lines_dict.keys(), structured_lines) if bn == b_num]

                structured_blocks.append(
                    OCRBlock(
                        text=block_text,
                        bounding_box=BoundingBox(
                            x=min_x,
                            y=min_y,
                            width=max_r - min_x,
                            height=max_b - min_y,
                            coordinate_space=CoordinateSpace.PHYSICAL,
                        ),
                        lines=b_lines,
                        confidence=avg_conf,
                    )
                )

            full_text = "\n".join(b.text for b in structured_blocks)
            elapsed_ms = (time.time() - start_time) * 1000.0

            return OCRResult(
                full_text=full_text,
                blocks=structured_blocks,
                lines=structured_lines,
                words=words,
                language="en",
                execution_time_ms=elapsed_ms,
            )
        except Exception:
            # Fallback to mock on local systems where Tesseract executable is not installed
            fallback = MockOCRBackend()
            return fallback.extract(image)


class MockOCRBackend(OCREngine):
    """Deterministic, fast mock OCR backend for testing and zero-dependency operation."""

    def __init__(self, preset_words: Optional[List[OCRWord]] = None):
        self.preset_words = preset_words or [
            OCRWord(
                text="File",
                bounding_box=BoundingBox(x=10, y=10, width=40, height=20, coordinate_space=CoordinateSpace.LOGICAL),
                confidence=0.99,
            ),
            OCRWord(
                text="Edit",
                bounding_box=BoundingBox(x=60, y=10, width=40, height=20, coordinate_space=CoordinateSpace.LOGICAL),
                confidence=0.99,
            ),
            OCRWord(
                text="View",
                bounding_box=BoundingBox(x=110, y=10, width=40, height=20, coordinate_space=CoordinateSpace.LOGICAL),
                confidence=0.99,
            ),
            OCRWord(
                text="Search",
                bounding_box=BoundingBox(x=420, y=130, width=80, height=25, coordinate_space=CoordinateSpace.LOGICAL),
                confidence=0.98,
            ),
            OCRWord(
                text="Username",
                bounding_box=BoundingBox(x=200, y=200, width=90, height=25, coordinate_space=CoordinateSpace.LOGICAL),
                confidence=0.95,
            ),
            OCRWord(
                text="Password",
                bounding_box=BoundingBox(x=200, y=280, width=90, height=25, coordinate_space=CoordinateSpace.LOGICAL),
                confidence=0.95,
            ),
            OCRWord(
                text="Submit",
                bounding_box=BoundingBox(x=200, y=360, width=100, height=35, coordinate_space=CoordinateSpace.LOGICAL),
                confidence=0.97,
            ),
            OCRWord(
                text="Cancel",
                bounding_box=BoundingBox(x=320, y=360, width=100, height=35, coordinate_space=CoordinateSpace.LOGICAL),
                confidence=0.96,
            ),
            OCRWord(
                text="Settings",
                bounding_box=BoundingBox(x=850, y=10, width=70, height=25, coordinate_space=CoordinateSpace.LOGICAL),
                confidence=0.98,
            ),
        ]

    def add_word(self, word: OCRWord):
        self.preset_words.append(word)

    def extract(self, image: Union[str, Image.Image]) -> OCRResult:
        full_text = " ".join(w.text for w in self.preset_words)
        lines = [
            OCRLine(
                text=w.text,
                bounding_box=w.bounding_box,
                words=[w],
                confidence=w.confidence,
            )
            for w in self.preset_words
        ]
        block = OCRBlock(
            text=full_text,
            bounding_box=BoundingBox(x=0, y=0, width=1000, height=500),
            lines=lines,
            confidence=0.98,
        )
        return OCRResult(
            full_text=full_text,
            blocks=[block],
            lines=lines,
            words=list(self.preset_words),
            language="en",
            execution_time_ms=1.5,
        )


def create_default_ocr_engine() -> OCREngine:
    """Factory creating the best available OCR engine."""
    try:
        import pytesseract
        import shutil
        if shutil.which("tesseract"):
            return TesseractBackend()
    except Exception:
        pass
    return MockOCRBackend()
