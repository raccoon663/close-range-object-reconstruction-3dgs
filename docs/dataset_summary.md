# Capture summary

Every source photograph was decoded and inspected without modification.

| Elevation ring | Images | Size |
|---|---:|---:|
| lower | 88 | 2.12 GB |
| middle | 75 | 1.54 GB |
| upper | 105 | 2.48 GB |
| **Total** | **268** | **6.14 GB** |

## EXIF summary

- image dimensions: 7008 × 4672 for all frames
- camera: Sony ILCE-7CM2 (α7C II)
- lens: TAMRON 25-200mm F2.8-5.6 A075 E
- focal length: 49 mm (193), 50 mm (47), 51 mm (28)
- aperture: f/8 (230), f/4 (28), f/6.3 (10)
- ISO: 2500 (3), 3200 (25), 6400 (29), 8000 (44), 10000 (43), 12800 (124)
- exposure: 1/80 (11), 1/60 (140), 1/50 (67), 1/40 (31), 1/30 (19)
- GPS records: none

High sensitivity and relatively slow shutter speeds explain part of the visible noise and softness. The 49–51 mm focal-length variation is small, so the reconstruction baseline used one shared `SIMPLE_RADIAL` camera.

## Split and registration

The deterministic source split reserved views around each orbit.

| Ring | Training | Source-level holdout |
|---|---:|---:|
| lower | 81 | 7 |
| middle | 69 | 6 |
| upper | 97 | 8 |
| **Total** | **247** | **21** |

All 247 training images were registered after exhaustive matching and pose extension. The resulting sparse model contains 21,035 points.

The 21 source-level holdout images do not have recovered poses and are not the same as Nerfstudio's interval evaluation views. No metric from the interval split is presented as a strict source-level holdout result.

## Public sample

`sample_data/` contains six evenly spaced reduced frames from each elevation ring. They are 1752 pixels on the long edge, use JPEG quality 88, and contain no EXIF metadata. `sample_data/manifest.csv` records each source filename and source SHA-256 hash so that the sample can be matched to the original capture.
