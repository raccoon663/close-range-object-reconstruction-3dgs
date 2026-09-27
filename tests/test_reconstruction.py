"""Synthetic geometry/IO regression tests; not validation of historical results."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import numpy as np
from PIL import Image
from plyfile import PlyData, PlyElement
import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
from colmap_text import Camera, View, project, read_model, read_views, qvec_to_rot
from clean_gaussians_multiview import coordinate_transform, support_counts
from image_list import read_image_list


def scene(tmp_path, count=3):
    model = tmp_path / "model"
    masks = tmp_path / "masks"
    model.mkdir()
    masks.mkdir()
    (model / "cameras.txt").write_text("1 PINHOLE 8 8 4 4 4 4\n")
    (model / "images.txt").write_text("".join(f"{i+1} 1 0 0 0 0 0 0 1 ring/{i}.jpg\n\n" for i in range(count)))
    (model / "points3D.txt").write_text("# empty synthetic sparse point set\n")
    (masks / "ring").mkdir()
    for i in range(count):
        a = np.zeros((4, 4), dtype=np.uint8)
        a[2, 2] = 255
        Image.fromarray(a).save(masks / "ring" / f"{i}.png")
    return model, masks


def test_empty_observation_lines_and_scaled_masks(tmp_path):
    model, masks = scene(tmp_path)
    cameras, views = read_model(model)
    assert len(views) == 3
    xyz = np.array([[0, 0, 1], [0, 0, -1], [1, 0, 1], [-1.01, 0, 1], [-.5, 0, 1], [np.nan, 0, 1], [0, 0, 0]])
    valid, fg, _ = support_counts(xyz, cameras, views, masks, chunk_size=2)
    np.testing.assert_array_equal(valid, [3, 0, 0, 0, 3, 0, 0])
    np.testing.assert_array_equal(fg, [3, 0, 0, 0, 0, 0, 0])


@pytest.mark.parametrize("model,params,expected", [
    ("SIMPLE_PINHOLE", [10, 5, 5], [10, 5]),
    ("PINHOLE", [10, 20, 5, 5], [10, 5]),
    ("SIMPLE_RADIAL", [10, 5, 5, 1], [11.25, 5]),
    ("RADIAL", [10, 5, 5, 1, 2], [11.875, 5]),
    ("OPENCV", [10, 10, 5, 5, 0, 0, .1, .2], [11.5, 5.25]),
])
def test_intrinsics_distortion(model, params, expected):
    np.testing.assert_allclose(project(Camera(model, 20, 20, np.array(params)), np.array([[.5, 0, 1]]))[0], expected)


def test_dataparser_inverse_includes_translation_and_scale(tmp_path):
    matrix = np.eye(4)
    matrix[:3, :3] = qvec_to_rot([np.sqrt(.5), 0, 0, np.sqrt(.5)])
    matrix[:3, 3] = [1, 2, 3]
    path = tmp_path / "transform.json"
    path.write_text(json.dumps({"transform": matrix[:3].tolist(), "scale": 2}))
    args = argparse.Namespace(ply_in_colmap_world=False, ply_to_colmap=None, dataparser_transform=path)
    inverse = coordinate_transform(args)
    p = np.array([3., 4., 5., 1.])
    normalized = matrix @ p
    normalized[:3] *= 2
    np.testing.assert_allclose(inverse @ normalized, p)


def test_camera_rotation_translation(tmp_path):
    model, masks = scene(tmp_path, 1)
    cameras, views = read_model(model)
    rotation = qvec_to_rot([np.sqrt(.5), 0, np.sqrt(.5), 0])
    view = View(views[0].name, 1, rotation, np.array([0, 0, 2]))
    # World point (-1,0,0) becomes (0,0,3) in this camera.
    valid, fg, _ = support_counts(np.array([[-1., 0, 0]]), cameras, [view], masks)
    assert valid[0] == fg[0] == 1


def test_mask_mismatch_and_missing(tmp_path):
    model, masks = scene(tmp_path, 1)
    cameras, views = read_model(model)
    path = masks / "ring/0.png"
    Image.new("L", (4, 2), 255).save(path)
    with pytest.raises(ValueError, match="aspect"):
        support_counts(np.array([[0, 0, 1]]), cameras, views, masks)
    path.unlink()
    with pytest.raises(FileNotFoundError):
        support_counts(np.array([[0, 0, 1]]), cameras, views, masks)


def test_cli_preserves_attributes_and_refuses_overwrite(tmp_path):
    model, masks = scene(tmp_path)
    # One view rejects the second center: support 2/3, below .80.
    m = np.zeros((4, 4), dtype=np.uint8)
    m[2, 2] = 255
    for i in (0, 1):
        m[2, 1] = 255
        Image.fromarray(m).save(masks / f"ring/{i}.png")
    data = np.zeros(4, dtype=[("x", "f4"), ("y", "f4"), ("z", "f4"), ("opacity", "f4"), ("f_rest_0", "f4"), ("rot_0", "f4"), ("label", "u1")])
    data["z"] = [1, 1, -1, 1]
    data["x"][1] = -.5
    data["opacity"] = [7, 8, 9, np.nan]
    data["f_rest_0"] = 1.25
    data["label"] = [3, 4, 5, 6]
    source = tmp_path / "input.ply"
    PlyData([PlyElement.describe(data, "vertex")], comments=["test provenance"], byte_order=">").write(source)
    before = source.read_bytes()
    output = tmp_path / "filtered.ply"
    cmd = [sys.executable, str(SCRIPTS / "clean_gaussians_multiview.py"), "--input-ply", str(source), "--colmap-model", str(model), "--masks", str(masks), "--output-ply", str(output), "--ply-in-colmap-world", "--diagnostics", str(tmp_path / "counts.npz")]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    ply = PlyData.read(output)
    np.testing.assert_array_equal(ply["vertex"].data, data[:1])
    assert ply.comments == ["test provenance"] and ply.byte_order == ">"
    assert source.read_bytes() == before
    diag = np.load(tmp_path / "counts.npz")
    assert diag["foreground_views"].tolist() == [3, 2, 0, 3]
    assert subprocess.run(cmd, capture_output=True).returncode != 0
    # Too few valid views must fail without writing an empty artifact.
    cmd = cmd[:cmd.index("--diagnostics")] + ["--min-valid-views", "4"]
    cmd[cmd.index("--output-ply")+1] = str(tmp_path / "empty.ply")
    assert subprocess.run(cmd, capture_output=True).returncode != 0
    assert not (tmp_path / "empty.ply").exists()


@pytest.mark.parametrize("contents", ["", "../outside.jpg\n", "a.jpg\na.jpg\n", "C:/private.jpg\n"])
def test_image_list_rejects_invalid(tmp_path, contents):
    path = tmp_path / "train_images.txt"
    path.write_text(contents)
    with pytest.raises(ValueError):
        read_image_list(path, tmp_path)


def test_csv_not_training_list(tmp_path):
    path = tmp_path / "manifest.csv"
    path.write_text("source_filename,sample_filename\na.jpg,b.jpg\n")
    with pytest.raises(ValueError, match="metadata"):
        read_image_list(path, tmp_path)


def test_unsupported_camera_and_empty_model(tmp_path):
    model, _ = scene(tmp_path, 1)
    (model / "cameras.txt").write_text("1 OPENCV_FISHEYE 8 8 4 4 4 4 0 0 0 0\n")
    with pytest.raises(ValueError, match="Unsupported"):
        read_model(model)
    (model / "images.txt").write_text("# no poses\n")
    with pytest.raises(ValueError, match="empty"):
        read_views(model / "images.txt")


def test_explicit_transform_and_singular_rejection(tmp_path):
    p = tmp_path / "matrix.json"
    transform = np.eye(4)
    transform[:3, 3] = [1, 2, 3]
    p.write_text(json.dumps(transform.tolist()))
    args = argparse.Namespace(ply_in_colmap_world=False, ply_to_colmap=p, dataparser_transform=None)
    np.testing.assert_array_equal(coordinate_transform(args), transform)
    transform[0, 0] = 0
    p.write_text(json.dumps(transform.tolist()))
    with pytest.raises(ValueError, match="singular"):
        coordinate_transform(args)


def test_prepare_dataset(tmp_path):
    model, masks = scene(tmp_path, 1)
    images = tmp_path / "images"
    (images / "ring").mkdir(parents=True)
    Image.new("RGB", (8, 8)).save(images / "ring/0.jpg")
    Image.new("L", (8, 8), 255).save(masks / "ring/0.png")
    image_list = tmp_path / "train_images.txt"
    image_list.write_text("ring/0.jpg\n")
    output = tmp_path / "prepared"
    result = subprocess.run([sys.executable, str(SCRIPTS / "prepare_nerfstudio_data.py"), "--images", str(images), "--image-list", str(image_list), "--masks", str(masks), "--colmap-model", str(model), "--output", str(output)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert Image.open(output / "images_2/ring/0.jpg").size == (4, 4)
    assert Image.open(output / "masks_2/ring/0.png").size == (4, 4)
    assert (output / "colmap/sparse/0/images.txt").read_bytes() == (model / "images.txt").read_bytes()
