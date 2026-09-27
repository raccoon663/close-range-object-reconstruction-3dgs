from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from ultralytics import SAM


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate object masks with a SAM 2 box prompt.")
    parser.add_argument("--images", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--output-downscaled", type=Path, required=True)
    parser.add_argument("--model", type=Path, default=Path("sam2.1_t.pt"))
    parser.add_argument("--downscale", type=int, default=2)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    names = [line.strip() for line in args.manifest.read_text(encoding="utf-8").splitlines() if line.strip()]
    model = SAM(str(args.model))
    preview_rows: list[Image.Image] = []
    areas: list[float] = []

    for index, name in enumerate(names):
        source = args.images / name
        image = Image.open(source).convert("RGB")
        width, height = image.size
        full_path = (args.output / name).with_suffix(".png")
        small_path = (args.output_downscaled / name).with_suffix(".png")
        if full_path.exists() and small_path.exists() and not args.force:
            mask = Image.open(full_path).convert("L")
            mask_array = np.asarray(mask) > 0
        else:
            box = [0.25 * width, 0.06 * height, 0.75 * width, 0.96 * height]
            result = model(
                str(source),
                bboxes=box,
                device=0,
                retina_masks=True,
                verbose=False,
            )[0]
            if result.masks is None or len(result.masks.data) == 0:
                result = model(
                    str(source),
                    bboxes=box,
                    points=[0.5 * width, 0.48 * height],
                    labels=[1],
                    device=0,
                    retina_masks=True,
                    verbose=False,
                )[0]
            if result.masks is None or len(result.masks.data) == 0:
                raise RuntimeError(f"No mask returned for {name}")
            mask_array = result.masks.data[0].cpu().numpy() > 0.5
            mask = Image.fromarray(mask_array.astype(np.uint8) * 255)
            full_path.parent.mkdir(parents=True, exist_ok=True)
            small_path.parent.mkdir(parents=True, exist_ok=True)
            mask.save(full_path, optimize=True)
            mask.resize((width // args.downscale, height // args.downscale), Image.Resampling.NEAREST).save(
                small_path, optimize=True
            )
        areas.append(float(mask_array.mean()))

        if index % max(1, len(names) // 12) == 0:
            thumb = image.copy()
            thumb.thumbnail((480, 320), Image.Resampling.LANCZOS)
            thumb_mask = mask.resize(thumb.size, Image.Resampling.NEAREST)
            pixels = np.asarray(thumb).copy()
            keep = np.asarray(thumb_mask) > 0
            pixels[~keep] = (35, 35, 35)
            tile = Image.fromarray(pixels)
            ImageDraw.Draw(tile).text((8, 8), name, fill="white", font=ImageFont.load_default(size=18))
            preview_rows.append(tile)

        print(f"[{index + 1:03d}/{len(names):03d}] {name}: {areas[-1]:.3f}", flush=True)

    columns = 4
    tile_width = max(tile.width for tile in preview_rows)
    tile_height = max(tile.height for tile in preview_rows)
    rows = (len(preview_rows) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * tile_width, rows * tile_height), "#202020")
    for index, tile in enumerate(preview_rows):
        sheet.paste(tile, ((index % columns) * tile_width, (index // columns) * tile_height))
    preview_path = args.output.parent / "mask_review.jpg"
    sheet.save(preview_path, quality=92)

    summary = {
        "images": len(names),
        "model": str(args.model),
        "box_ratios_xyxy": [0.25, 0.06, 0.75, 0.96],
        "mean_mask_fraction": float(np.mean(areas)),
        "min_mask_fraction": float(np.min(areas)),
        "max_mask_fraction": float(np.max(areas)),
    }
    (args.output.parent / "mask_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
