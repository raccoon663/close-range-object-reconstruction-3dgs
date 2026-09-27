# Reconstruction notes

## Camera recovery

The 247 source-selected photographs cover lower, middle, and upper orbit rings.
Historical notes report fragmented sequential/exhaustive reconstruction and a
later connected 247-camera, 21,035-point model. The table calls this additional
stage “pose extension”. Its exact commands, registration strategy, manual
interventions (if any) and intermediate states could not be recovered from the
published history or the scoped local project-folder search. Registration and
bundle adjustment are named in the original notes, but their sequence and inputs
are not specified. `run_colmap.py` implements the automated baseline only and
must not be presented as independently reproducing the final connected model.

A simple image-count reduction was not successful:

| Input views | Registered across models | Largest model | Models |
|---:|---:|---:|---:|
| 50 | 6 | 6 | 1 |
| 100 | 43 | 19 | 3 |
| 247 | 245 | 150 | 4 |
| 247 + pose extension | 247 | 247 | 1 |

For this handheld capture, adjacent-view overlap and bridge views between elevation rings mattered more than the nominal number of photographs.

## Foreground isolation

Box-prompted SAM2 masks isolated the figurine in each training view. Supplying those masks during Splatfacto training reduced background supervision but did not remove every background-initialized Gaussian. A radial crop was also unreliable because the base and table occupied nearby coordinates.

The final cleanup projects every Gaussian center into the registered cameras. For views in which the point projects inside the image, the procedure records whether the projected pixel lies inside the foreground mask. A point is retained when at least 80% of its valid projections agree with the foreground.

This is the historical method description, not a recovered implementation.
The new [cleanup script](../scripts/clean_gaussians_multiview.py) adds a configurable
minimum valid-view count (default 3), positive-depth checks, explicit coordinate
transforms, lens distortion and scaled-mask lookup. Its synthetic tests do not
establish agreement with the historical counts below. See [cleanup.md](cleanup.md).

| Representation | Gaussians |
|---|---:|
| half-resolution object model before cleanup | 73,653 |
| retained by the 0.80 support rule | 19,165 |
| valid entries written to the PLY | 19,118 |

This rule removes most of the table and room while preserving the base, tail, wings, and head across the orbit.

That assessment refers to the published visual result. Only the final PLY's
19,118 finite vertices can currently be verified from committed data. The
intermediate 73,653 and 19,165 counts remain historical reports, and the 47-entry
export difference lacks an attributable log. No new cleanup/ablation was run on
the historical model. A center-only silhouette test cannot resolve depth
occlusion, Gaussian extent, false background support or threshold sensitivity.

## Evaluation split

There are 268 source images, 247 selected for camera recovery/training preparation,
and 21 unposed reserved capture frames. The latter were not quantitatively
evaluated. Nerfstudio's interval split uses every 14th posed image from the 247
and is distinct from the source reservation. No independent novel-view metrics
or PSNR/SSIM/LPIPS values are available in the repository. Cleanup using evaluation
masks would also make those views unsuitable for an untouched evaluation.

## Visual assessment

The cleaned representation supports free-viewpoint rotation and preserves the main shape and color structure. Remaining errors concentrate on the transparent gold accessory, glossy highlights, thin edges, and poorly observed surfaces. These areas appear soft or contain a small number of floating splats.

The result should be interpreted as an object-centric radiance representation. It is not a metrically scaled, watertight mesh, and the experiment does not report geometric accuracy against a reference scan.

## Recommended capture changes

- use a matte neutral background with clear foreground separation
- keep lighting diffuse and fixed
- lock exposure, white balance, and focus
- use a lower ISO and stable support where possible
- add deliberate bridge views between elevation rings
- include more coverage of the underside and occluded thin structures
