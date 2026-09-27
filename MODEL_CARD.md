# Model card

## Artifact

`model/dragon_object_half_clean.ply` is a 3D Gaussian Splat reconstruction of a small glossy figurine. It contains 19,118 valid Gaussians and occupies 4.52 MB.

## Source data

The capture contains 268 Sony α7C II photographs taken in three handheld orbit rings. Twenty-one frames were reserved before camera recovery; 247 training frames were registered. The repository includes 18 reduced sample frames, while the 6.14 GB full-resolution source set is kept outside Git history.

## Processing

- PyCOLMAP feature extraction, exhaustive matching, registration, and bundle adjustment
- box-prompted SAM2 foreground masks
- Nerfstudio Splatfacto for 30,000 iterations at 3504 × 2336
- projection of Gaussian centers into all registered masks
- multi-view foreground support threshold of 0.80

## Intended use

Close-range reconstruction experiments, visual inspection in a Gaussian Splat viewer, and comparison of capture or cleanup strategies.

## Limitations

The representation is not a watertight mesh and has no metric scale. Transparent and glossy parts contain view-dependent artifacts. Occluded surfaces, thin edges, and mask boundaries may be incomplete or soft.
