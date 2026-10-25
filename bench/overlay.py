from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw


def normalized_bbox_to_pixels(bbox: list[float], width: int, height: int) -> tuple[int, int, int, int]:
    """Convert [left, top, right, bottom] normalized coordinates to pixels."""
    if len(bbox) != 4:
        raise ValueError(f"bbox must contain four values: {bbox}")
    left, top, right, bottom = (float(value) for value in bbox)
    if not (0 <= left < right <= 1 and 0 <= top < bottom <= 1):
        raise ValueError(f"bbox must be normalized and ordered: {bbox}")
    return (
        round(left * width),
        round(top * height),
        round(right * width),
        round(bottom * height),
    )


def draw_bbox_on_image(
    image_path: Path,
    bbox: list[float],
    output_path: Path,
    line_width: int = 6,
) -> Path:
    """Draw a red target box on an image and save the annotated copy."""
    if line_width < 1:
        raise ValueError("line_width must be positive")

    with Image.open(image_path) as source:
        image = source.convert("RGB")
        pixel_bbox = normalized_bbox_to_pixels(bbox, image.width, image.height)
        draw = ImageDraw.Draw(image)
        draw.rectangle(pixel_bbox, outline=(255, 0, 0), width=line_width)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(output_path)
    return output_path


def get_case_bbox(case: dict[str, Any]) -> list[float]:
    for field in case.get("input", {}).get("fields", []):
        if field.get("key") == "target_bbox":
            value = field.get("value")
            if not isinstance(value, list):
                break
            return [float(item) for item in value]
    raise ValueError(f"case has no target_bbox: {case.get('id')}")
