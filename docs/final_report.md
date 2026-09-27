# Reconstruction notes

## Camera recovery

The 247 training photographs cover lower, middle, and upper orbit rings. Sequential matching produced several disconnected models. Exhaustive matching improved within-ring connectivity, after which image registration and bundle adjustment produced one model containing all 247 inputs and 21,035 sparse points.

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

| Representation | Gaussians |
|---|---:|
| half-resolution object model before cleanup | 73,653 |
| retained by the 0.80 support rule | 19,165 |
| valid entries written to the PLY | 19,118 |

This rule removes most of the table and room while preserving the base, tail, wings, and head across the orbit.

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
