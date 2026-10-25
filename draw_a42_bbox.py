from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image

from bench.overlay import draw_bbox_on_image, get_case_bbox, normalized_bbox_to_pixels


PROJECT_ROOT = Path(__file__).resolve().parent
REPO_ROOT = PROJECT_ROOT.parent
DEFAULT_CASES = PROJECT_ROOT / "tasks/A4.2/DentXpertBench-cases-v3.2-A4.2-2026-10-19.json"
DEFAULT_IMAGE_ROOT = REPO_ROOT / "公开数据集/公开数据集"
DEFAULT_OUTPUT = PROJECT_ROOT / "preview/a4_2_bbox_case_001.jpg"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Draw an A4.2 target_bbox on its source image.")
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--image-root", type=Path, default=DEFAULT_IMAGE_ROOT)
    parser.add_argument("--case-index", type=int, default=1, help="1-based case index")
    parser.add_argument("--case-id", default=None)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--line-width", type=int, default=6)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = json.loads(args.cases.read_text(encoding="utf-8"))
    cases = payload["cases"]

    if args.case_id:
        matches = [case for case in cases if case.get("id") == args.case_id]
        if not matches:
            raise SystemExit(f"case id not found: {args.case_id}")
        case = matches[0]
    else:
        if not 1 <= args.case_index <= len(cases):
            raise SystemExit(f"case index must be between 1 and {len(cases)}")
        case = cases[args.case_index - 1]

    image_meta = case["input"]["images"][0]
    image_path = args.image_root / image_meta["path"]
    bbox = get_case_bbox(case)
    with Image.open(image_path) as image:
        pixel_bbox = normalized_bbox_to_pixels(bbox, image.width, image.height)
    output_path = draw_bbox_on_image(image_path, bbox, args.output, args.line_width)

    print(json.dumps({
        "case_id": case["id"],
        "image": str(image_path),
        "normalized_bbox": bbox,
        "pixel_bbox": pixel_bbox,
        "output": str(output_path),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
