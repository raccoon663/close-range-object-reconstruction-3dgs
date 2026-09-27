"""Read COLMAP text cameras and alternating pose/observation image records."""
from dataclasses import dataclass
from pathlib import Path
import numpy as np
from image_list import relative_name


@dataclass
class Camera:
    model: str
    width: int
    height: int
    params: np.ndarray


@dataclass
class View:
    name: str
    camera_id: int
    rotation: np.ndarray
    translation: np.ndarray


def qvec_to_rot(q):
    q = np.asarray(q, dtype=float)
    norm = np.linalg.norm(q)
    if not np.isfinite(norm) or norm < 1e-12:
        raise ValueError("Invalid COLMAP quaternion")
    w, x, y, z = q / norm
    return np.array([
        [1-2*y*y-2*z*z, 2*x*y-2*z*w, 2*x*z+2*y*w],
        [2*x*y+2*z*w, 1-2*x*x-2*z*z, 2*y*z-2*x*w],
        [2*x*z-2*y*w, 2*y*z+2*x*w, 1-2*x*x-2*y*y],
    ])


def read_views(path: Path) -> list[View]:
    views = []
    # Empty observation lines are significant: never strip them before pairing.
    lines = iter(path.read_text(encoding="utf-8").splitlines())
    for line in lines:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        fields = line.split(maxsplit=9)
        if len(fields) != 10:
            raise ValueError("Malformed COLMAP image pose record")
        rotation = qvec_to_rot([float(x) for x in fields[1:5]])
        translation = np.array([float(x) for x in fields[5:8]])
        if not np.isfinite(translation).all():
            raise ValueError("Nonfinite camera translation")
        views.append(View(relative_name(fields[9]), int(fields[8]), rotation, translation))
        observations = next(lines, None)
        if observations is None or observations.lstrip().startswith("#") or len(observations.split()) % 3:
            raise ValueError("Missing or malformed COLMAP observations line")
    if not views or len({v.name for v in views}) != len(views):
        raise ValueError("Camera model is empty or has duplicate image names")
    return views


def read_model(directory: Path):
    cameras = {}
    counts = {"SIMPLE_PINHOLE": 3, "PINHOLE": 4, "SIMPLE_RADIAL": 4, "RADIAL": 5, "OPENCV": 8}
    for line in (directory / "cameras.txt").read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        ident, model, w, h, *params = line.split()
        values = np.array(params, dtype=float)
        if model not in counts:
            raise ValueError(f"Unsupported camera model {model}; convert/undistort explicitly first")
        if len(values) != counts[model] or not np.isfinite(values).all() or min(int(w), int(h)) <= 0:
            raise ValueError("Invalid camera dimensions or parameters")
        if values[0] <= 0 or (model in {"PINHOLE", "OPENCV"} and values[1] <= 0):
            raise ValueError("Focal lengths must be positive")
        if int(ident) in cameras:
            raise ValueError("Duplicate camera ID")
        cameras[int(ident)] = Camera(model, int(w), int(h), values)
    views = read_views(directory / "images.txt")
    if any(v.camera_id not in cameras for v in views):
        raise ValueError("Image references missing camera")
    return cameras, views


def project(camera: Camera, xyz: np.ndarray):
    """COLMAP/OpenCV: +x right, +y down, +z forward; retain distortion."""
    with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
        x, y = xyz[:, 0] / xyz[:, 2], xyz[:, 1] / xyz[:, 2]
        p = camera.params
        if camera.model in {"PINHOLE", "OPENCV"}:
            fx, fy, cx, cy = p[:4]
        else:
            fx, cx, cy = p[:3]
            fy = fx
        r2 = x*x + y*y
        if camera.model in {"SIMPLE_RADIAL", "RADIAL"}:
            radial = 1 + p[3]*r2
            if camera.model == "RADIAL":
                radial += p[4]*r2*r2
            x, y = x*radial, y*radial
        elif camera.model == "OPENCV":
            k1, k2, p1, p2 = p[4:]
            radial = 1 + k1*r2 + k2*r2*r2
            x, y = (x*radial + 2*p1*x*y + p2*(r2+2*x*x),
                    y*radial + p1*(r2+2*y*y) + 2*p2*x*y)
        return np.column_stack((fx*x+cx, fy*y+cy))
