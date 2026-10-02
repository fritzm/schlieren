# Vendor CAD models

Manufacturer-supplied 3D models of purchased parts, loaded by `schlieren.vendor_cad` for viewer assemblies
and clearance checks. Like `docs/reference/`, these are manufacturer specifications, not measured values or
committed project dimensions.

Name files `<Brand>-<part>.step` following the `docs/reference/` convention (`/` in part numbers becomes
`-`). Keep the vendor file unmodified; place it in project coordinates in code, not by re-exporting.

| File | Vendor file | Source | Native frame |
|---|---|---|---|
| `Thorlabs-TR50-M.step` | 0331-E0W.step (SolidWorks 2014, AP214, mm) | thorlabs.com TR50/M, "Step" | Axis +Y, base at origin; includes M4 setscrew stud |
| `Thorlabs-SMR1-M.step` | 0665-E0W.step (SolidWorks 2014, AP214, mm) | thorlabs.com SMR1/M, "Step" | Optical axis +Z, faces at z=-0.40 in and 0, post seat at y=-0.87 in |
| `Thorlabs-SM1CP2M.step` | 13217-E0W.step (SolidWorks 2016, AP214, inch) | thorlabs.com SM1CP2M, "Step" | Axis +Y, knurled back face at y=0, seat 0.110 in, thread end 0.210 in |
| `Thorlabs-SM1V05.step` | 0591-E0W.step (AP214, inch) | thorlabs.com SM1V05, "Step" | Axis +X, 1.030 in overall; three solids (sleeve, lock ring, retaining ring); dimension reference only |
| `Thorlabs-SM1RC-M.step` | 13349-E0W.step (SolidWorks 2016, AP214, m) | thorlabs.com SM1RC/M, "Step" | Axis +Z through origin, faces at z=0 and 0.40 in, post seat at y=-0.87 in; two solids (split ring, M4 lock screw at +Y) |
| `Thorlabs-FAS100.step` | 0634-E0W.step (SolidWorks 2007, AP214, mm) | thorlabs.com FAS100, "Step" | Axis +X through (y, z) = (1.583, -2.103) mm, knob at -X, ball-tip apex at x=22.013 mm; four solids |
| `Thorlabs-SM1L15.step` | TTN048857-E0W.step (SolidWorks 2016, AP214, m) | thorlabs.com SM1L15, "Step" | Axis +X through (y, z) = (27.854, 33.711) mm, off origin; two solids (tube, retaining ring); not yet loaded |
| `Thorlabs-SM1L03.step` | 0823-E0W.step (SolidWorks 2014, AP214, inch) | thorlabs.com SM1L03, "Step" | Axis +X, x from -0.45 in to 0; two solids (tube, retaining ring); not yet loaded |
| `Thorlabs-SM1D12.step` | 0077-E0W.step (SolidWorks 2022, AP214, mm) | thorlabs.com SM1D12, "Step" | Axis +Z, z from 0 to 0.42 in; 16 solids (iris leaves, housing, lever); not yet loaded |
| `Thorlabs-SM1CP1.step` | 0756-E0W.step (SolidWorks 2022, AP214, mm) | thorlabs.com SM1CP1, "Step" | Axis +Z through (x, y) = (14.107, 16.294) mm, off origin, z from 19.595 to 23.786 mm; one solid; not yet loaded |
| `Thorlabs-SM1EC2.step` | CCO000389.STEP (SolidWorks 2016, AP203, mm) | thorlabs.com SM1EC2, "Step" | Axis +Z through origin; surface model only (no solids); not yet loaded |
| `Thorlabs-ACL2520U-A.step` | CTN002256-E0W.step (SolidWorks 2014, AP203, mm) | thorlabs.com ACL2520U-A, "Step" | Axis +Y through origin, y from -6.0 to 6.0 mm; one solid; not yet loaded |
| `Alpha-CN40-40B.step` | CN40-40B (2009, AP203 config control design, mm) | alphanovatech.com CN40-40B | Axis +Y through origin, base mounting face at y=0, 3.0 mm base, pins to y=40 mm; one solid |

Thorlabs CAD downloads are listed per product through the site's GraphQL API at
`https://www.thorlabs.com/graphql`, e.g. `{ products(storeId: "Thorlabs-Website", filter: "name:\"SM1RC/M\"")
{ items { name assets { group optiUrl } } } }`; the `Step` asset is the one CadQuery can read (the `CAD PDF`
asset is the drawing filed in `docs/reference/`). SolidWorks (`.sldprt`) and eDrawing files are not usable here.

Project policy: where a vendor model is available, use its exact values in preference to rounded dimensions
from the drawing. Thorlabs SM1 parts are inch-primary, so their models are exact while the drawings' mm values
are rounded (e.g. SMR1/M 0.400 in = 10.16 mm, drawn as 10.2 mm). The reverse also occurs: the metric TR50/M
model is rounded to inches (1.969 in, 0.499 in), so its exact metric nominals (50 mm, Ø12.7 mm) are used.
