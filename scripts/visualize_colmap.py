#!/usr/bin/env python3
"""Render a compact diagnostic figure from a COLMAP text model."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from colmap_text import read_views


def qvec_to_rot(q):
    w, x, y, z = q
    return np.array([
        [1 - 2 * y * y - 2 * z * z, 2 * x * y - 2 * z * w, 2 * x * z + 2 * y * w],
        [2 * x * y + 2 * z * w, 1 - 2 * x * x - 2 * z * z, 2 * y * z - 2 * x * w],
        [2 * x * z - 2 * y * w, 2 * y * z + 2 * x * w, 1 - 2 * x * x - 2 * y * y],
    ])


def read_cameras(path):
    return [(-(v.rotation.T @ v.translation), v.name.split("/")[0]) for v in read_views(path)]


def read_points(path):
    xyz, rgb = [], []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        fields = line.split()
        xyz.append([float(x) for x in fields[1:4]])
        rgb.append([int(x) / 255 for x in fields[4:7]])
    return np.asarray(xyz).reshape(-1, 3), np.asarray(rgb).reshape(-1, 3)


def equal_axes(ax, values):
    center = (values.min(axis=0) + values.max(axis=0)) / 2
    radius = max(np.max(values.max(axis=0) - values.min(axis=0)) / 2, 1e-6)
    for setter, c in zip((ax.set_xlim, ax.set_ylim, ax.set_zlim), center):
        setter(c - radius, c + radius)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("model", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    cameras = read_cameras(args.model / "images.txt")
    points, colors = read_points(args.model / "points3D.txt")
    centers = np.array([c for c, _ in cameras])
    groups = [g for _, g in cameras]
    group_colors = {"lower": "#2f6fed", "middle": "#21a366", "upper": "#e95f26"}

    fig = plt.figure(figsize=(13, 10), constrained_layout=True)
    views = [(25, 35, "Perspective"), (90, -90, "Top"), (0, 0, "Front"), (0, 90, "Side")]
    combined = centers
    for index, (elev, azim, title) in enumerate(views, 1):
        ax = fig.add_subplot(2, 2, index, projection="3d")
        sample = slice(None, None, max(1, len(points) // 15000))
        ax.scatter(points[sample, 0], points[sample, 1], points[sample, 2], c=colors[sample], s=0.45, alpha=0.45)
        for group in sorted(set(groups)):
            mask = np.array([g == group for g in groups])
            ax.scatter(centers[mask, 0], centers[mask, 1], centers[mask, 2], s=12, label=group, c=group_colors.get(group))
        equal_axes(ax, combined)
        ax.view_init(elev=elev, azim=azim)
        ax.set_title(title)
        ax.set_axis_off()
        if index == 1:
            ax.legend(loc="upper right")
    fig.suptitle(f"COLMAP sparse reconstruction: {len(cameras)} cameras, {len(points):,} points")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=180)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
