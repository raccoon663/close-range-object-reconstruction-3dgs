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

The repository excludes the virtual environment and checkpoint. Recreate the environment with versions listed above and review the scripts before adapting them to a different CUDA or operating-system setup.
