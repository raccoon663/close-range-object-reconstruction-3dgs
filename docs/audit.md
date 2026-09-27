# Repository audit

## Scope and evidence

Audited all scripts and documentation, README, model card, Git attributes/ignore
rules, sample CSV and images, PLY metadata/payload, viewer bootstrap/settings/license,
and all eight published commits reachable from `main` at `ef6eba9`. A scoped
search of available local project folders did not recover additional cleanup,
pose-extension or run state. This was not an exhaustive search of every disk or
private external archive.

## Changes made and important technical fixes

| Finding | Resolution |
|---|---|
| Described cleanup had no implementation | Added clearly labeled reimplementation with diagnostics and synthetic tests |
| PLY/COLMAP coordinate equality was unspecified | Required explicit identity, affine mapping or inverse saved Nerfstudio COLMAP-parser transform |
| Support alone can retain poorly observed points | Added configurable minimum valid views, default 3; original artifact unchanged |
| Missing projection details | Documented positive depth, distortion, bounds, mask resizing, path matching and attribute preservation |
| 247/247 wording conflated baseline and extension | Separated 245-across-four-model baseline from unrecovered final pose extension |
| Preparation/export steps absent | Added validated data-layout utility and explicit new-run workflow with external export command |
| Sample CSV confused with filename list | Added `--image-list`, retained legacy alias, rejected CSV with actionable message |
| SAM hard-coded GPU and unchecked inputs | Configurable device, weights/file/size/binary-mask checks and empty-list rejection |
| Visualization skipped empty COLMAP observations | Shared parser retains alternating pose/observation records correctly |
| Training wrapper assumed local venv and missing compat | Configurable executable/data/output, input checks and native exit-code propagation |
| Dependency coverage incomplete | Lightweight/pipeline requirements plus platform-specific GPU/weights guidance; no false lockfile |
| Lambertian wording and evaluation terminology imprecise | SH-aware limitations and explicit unposed reserved-capture distinction |
| Viewer dominated repository identity | Precise vendored attributes and provenance; original engine/license preserved |

## Files added

- `scripts/clean_gaussians_multiview.py`
- `scripts/colmap_text.py`
- `scripts/image_list.py`
- `scripts/prepare_nerfstudio_data.py`
- `tests/test_reconstruction.py`
- `requirements.txt`, `requirements-pipeline.txt`
- `docs/cleanup.md`, `docs/reproduction.md`, `docs/audit.md`
- `viewer/README.md`

## Files modified

`README.md`, `MODEL_CARD.md`, `.gitignore`, `.gitattributes`, all four original
scripts, and `docs/dataset_summary.md`, `docs/environment.md`,
`docs/final_report.md`. The sample manifest, sample images, published model,
render/video assets, viewer engine/configuration and licenses are preserved.

## Remaining limitations

The full 6.14 GB capture is private. Exact source-selection lists, connected
camera model, pose-extension steps/state, SAM2 masks/weight checksum, checkpoint,
raw Gaussian export and dataparser transform are absent. The historical
73,653 → 19,165 → 19,118 counts cannot be regenerated, and the 47-entry difference
cannot be attributed conclusively. Historical image resampling, video generation,
viewer bundle revision and any local compatibility patches remain unknown.
External SAM2 weights and a compatible GPU environment are still required for a
new full experiment. No retraining or modification of the published model occurred.

## Verification performed

- 18 synthetic pytest cases passed: supported intrinsics/distortion, camera
  rotation/translation, parser transform inversion including scale/translation,
  empty COLMAP observation lines, scaled masks, bounds/depth, nonfinite points,
  threshold/minimum-view rejection, PLY property/encoding preservation,
  overwrite refusal, bad inputs and prepared dataset layout.
- Python compilation and `--help` for all five executable Python CLIs passed;
  the two shared Python modules were compiled. PowerShell wrapper parsed without
  syntax errors. No GPU invocation was made.
- Local Markdown link and HTML image targets, public sample dimensions, viewer
  model/poster targets and JSON settings were checked. External reference URLs
  were consulted for conventions/CLI behavior; no blanket external-link or
  browser rendering claim is made.
- Published PLY inspected: 19,118 vertices, 62 finite scalar fields per vertex,
  4,742,856 bytes; SHA-256 unchanged at
  `273d8504b1b807c1efa4d2784576ab2bc549a41c557f2939d4f5221a1c03f15b`.
- Existing binary assets and viewer/license files compared to the audit base;
  repository diff checked for whitespace errors, unintended large files,
  environments/checkpoints and personal absolute paths.

These checks establish lightweight code/packaging behavior. They do not validate
real-data projection alignment, SAM inference, PyCOLMAP reconstruction, CUDA
training, exact historical counts, perceptual quality or geometric accuracy.
The new requirements are not a fully solved GPU environment lockfile.

## Recommended future experiments

Recover/archive original lists, model state, masks, parser transform and export
logs first. Then independently pose reserved capture frames and define a strict
evaluation protocol excluding them from optimization and cleanup. Report actual
PSNR/SSIM/LPIPS and foreground-only metrics with split details, if computed.
Run genuine support-threshold and minimum-view sweeps, and compare visibility-
and covariance-aware filtering. None of these experiments was performed here.

## Recommended GitHub topics

`3d-gaussian-splatting`, `gaussian-splatting`, `3d-reconstruction`,
`computer-vision`, `photogrammetry`, `colmap`, `nerfstudio`, `sam2`,
`novel-view-synthesis`. Repository topics were not changed by this audit.
