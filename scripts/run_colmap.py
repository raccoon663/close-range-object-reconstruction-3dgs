#!/usr/bin/env python3
"""Run a reproducible CPU COLMAP baseline through PyCOLMAP."""

from __future__ import annotations

import argparse
import json
import shutil
import time
from pathlib import Path

import pycolmap


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--images", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--max-image-size", type=int, default=2000)
    parser.add_argument("--matcher", choices=["sequential", "exhaustive"], default="sequential")
    parser.add_argument("--fresh", action="store_true")
    args = parser.parse_args()

    database = args.workspace / "database.db"
    sparse = args.workspace / "sparse"
    if args.fresh and args.workspace.exists():
        shutil.rmtree(args.workspace)
    sparse.mkdir(parents=True, exist_ok=True)
    image_names = [line.strip() for line in args.manifest.read_text(encoding="utf-8").splitlines() if line.strip()]
    started = time.time()

    extraction = pycolmap.FeatureExtractionOptions()
    extraction.max_image_size = args.max_image_size
    extraction.use_gpu = False
    extraction.sift.max_num_features = 8192
    print(f"Extracting features for {len(image_names)} images at max {args.max_image_size}px", flush=True)
    pycolmap.extract_features(
        database_path=str(database),
        image_path=str(args.images),
        image_names=image_names,
        camera_mode=pycolmap.CameraMode.SINGLE,
        camera_model="SIMPLE_RADIAL",
        extraction_options=extraction,
        device=pycolmap.Device.cpu,
    )

    matching = pycolmap.FeatureMatchingOptions()
    matching.use_gpu = False
    if args.matcher == "sequential":
        pairing = pycolmap.SequentialPairingOptions()
        pairing.overlap = 20
        pairing.quadratic_overlap = True
        pairing.loop_detection = False
        print("Matching sequential neighbors (overlap=20, quadratic overlap enabled)", flush=True)
        pycolmap.match_sequential(str(database), matching_options=matching, pairing_options=pairing, device=pycolmap.Device.cpu)
    else:
        print("Matching all image pairs", flush=True)
        pycolmap.match_exhaustive(str(database), matching_options=matching, device=pycolmap.Device.cpu)

    print("Running incremental mapping", flush=True)
    options = pycolmap.IncrementalPipelineOptions()
    options.multiple_models = True
    options.min_model_size = 10
    options.ba_refine_principal_point = False
    models = pycolmap.incremental_mapping(str(database), str(args.images), str(sparse), options=options)
    summaries = []
    for model_id, reconstruction in models.items():
        model_dir = sparse / str(model_id)
        text_dir = args.workspace / "sparse_text" / str(model_id)
        text_dir.mkdir(parents=True, exist_ok=True)
        reconstruction.write_text(text_dir)
        reconstruction.export_PLY(args.workspace / f"sparse_{model_id}.ply")
        summaries.append({
            "model_id": model_id,
            "registered_images": reconstruction.num_reg_images(),
            "total_images": reconstruction.num_images(),
            "sparse_points": reconstruction.num_points3D(),
            "mean_observations_per_image": reconstruction.compute_mean_observations_per_reg_image(),
            "binary_model": str(model_dir),
            "text_model": str(text_dir),
        })
    result = {
        "pycolmap": pycolmap.__version__,
        "matcher": args.matcher,
        "max_image_size": args.max_image_size,
        "training_images": len(image_names),
        "elapsed_seconds": round(time.time() - started, 1),
        "models": summaries,
    }
    (args.workspace / "reconstruction_summary.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
