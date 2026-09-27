# Multi-view Gaussian cleanup

## Provenance

`scripts/clean_gaussians_multiview.py` is a new implementation of the described
method. No original cleanup code was found in the eight commits reachable from
the audited `main` (`ef6eba9`), or in the scoped local project-folder search.
This does not establish that no original exists elsewhere. The raw Gaussian
export, masks, cameras, checkpoint and saved dataparser transform are absent.
Consequently the historical 73,653 → 19,165 → 19,118 sequence has **not** been
regenerated. The 47-entry difference is unexplained by the available run records;
do not assign it to a particular validity/opacity filter without the logs.

## Coordinates and projection

The implementation accepts a COLMAP **text** model. For binary models, export text
with PyCOLMAP `Reconstruction(path).write_text(output_path)` or COLMAP's model
converter. Supported cameras are SIMPLE_PINHOLE, PINHOLE, SIMPLE_RADIAL, RADIAL
and OPENCV; others fail explicitly. Use masks corresponding to these cameras'
original, distorted images. Never mix undistorted images/masks with the original
distorted camera model.

The caller must select one coordinate contract:

- `--ply-in-colmap-world`: an explicit assertion that the PLY is already in the
  COLMAP world frame. It is generally incorrect for a default Splatfacto export.
- `--ply-to-colmap matrix.json`: a 3×4 or 4×4 affine matrix mapping PLY centers to
  COLMAP world coordinates, using homogeneous **column vectors**.
- `--dataparser-transform dataparser_transforms.json`: the saved `transform` and
  `scale` from the **same Nerfstudio COLMAP-parser run**. The forward relation is
  `x_model = scale * (T[:3,:3] @ x_colmap + T[:3,3])`; cleanup inverts the combined
  affine transform, including the scaled translation. Do not substitute a raw
  `transforms.json`, viewer transform, or metadata from another parser/run.

For each transformed center, `x_camera = R @ x_colmap + t`, using COLMAP's
scalar-first quaternion and world-to-camera translation. COLMAP camera axes are
+x right, +y down, +z forward. Only strictly positive depth is eligible. Divide
by z, apply the camera's radial/tangential distortion, then apply intrinsics.
The implementation retains projections with finite coordinates and
`0 <= u < width`, `0 <= v < height`.

For a mask of size `(mask_width, mask_height)`, lookup uses
`floor(u * mask_width / width)` and `floor(v * mask_height / height)`.
This defines the pixel-cell convention explicitly. Masks must be binary 0/255,
uniformly resized full-frame images (integer rounding allowed), not crops.
Matching preserves the complete relative image path and replaces its suffix
with `.png`; there is no ambiguous basename fallback. Missing masks fail.

Nerfstudio converts OpenCV camera axes to OpenGL (+y up, -z forward), then
orients, centers and scales the world. Its COLMAP parser includes the initial
world-axis conversion in the saved dataparser transform. Inverting that saved
transform avoids guessing sign flips or assuming equal worlds. The PLY output
stays in its original coordinate frame; transformed centers are used only for
classification. Spherical harmonics, log scales, rotations, opacity, property
types/order, encoding and comments are preserved for retained rows.

Sources: [COLMAP pose format](https://colmap.github.io/format.html),
[Nerfstudio 1.1.5 COLMAP parser](https://github.com/nerfstudio-project/nerfstudio/blob/v1.1.5/nerfstudio/data/dataparsers/colmap_dataparser.py),
[Nerfstudio Gaussian exporter](https://github.com/nerfstudio-project/nerfstudio/blob/v1.1.5/nerfstudio/scripts/exporter.py).

## Rule, outputs and limits

`support = foreground_views / valid_views`. Keep a row only when all its scalar
attributes are finite, support is at least `--threshold` (default 0.80), and
valid views are at least `--min-valid-views` (default 3). Zero valid views always
fail. Three views is a configurable guard against isolated support, not an
empirically optimized setting or a recovered historical parameter.

The new output must not exist. A `.summary.json` sidecar records input/output
hashes, camera/mask hashes, transform, thresholds and counts. Optional `.npz`
diagnostics store counts, support and keep decisions in input vertex order.
Only vertex-only scalar-property PLY is supported; meshes and list properties
are rejected to avoid broken indices. No additional opacity threshold is applied.
No-retained-point runs fail without writing a PLY.

This is a **center-projection silhouette heuristic**, not visibility-aware
volumetric segmentation. It ignores covariance/extent, transmittance and depth
occlusion. An occluded background point may project inside a foreground mask;
a large foreground Gaussian may have its center outside a silhouette. Mask
errors and the support/minimum-view thresholds affect thin structures and
sparsely observed regions. Validate alignment visually before trusting a real
run. Synthetic tests establish projection/IO behavior, not historical alignment
or reconstruction quality. Evaluation images used for cleanup are part of the
selection process and cannot then serve as untouched test views.
