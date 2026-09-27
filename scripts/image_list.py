"""Shared, ordered input-list validation (public sample CSV is not a training list)."""
from pathlib import Path, PurePosixPath


def relative_name(name: str) -> str:
    name = name.replace("\\", "/")
    p = PurePosixPath(name)
    if not name or p.is_absolute() or ".." in p.parts or ":" in name:
        raise ValueError(f"Expected a safe relative image name, got {name!r}")
    return p.as_posix()


def read_image_list(path: Path, images: Path) -> list[str]:
    if path.suffix.lower() == ".csv":
        raise ValueError("Use train_images.txt: one relative filename per line; sample manifest.csv is metadata.")
    names = [relative_name(s.strip()) for s in path.read_text(encoding="utf-8-sig").splitlines() if s.strip()]
    if not names or len(set(names)) != len(names):
        raise ValueError("Image list must be nonempty and contain no duplicate names")
    root = images.resolve()
    for name in names:
        source = (root / name).resolve()
        if not source.is_relative_to(root) or not source.is_file():
            raise ValueError(f"Missing image or path outside image root: {name}")
    masks = [str(Path(n).with_suffix(".png")).casefold() for n in names]
    if len(set(masks)) != len(masks):
        raise ValueError("Image names collide after conversion to mask .png names")
    return names
