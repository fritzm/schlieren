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

Thorlabs CAD downloads are listed per product through the site's GraphQL API (`products(...) { assets
{ group optiUrl } }` at `https://www.thorlabs.com/graphql`, store `Thorlabs-Website`); the `Step` asset is
the one CadQuery can read. SolidWorks (`.sldprt`) and eDrawing files are not usable here.

Project policy: where a vendor model is available, use its exact values in preference to rounded dimensions
from the drawing. Thorlabs SM1 parts are inch-primary, so their models are exact while the drawings' mm values
are rounded (e.g. SMR1/M 0.400 in = 10.16 mm, drawn as 10.2 mm). The reverse also occurs: the metric TR50/M
model is rounded to inches (1.969 in, 0.499 in), so its exact metric nominals (50 mm, Ø12.7 mm) are used.
