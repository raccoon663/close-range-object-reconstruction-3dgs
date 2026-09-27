# Reproduction workflow and evidence boundaries

The published PLY and viewer can be inspected immediately. Exact retraining and
historical cleanup cannot be reproduced from this public checkout alone.
The commands below are a **new, explicit workflow**, not a recovered shell
transcript. They preserve recorded training settings where available. No full
training run was performed during this audit.

## 1. Inputs and environment

Install the appropriate dependencies from [environment.md](environment.md).
Obtain your source images and create `train_images.txt`, one relative filename
per line (for example `lower/DSC05268.JPG`). Preserve order and subdirectories.
The exact historical 247-name list and 21-name reserved list are not committed;
the ring counts alone do not reconstruct that selection. Record your own lists.

`sample_data/manifest.csv` describes 18 reduced public samples; it is **not** a
training list. Its SHA-256 column hashes private originals, not these reduced
JPEGs. The samples are for inspection and do not reproduce the full capture.

## 2. Automated baseline camera recovery

Commands are shown on one line for both PowerShell and POSIX shells. Replace
the illustrative paths with actual inputs.

```text
python scripts/run_colmap.py --images raw_data/images --image-list train_images.txt --workspace outputs/colmap --matcher exhaustive
```

Use a fresh workspace for each experiment. `--fresh` explicitly deletes the
selected generated workspace; do not point it at valuable data. The baseline
uses CPU features/matching and one shared SIMPLE_RADIAL camera, an approximation
given the recorded 49–51 mm focal-length variation. Results are not guaranteed
bit-identical across platforms or parallel mapping runs.

Inspect `outputs/colmap/reconstruction_summary.json` and the text models under
`outputs/colmap/sparse_text/`. Do not union image counts across models and call
that a connected reconstruction. Select one model and verify its image names.

**Historical gap:** the 247-image automated experiment reports 245 registered
across four models (largest 150). The final 247-camera/21,035-point model followed
an additional “pose extension” stage. Its commands, correspondences, saved model
and intermediate states are unavailable. Whether it used manual interventions
cannot be established. `run_colmap.py` does not implement it. There is no
fabricated pose-extension script here. If your baseline fragments, resolving
registration is a separate prerequisite before continuing with all 247 views.

Optional diagnostic for a selected text model:

```text
python scripts/visualize_colmap.py outputs/colmap/sparse_text/0 outputs/cameras.png
```

Model `0` is an example, not an assertion that it is the largest/final model.

## 3. Foreground masks

Obtain Ultralytics-compatible `sam2.1_t.pt` separately and place it under
`weights/`. The script requires an existing file and accepts `--device cpu` or
a GPU index. Review all masks, especially thin and transparent parts; the fixed
box prompt was chosen for this capture and is not a general object detector.

```text
python scripts/generate_object_masks.py --images raw_data/images --image-list train_images.txt --output data/masks --output-downscaled data/masks_2 --downscale 2 --model weights/sam2.1_t.pt --device 0
```

Inspect `data/mask_review.jpg` and `data/mask_summary.json`. Cached masks are
reused unless `--force`; regenerate when inputs, weights or prompts change.

## 4. Prepare the COLMAP-parser layout

The new utility copies the selected text model and full images/masks, then
resizes images with Lanczos and masks with nearest-neighbor sampling. Camera
dimensions must match the originals. It requires the model and list to contain
exactly the same image names, so fragmented output cannot silently pass as full
registration. The exact historical image-conversion/resampling procedure was
not recorded; these new resizes are not claimed pixel-identical.

```text
python scripts/prepare_nerfstudio_data.py --images raw_data/images --image-list train_images.txt --colmap-model outputs/colmap/sparse_text/0 --masks data/masks --output data/nerfstudio/dragon --downscale 2
```

The result contains `images/`, `images_2/`, `masks/`, `masks_2/` and
`colmap/sparse/0/`. The Nerfstudio **colmap** parser reads that layout directly;
`ns-process-data` and a guessed `transforms.json` conversion are not required.
Keep the original distorted masks for cleanup even if training internally
undistorts images. Do not apply a second downscale to intrinsics manually.

## 5. Train only when producing a new experiment

Activate the Nerfstudio environment. The existing PowerShell wrapper now accepts
`-Data`, `-Output` and `-NsTrain` and resolves `ns-train` from the environment:

```powershell
./scripts/train_object_half.ps1 -Data data/nerfstudio/dragon -Output outputs/checkpoints/object-half
```

Equivalent direct invocation:

```text
ns-train splatfacto --output-dir outputs/checkpoints/object-half --experiment-name dragon-object-half --max-num-iterations 30000 --vis tensorboard --steps-per-save 5000 --steps-per-eval-all-images 5000 --pipeline.model.background-color white colmap --data data/nerfstudio/dragon --downscale-factor 2 --masks-path masks --eval-mode interval --eval-interval 14
```

Archive the actual configuration, package lock, checkpoint, image split and
`dataparser_transforms.json` together. The old wrapper referenced an absent
`compat/` directory; its contents and any historical platform patches could not
be recovered. The replacement removes that unresolved dependency, but this does
not prove the documented Windows/CUDA training stack installs without adaptation.

The 247 posed source-selected images are further divided by Nerfstudio's interval
split. They are not all optimization views. The 21 unposed reserved capture
frames are separate and have no independent quantitative results.

## 6. Export and clean without retraining

If an existing compatible checkpoint/config is available, export it directly.
`RUN_CONFIG` and `RUN_TRANSFORM` below denote actual files from that run; replace
them. The historical checkpoint is not committed.

```text
ns-export gaussian-splat --load-config RUN_CONFIG --output-dir outputs/export
python scripts/clean_gaussians_multiview.py --input-ply outputs/export/splat.ply --colmap-model data/nerfstudio/dragon/colmap/sparse/0 --masks data/masks_2 --dataparser-transform RUN_TRANSFORM --threshold 0.80 --min-valid-views 3 --output-ply outputs/diagnostics/clean_reimplementation.ply --diagnostics outputs/diagnostics/support.npz
```

The exporter may already discard nonfinite or very low-opacity entries, so
post-export counts need not equal checkpoint Gaussian counts. Cleanup preserves
PLY coordinates/attributes. See [cleanup.md](cleanup.md) for the coordinate
contract, supported distortion models and heuristic limitations. New output
names are mandatory; never overwrite `model/dragon_object_half_clean.ply` to
claim historical reproduction. No threshold ablation has been performed.

## 7. View and optionally deploy

```text
python -m http.server 8000
```

From the repository root, open `http://localhost:8000/viewer/`. This serves the
published model. To inspect a diagnostic without changing the default, open
`http://localhost:8000/viewer/?content=../outputs/diagnostics/clean_reimplementation.ply`.
Hosting requires the `viewer/`, `model/` and referenced `assets/` paths to retain
their relative layout. The existing GitHub Pages link is a published historical
deployment; no deployment change is needed for this audit.

## Lightweight verification

```text
python -m pip install -r requirements.txt pytest
python -m compileall -q scripts tests
python -m pytest -q
```

Tests use synthetic cameras, masks and PLYs. They do not require the private data,
SAM2 weights, PyCOLMAP, GPU training or historical checkpoints.
