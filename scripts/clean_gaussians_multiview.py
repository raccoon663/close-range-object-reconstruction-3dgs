#!/usr/bin/env python3
"""Reimplemented center-projection silhouette filter; not the historical cleanup code."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image
from colmap_text import read_model, project


def affine(value):
    matrix = np.asarray(value, dtype=float)
    if matrix.shape == (3, 4):
        matrix = np.vstack((matrix, [0, 0, 0, 1]))
    if matrix.shape != (4, 4) or not np.isfinite(matrix).all() or not np.allclose(matrix[3], [0, 0, 0, 1]):
        raise ValueError("Expected a finite affine 3x4 or 4x4 matrix")
    if abs(np.linalg.det(matrix[:3, :3])) < 1e-12:
        raise ValueError("Coordinate transform is singular")
    return matrix


def coordinate_transform(args):
    if args.ply_in_colmap_world:
        return np.eye(4)
    if args.ply_to_colmap:
        return affine(json.loads(args.ply_to_colmap.read_text(encoding="utf-8")))
    data = json.loads(args.dataparser_transform.read_text(encoding="utf-8"))
    scale = float(data["scale"])
    if not np.isfinite(scale) or scale <= 0:
        raise ValueError("Dataparser scale must be finite and positive")
    forward = affine(data["transform"])
    forward[:3, :] *= scale
    return np.linalg.inv(forward)


def support_counts(xyz, cameras, views, masks, chunk_size=100000):
    valid = np.zeros(len(xyz), dtype=np.uint32)
    foreground = np.zeros(len(xyz), dtype=np.uint32)
    mask_metadata = []
    used_paths = set()
    root = masks.resolve()
    for view in views:
        camera = cameras[view.camera_id]
        path = (masks / Path(view.name).with_suffix(".png")).resolve()
        if not path.is_relative_to(root) or path in used_paths:
            raise ValueError(f"Unsafe or colliding mask path for {view.name}")
        used_paths.add(path)
        with Image.open(path) as image:
            if image.mode not in {"1", "L"}:
                raise ValueError(f"Mask must be binary/grayscale, not {image.mode}: {view.name}")
            mask = np.asarray(image.convert("L"))
        if not np.isin(mask, [0, 255]).all():
            raise ValueError(f"Mask must contain only 0 and 255: {view.name}")
        mh, mw = mask.shape
        # Permit integer-rounded uniform resizing, but not crops or aspect changes.
        if abs(mw / camera.width - mh / camera.height) > max(1/camera.width, 1/camera.height):
            raise ValueError(f"Mask aspect ratio differs from camera: {view.name}")
        mask_metadata.append({"image": view.name, "size": [mw, mh], "sha256": sha256(path)})
        for start in range(0, len(xyz), chunk_size):
            stop = min(start + chunk_size, len(xyz))
            camera_xyz = xyz[start:stop] @ view.rotation.T + view.translation
            uv = project(camera, camera_xyz)
            ok = (np.isfinite(camera_xyz).all(axis=1) & (camera_xyz[:, 2] > 0)
                  & np.isfinite(uv).all(axis=1) & (uv[:, 0] >= 0) & (uv[:, 0] < camera.width)
                  & (uv[:, 1] >= 0) & (uv[:, 1] < camera.height))
            ids = np.flatnonzero(ok)
            # Pixel cells use floor and bounds before indexing (never wrap negatives).
            mx = np.minimum(np.floor(uv[ids, 0] * mw / camera.width).astype(int), mw - 1)
            my = np.minimum(np.floor(uv[ids, 1] * mh / camera.height).astype(int), mh - 1)
            valid[start + ids] += 1
            foreground[start + ids] += (mask[my, mx] > 0).astype(np.uint32)
    return valid, foreground, mask_metadata


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-ply", type=Path, required=True)
    parser.add_argument("--colmap-model", type=Path, required=True, help="COLMAP text model directory")
    parser.add_argument("--masks", type=Path, required=True, help="Original distorted image masks; relative names preserved, suffix .png")
    parser.add_argument("--output-ply", type=Path, required=True, help="New file; existing files are never overwritten")
    parser.add_argument("--threshold", type=float, default=0.80)
    parser.add_argument("--min-valid-views", type=int, default=3)
    parser.add_argument("--chunk-size", type=int, default=100000)
    parser.add_argument("--diagnostics", type=Path, help="New .npz file with counts/support/keep in original vertex order")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--ply-in-colmap-world", action="store_true", help="Explicit assertion of identical world coordinates")
    group.add_argument("--ply-to-colmap", type=Path, help="JSON affine matrix: COLMAP_world = matrix @ PLY_homogeneous")
    group.add_argument("--dataparser-transform", type=Path, help="Nerfstudio COLMAP dataparser_transforms.json from the same run (transform, scale)")
    args = parser.parse_args()
    if not 0 <= args.threshold <= 1 or args.min_valid_views < 1 or args.chunk_size < 1:
        parser.error("threshold must be in [0,1]; minimum views and chunk size must be positive")
    output = args.output_ply
    report_path = output.with_suffix(".summary.json")
    destinations = [output, report_path] + ([args.diagnostics] if args.diagnostics else [])
    if len({p.resolve() for p in destinations}) != len(destinations) or any(p.exists() for p in destinations):
        parser.error("Output destinations must be distinct new files")
    if args.diagnostics and args.diagnostics.suffix != ".npz":
        parser.error("--diagnostics must end in .npz")
    from plyfile import PlyData
    ply = PlyData.read(args.input_ply)
    # Mesh indices would become invalid after filtering; reject instead of silently corrupting.
    if [e.name for e in ply.elements] != ["vertex"]:
        raise ValueError("Only vertex-only Gaussian PLY is supported")
    vertices = ply["vertex"].data
    if not len(vertices) or not {"x", "y", "z"}.issubset(vertices.dtype.names):
        raise ValueError("Input PLY must contain nonempty x/y/z vertices")
    finite = np.ones(len(vertices), dtype=bool)
    for name in vertices.dtype.names:
        if vertices[name].dtype.kind not in "fiu":
            raise ValueError("Only scalar numeric PLY properties are supported")
        finite &= np.isfinite(vertices[name])
    xyz = np.column_stack([vertices[n] for n in ("x", "y", "z")]).astype(float)
    matrix = coordinate_transform(args)
    with np.errstate(invalid="ignore", over="ignore"):
        xyz = xyz @ matrix[:3, :3].T + matrix[:3, 3]
    cameras, views = read_model(args.colmap_model)
    valid, foreground, mask_metadata = support_counts(xyz, cameras, views, args.masks, args.chunk_size)
    support = np.divide(foreground, valid, out=np.zeros(len(valid), dtype=float), where=valid > 0)
    keep = finite & (valid >= args.min_valid_views) & (support >= args.threshold)
    if not keep.any():
        raise ValueError("No Gaussians retained; check alignment, masks, threshold, and minimum views. No output written.")
    report = {
        "implementation": "reimplementation; not verified against historical counts",
        "input_sha256": sha256(args.input_ply), "input_vertices": len(vertices),
        "nonfinite_vertices": int((~finite).sum()), "zero_valid_views": int((valid == 0).sum()),
        "retained": int(keep.sum()), "threshold": args.threshold, "min_valid_views": args.min_valid_views,
        "registered_views": len(views), "ply_to_colmap": matrix.tolist(),
        "camera_files_sha256": {n: sha256(args.colmap_model / n) for n in ("cameras.txt", "images.txt")},
        "masks": mask_metadata,
        "note": "Center-only silhouette heuristic; no depth/occlusion test. Output coordinates/attributes unchanged.",
    }
    # Subset the structured array: preserve property order, types, SH, opacity, scales, rotations, comments and encoding.
    ply["vertex"].data = vertices[keep].copy()
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("xb") as stream:
        ply.write(stream)
    report["output_sha256"] = sha256(output)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if args.diagnostics:
        args.diagnostics.parent.mkdir(parents=True, exist_ok=True)
        with args.diagnostics.open("xb") as stream:
            np.savez_compressed(stream, valid_views=valid, foreground_views=foreground, support=support, keep=keep)
    print(f"Retained {keep.sum()} / {len(vertices)}; wrote {output} and {report_path}")


if __name__ == "__main__":
    main()
