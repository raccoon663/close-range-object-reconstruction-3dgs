#!/usr/bin/env python3
"""Prepare a Nerfstudio COLMAP directory (new utility, not historical code)."""
import argparse
from pathlib import Path
import shutil
import numpy as np
from PIL import Image
from colmap_text import read_model
from image_list import read_image_list


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--images", required=True, type=Path)
    parser.add_argument("--image-list", required=True, type=Path)
    parser.add_argument("--colmap-model", required=True, type=Path, help="Selected, connected TEXT model")
    parser.add_argument("--masks", required=True, type=Path, help="Full-resolution masks")
    parser.add_argument("--output", required=True, type=Path, help="New dataset directory")
    parser.add_argument("--downscale", type=int, default=2)
    args = parser.parse_args()
    if args.downscale < 2 or args.output.exists():
        parser.error("Use downscale >= 2 and a new output directory")
    output = args.output.resolve()
    for source in (args.images, args.masks, args.colmap_model):
        source = source.resolve()
        if source == output or source.is_relative_to(output) or output.is_relative_to(source):
            parser.error("Output and source directories must not overlap")
    names = read_image_list(args.image_list, args.images)
    cameras, views = read_model(args.colmap_model)
    if set(names) != {v.name for v in views}:
        parser.error("Selected model must exactly match the image list; inspect fragmented reconstructions first")
    model_files = [args.colmap_model / n for n in ("cameras.txt", "images.txt", "points3D.txt")]
    if not all(p.is_file() for p in model_files):
        parser.error("Text cameras, images and points3D files are required")
    for view in views:
        camera = cameras[view.camera_id]
        with Image.open(args.images / view.name) as im, Image.open(args.masks / Path(view.name).with_suffix(".png")) as mask:
            if im.size != (camera.width, camera.height) or mask.size != im.size:
                raise ValueError(f"Camera/image/mask dimensions disagree: {view.name}")
            if min(im.size) < args.downscale:
                raise ValueError(f"Downscale exceeds image dimensions: {view.name}")
            if mask.mode not in {"1", "L"} or not np.isin(np.asarray(mask.convert("L")), [0, 255]).all():
                raise ValueError(f"Mask must be binary grayscale: {view.name}")
    for name in names:
        for folder, root, rel, method in (
            ("images", args.images, Path(name), Image.Resampling.LANCZOS),
            ("masks", args.masks, Path(name).with_suffix(".png"), Image.Resampling.NEAREST),
        ):
            target = args.output / folder / rel
            small = args.output / f"{folder}_{args.downscale}" / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            small.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(root / rel, target)
            with Image.open(root / rel) as im:
                size = tuple(v // args.downscale for v in im.size)
                im.resize(size, method).save(small)
    model_target = args.output / "colmap" / "sparse" / "0"
    model_target.mkdir(parents=True)
    for path in model_files:
        shutil.copy2(path, model_target / path.name)
    print(f"Prepared {len(names)} registered views in {args.output}")


if __name__ == "__main__":
    main()
