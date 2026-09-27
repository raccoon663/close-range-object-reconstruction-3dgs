from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from image_list import read_image_list


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate object masks with a SAM 2 box prompt.")
    parser.add_argument("--images", type=Path, required=True)
    parser.add_argument("--image-list", "--manifest", dest="image_list", type=Path, required=True,
                        help="train_images.txt: one relative filename per line; legacy --manifest remains accepted")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--output-downscaled", type=Path, required=True)
    parser.add_argument("--model", type=Path, default=Path("sam2.1_t.pt"))
    parser.add_argument("--downscale", type=int, default=2)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--device", default="0", help="Ultralytics device, e.g. 0 or cpu")
    args = parser.parse_args()

    names = read_image_list(args.image_list, args.images)
    if args.downscale < 1:
        parser.error("--downscale must be positive")
    roots = [p.resolve() for p in (args.images, args.output, args.output_downscaled)]
    if any(a == b or a.is_relative_to(b) or b.is_relative_to(a)
           for i, a in enumerate(roots) for b in roots[i+1:]):
        parser.error("Image and mask directories must not overlap")
    if not args.model.is_file():
        parser.error("SAM2 weights not found; obtain the documented weights and pass --model")
    from ultralytics import SAM
    model = SAM(str(args.model))
    preview_rows: list[Image.Image] = []
    areas: list[float] = []

    for index, name in enumerate(names):
        source = args.images / name
        image = Image.open(source).convert("RGB")
        width, height = image.size
        if min(width, height) < args.downscale:
            raise ValueError(f"Downscale exceeds image dimensions: {name}")
        full_path = (args.output / name).with_suffix(".png")
        small_path = (args.output_downscaled / name).with_suffix(".png")
        if full_path.exists() and small_path.exists() and not args.force:
            mask = Image.open(full_path).convert("L")
            with Image.open(small_path) as small:
                if mask.size != image.size or small.size != (width // args.downscale, height // args.downscale):
                    raise ValueError(f"Cached mask size mismatch for {name}; regenerate with --force")
            mask_array = np.asarray(mask) > 0
        else:
            box = [0.25 * width, 0.06 * height, 0.75 * width, 0.96 * height]
            result = model(
                str(source),
                bboxes=box,
                device=args.device,
                retina_masks=True,
                verbose=False,
            )[0]
            if result.masks is None or len(result.masks.data) == 0:
                result = model(
                    str(source),
                    bboxes=box,
                    points=[0.5 * width, 0.48 * height],
                    labels=[1],
                    device=args.device,
                    retina_masks=True,
                    verbose=False,
                )[0]
            if result.masks is None or len(result.masks.data) == 0:
                raise RuntimeError(f"No mask returned for {name}")
            mask_array = result.masks.data[0].cpu().numpy() > 0.5
            if mask_array.shape != (height, width):
                raise ValueError(f"SAM mask dimensions differ from source image: {name}")
            mask = Image.fromarray(mask_array.astype(np.uint8) * 255)
            full_path.parent.mkdir(parents=True, exist_ok=True)
            small_path.parent.mkdir(parents=True, exist_ok=True)
            mask.save(full_path, optimize=True)
            mask.resize((width // args.downscale, height // args.downscale), Image.Resampling.NEAREST).save(
                small_path, optimize=True
            )
        if not np.isin(np.asarray(mask), [0, 255]).all() or not mask_array.any():
            raise ValueError(f"Empty or nonbinary mask for {name}; review the prompt or regenerate cached masks")
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
        "model": args.model.name,
        "device": args.device,
        "box_ratios_xyxy": [0.25, 0.06, 0.75, 0.96],
        "mean_mask_fraction": float(np.mean(areas)),
        "min_mask_fraction": float(np.min(areas)),
        "max_mask_fraction": float(np.max(areas)),
    }
    (args.output.parent / "mask_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
