# Capture summary

The historical capture audit reports that every source photograph was decoded
and inspected without modification. The private originals are not available in
this checkout for repeating the EXIF and source-hash checks below.

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

The historical notes describe a deterministic source reservation around each
orbit, but the original filename lists and selection rule are not committed.

| Ring | Selected for pose recovery/training preparation | Reserved capture frames |
|---|---:|---:|
| lower | 81 | 7 |
| middle | 69 | 6 |
| upper | 97 | 8 |
| **Total** | **247** | **21** |

The final historical model reports 247 registered images after exhaustive
matching and an additional unrecovered pose-extension stage, with 21,035 sparse
points. The automated baseline alone does not establish this result.

The 21 reserved capture images do not have recovered poses and were not
quantitatively evaluated. Nerfstudio's interval evaluation views are selected
within the 247 posed images, reducing the actual optimization subset. No interval
metric is presented as an independent reserved-capture result.

## Public sample

`sample_data/` contains six evenly spaced reduced frames from each elevation ring. They are 1752 pixels on the long edge, use JPEG quality 88, and contain no EXIF metadata. `sample_data/manifest.csv` records each source filename and source SHA-256 hash so that the sample can be matched to the original capture.
