# Model card

## Artifact

`model/dragon_object_half_clean.ply` is a 3D Gaussian Splat reconstruction of a small glossy figurine. It contains 19,118 vertices with 62 finite scalar attributes per vertex and occupies 4,742,856 bytes (4.52 MiB). These properties were independently checked during the repository audit; they do not establish geometric validity.

SHA-256: `273d8504b1b807c1efa4d2784576ab2bc549a41c557f2939d4f5221a1c03f15b`.
The PLY header identifies Nerfstudio 1.1.5 and z as the vertical axis. It contains
SH color, opacity, scale and rotation fields; it does not contain camera poses
or the transform back to the original COLMAP reconstruction.

## Source data

The capture contains 268 Sony α7C II photographs taken in three handheld orbit rings. Twenty-one frames were reserved before camera recovery; 247 training frames were registered. The repository includes 18 reduced sample frames, while the 6.14 GB full-resolution source set is kept outside Git history.

## Processing

- PyCOLMAP feature extraction, exhaustive matching, and an additional historical pose-extension stage whose exact procedure is unavailable
- box-prompted SAM2 foreground masks
- Nerfstudio Splatfacto for 30,000 iterations at 3504 × 2336
- projection of Gaussian centers into all registered masks
- multi-view foreground support threshold of 0.80

The reported 73,653 pre-cleanup and 19,165 supported Gaussians are historical
counts, not independently regenerated results. The cause of the 47-entry
difference before final export cannot be established without intermediate logs.
The new cleanup implementation defaults to three valid views and has not been
used to replace this artifact. See [cleanup provenance](docs/cleanup.md).

## Evaluation and reproducibility

The 21 reserved capture frames are unposed and have no quantitative evaluation.
Nerfstudio's interval evaluation selects every 14th view within the 247 posed
source-selected images; “247 training frames” describes source selection, not
247 optimization views. No PSNR, SSIM, LPIPS or geometric accuracy is claimed.
The original filename lists, connected camera model, masks, parser transform,
checkpoint and raw Gaussian export are absent. No geometric ground truth exists.

## Intended use

Close-range reconstruction experiments, visual inspection in a Gaussian Splat viewer, and comparison of capture or cleanup strategies.

## Limitations

The representation is not a watertight mesh and has no metric scale. Transparent and glossy parts contain view-dependent artifacts. Occluded surfaces, thin edges, and mask boundaries may be incomplete or soft.

Silhouette filtering checks centers, not covariance or visibility. Mask errors,
occlusion ambiguity and threshold sensitivity remain. Finite-order SH supports
view-dependent color but cannot guarantee consistent sharp specular/transparency
effects. The viewer uses SuperSplat/PlayCanvas under its retained MIT license.
