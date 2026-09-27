# Compute environment

## Hardware

| Component | Configuration |
|---|---|
| CPU | AMD Ryzen 9 9950X3D, 16 cores |
| System memory | 48 GB |
| GPU | NVIDIA GeForce RTX 5080 |
| GPU memory | 16,303 MiB |
| Operating system | Windows 11 25H2, build 26200 |

The GPU driver used for the final inspection was 616.56. Hardware values were read from the training workstation after the run; no host name, device identifier, or serial number is included.

## Software

| Package | Version |
|---|---|
| Python | 3.12.14 |
| PyCOLMAP | 3.13.0 |
| Nerfstudio | 1.1.5 |
| PyTorch | 2.7.1+cu128 |
| CUDA runtime used by PyTorch | 12.8 |
| torchvision | 0.22.1+cu128 |
| gsplat | 1.5.3+pt27cu128 |
| imageio-ffmpeg | 0.6.0 |

PyCOLMAP feature extraction and matching ran on the CPU because a compatible system COLMAP/CUDA toolchain was not available in this Windows environment. Splatfacto training ran on the RTX 5080.

## Final training run

- input resolution: 3504 × 2336 (`downscale-factor 2`)
- maximum iterations: 30,000
- background color: white
- mask directory supplied to the COLMAP data parser
- evaluation mode: interval, every 14th posed image
- checkpoint: step 29,999

The repository excludes the virtual environment and checkpoint. This table is a
historical environment record, not a tested lockfile. The original wrapper also
referenced an absent `compat/` directory; any local compatibility patches are
unknown. The audit did not retrain or validate this complete GPU stack.

## Practical installation scopes

For CPU preparation, cleanup and plots, use Python 3.10+ (the recorded training
Python was 3.12.14) in a dedicated environment:

```text
python -m venv .venv
python -m pip install -r requirements.txt
python -m pip install pytest
```

Activate `.venv` before the pip commands (`.venv/Scripts/Activate.ps1` on
PowerShell or `source .venv/bin/activate` on POSIX). NumPy, Pillow, matplotlib
and the newly introduced `plyfile` are declared in `requirements.txt`; their
historical versions were not recorded. `pytest` is test-only.

For a new GPU experiment, first install a matched PyTorch/torchvision pair for
your platform. The recorded CUDA 12.8 pair can be requested using the
[official previous-version instructions](https://pytorch.org/get-started/previous-versions/):

```text
python -m pip install torch==2.7.1 torchvision==0.22.1 --index-url https://download.pytorch.org/whl/cu128
python -m pip install -r requirements-pipeline.txt
```

These are installation starting points, not a guarantee that all transitive
dependencies resolve on every platform. `requirements-pipeline.txt` records
PyCOLMAP 3.13.0 and Nerfstudio 1.1.5, and declares Ultralytics with an unpinned
historical version. Inspect the resolved environment: installing Nerfstudio may
change gsplat or other packages. The recorded gsplat build was
`1.5.3+pt27cu128`; an ordinary unqualified pip install is not evidence of that
same wheel/build. Follow [gsplat installation](https://docs.gsplat.studio/main/INSTALL.html)
for a wheel compatible with your PyTorch/CUDA/OS, or a source build with the
required CUDA/compiler toolchain. Save `pip freeze`, CUDA/driver and wheel
provenance for the new run; do not relabel that environment as the historical one.

`ns-train` and `ns-export` come from Nerfstudio. A system COLMAP executable is
optional for text conversion; baseline reconstruction uses the Python PyCOLMAP
package. The preparation script precomputes downscaled images/masks, avoiding
an implicit image-resizing command during training setup.

## SAM2 and optional media tools

Download Ultralytics-compatible `sam2.1_t.pt` using the weights link in the
[official SAM2 documentation](https://docs.ultralytics.com/models/sam-2/), store it
under `weights/`, and pass `--model weights/sam2.1_t.pt`. Weights are external and
ignored by Git. Their historical checksum and the Ultralytics version are not
available; record both in a new experiment. Upstream code/weight licensing applies
separately from this repository's license.

`imageio-ffmpeg==0.6.0` is recorded historically, but no committed script imports
imageio or regenerates the orbit video. `imageio`'s version and the video-rendering
procedure are unknown; they are not mandatory dependencies of current scripts.
FFmpeg/media rendering is optional, and the existing MP4 is a historical artifact.
