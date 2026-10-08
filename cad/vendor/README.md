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
| `Thorlabs-SM1V05.step` | 0591-E0W.step (AP214, inch) | thorlabs.com SM1V05, "Step" | Axis +X, 1.030 in overall; three solids (sleeve, lock ring, retaining ring), placed separately |
| `Thorlabs-SM1RC-M.step` | 13349-E0W.step (SolidWorks 2016, AP214, m) | thorlabs.com SM1RC/M, "Step" | Axis +Z through origin, faces at z=0 and 0.40 in, post seat at y=-0.87 in; two solids (split ring, M4 lock screw at +Y) |
| `Thorlabs-FAS100.step` | 0634-E0W.step (SolidWorks 2007, AP214, mm) | thorlabs.com FAS100, "Step" | Axis +X through (y, z) = (1.583, -2.103) mm, knob at -X, ball-tip apex at x=22.013 mm; four solids |
| `Thorlabs-SM1L15.step` | TTN048857-E0W.step (SolidWorks 2016, AP214, m) | thorlabs.com SM1L15, "Step" | Axis +X through (y, z) = (27.854, 33.711) mm, off origin; two solids (tube, retaining ring); not yet loaded |
| `Thorlabs-SM1L03.step` | 0823-E0W.step (SolidWorks 2014, AP214, inch) | thorlabs.com SM1L03, "Step" | Axis +X, x from -0.45 in to 0; two solids (tube, retaining ring); only the tube is loaded |
| `Thorlabs-SM1D12.step` | 0077-E0W.step (SolidWorks 2022, AP214, mm) | thorlabs.com SM1D12, "Step" | Axis +Z, z from 0 to 0.42 in; external-thread shoulder at z=0.08 in; 16 solids (iris leaves, housing, lever at +Y) |
| `Thorlabs-SM1CP1.step` | 0756-E0W.step (SolidWorks 2022, AP214, mm) | thorlabs.com SM1CP1, "Step" | Axis +Z through (x, y) = (14.107, 16.294) mm, off origin, z from 19.595 to 23.786 mm; one solid; not yet loaded |
| `Thorlabs-SM1EC2.step` | CCO000389.STEP (SolidWorks 2016, AP203, mm) | thorlabs.com SM1EC2, "Step" | Axis +Z through origin; surface model only (no solids); not yet loaded |
| `Thorlabs-ACL2520U-A.step` | CTN002256-E0W.step (SolidWorks 2014, AP203, mm) | thorlabs.com ACL2520U-A, "Step" | Axis +Y through origin, convex vertex at y=-6.0 mm, plano face at y=6.0 mm; one solid |
| `Alpha-CN40-40B.step` | CN40-40B (2009, AP203 config control design, mm) | alphanovatech.com CN40-40B | Axis +Y through origin, base mounting face at y=0, 3.0 mm base, pins to y=40 mm; one solid |
| `McMaster-92815A202.step` | 92815A202_NO THREADS_Low-Profile Knurled-Head Thumb Nuts.STEP (SolidWorks 2024, AP203, mm) | mcmaster.com 92815A202, "3-D STEP", no threads | Axis +Z through origin, z from -2.5 to 2.5 mm; Ø20 mm knurled head, Ø5 mm plain bore, collar at +Z; one solid |
| `McMaster-8215K2.step` | 8215K2_Load-Rated Adhesive-Back Sorbothane Bumper.STEP (SolidWorks 2024, AP203, mm) | mcmaster.com 8215K2, "3-D STEP" | Hemisphere, axis +Y through origin, adhesive face at y=-7.9375 mm, apex at y=7.9375 mm; Ø1.25 in; one solid |
| `McMaster-93339A252.step` | 93339A252_NO THREADS_Easy-Adjust Alloy Steel Ball-Tip Set Screw.STEP (SolidWorks 2024, AP203, mm) | mcmaster.com 93339A252, "3-D STEP", no threads | Axis +Z through origin, hex-socket end at z=11.99 mm, ball apex at z=-13.01 mm, 25.0 mm overall; Ø5 mm plain body, 2.5 mm hex socket; two solids (body, Ø3 mm ball) |
| `McMaster-94459A797.step` | 94459A797_NO THREADS_Heat-Set Inserts for Plastic.STEP (SolidWorks 2024, AP203, mm) | mcmaster.com 94459A797, "3-D STEP", no threads | Axis +Y through origin, flange face at y=3.874 mm, pilot end at y=-2.858 mm, 6.73 mm overall; Ø7.92 mm flange, knurled tapered body, Ø5 mm plain bore; one solid |
| `McMaster-91131A028.step` | 91131A028_Black-Oxide Steel Leveling Washer.STEP (SolidWorks 2024, AP203, mm) | mcmaster.com 91131A028, "3-D STEP" | Axis +Y through origin, two-piece spherical washer assembled, y from -3.378 to 3.378 mm (6.756 mm overall); two solids (female washer Ø12.7 mm OD, y -3.378 to 0.591; male washer Ø11.13 mm OD, y -0.969 to 3.378) |
| `McMaster-8681N11.step` | 8681N11_3 Long Corner Bracket for Aluminum Bolt-Together Framing.STEP (SolidWorks 2024, AP203, mm) | mcmaster.com 8681N11, "3-D STEP" | Extrusion axis +X centered on the origin (x ±16.637 mm, 33.274 mm wide); L section in the y-z plane, outer corner at (y, z) = (-38.1, -38.1) mm, legs 76.2 mm (3 in) long and 6.35 mm thick toward +y and +z; four Ø8.33 mm holes, two per leg; one solid |
| `McMaster-98164A527.step` | 98164A527_NO THREADS_316 Stainless Steel Button Head Hex-Drive Screw.STEP (SolidWorks 2024, AP203, mm) | mcmaster.com 98164A527, "3-D STEP no threads" | Axis +Z through origin, z from -17.463 to 21.679 mm; Ø13.87 mm button head at +Z (head 4.216 mm, bearing face at z=17.463 mm), 34.925 mm (1-3/8 in) plain shank to -Z; no threads; one solid |
| `McMaster-90099A030.step` | 90099A030_NO THREADS_18-8 Stainless Steel Heavy-Profile Nylon-Insert Locknut.STEP (SolidWorks 2024, AP203, mm) | mcmaster.com 90099A030, "3-D STEP no threads" | Axis +Y through origin, y from -5.556 to 5.556 mm (7/16 in); hex 14.29 mm across flats, 16.48 mm across corners; nylon insert at +Y; no threads; two solids (nut, insert) |
| `McMaster-96659A134.step` | 96659A134_18-8 Stainless Steel SAE Washer.STEP (SolidWorks 2024, AP203, mm) | mcmaster.com 96659A134, "3-D STEP" | Axis +Z through origin, z from -0.832 to 0.832 mm (1.664 mm thick); Ø17.48 mm OD; one solid |
| `McMaster-92290A228.step` | 92290A228_NO THREADS_Super-Corrosion-Resistant 316 Stainless Steel Socket Head Screw.STEP (SolidWorks 2024, AP203, mm) | mcmaster.com 92290A228, "3-D STEP no threads" | Axis +Z through origin, z from -8.5 to 8.5 mm (M5 × 12 under the head plus the 5 mm head); Ø8.5 mm head of 5 mm at +Z, Ø5 mm plain shank to -Z; no threads; one solid |
| `McMaster-92290A242.step` | 92290A242_NO THREADS_Super-Corrosion-Resistant 316 Stainless Steel Socket Head Screw.STEP (SolidWorks 2024, AP203, mm) | mcmaster.com 92290A242, "3-D STEP no threads" | Axis +Z through origin, z from -12.5 to 12.5 mm (M5 × 20 under the head plus the 5 mm head); Ø8.5 mm head at +Z, Ø5 mm plain shank to -Z; no threads; one solid |
| `McMaster-93475A240.step` | 93475A240_18-8 Stainless Steel General Purpose Washer.STEP (SolidWorks 2024, AP203, mm) | mcmaster.com 93475A240, "3-D STEP" | Axis +Z through origin, z from -0.5 to 0.5 mm (1.0 mm thick); Ø10 mm OD; one solid |
| `McMaster-91292A114.step` | 91292A114_NO THREADS_18-8 Stainless Steel Socket Head Screw.STEP (SolidWorks 2024, AP203, mm) | mcmaster.com 91292A114, "3-D STEP no threads" | Axis +Z through origin, z from -7.5 to 7.5 mm (M3 × 12 under the head plus the 3 mm head); Ø5.5 mm head at +Z, Ø3 mm plain shank to -Z; no threads; one solid |
| `McMaster-91828A211.step` | 91828A211_NO THREADS_Corrosion-Resistant 18-8 Stainless Steel Hex Nut.STEP (SolidWorks 2024, AP203, mm) | mcmaster.com 91828A211, "3-D STEP no threads" | Axis +Z through origin, z from -1.2 to 1.2 mm (2.4 mm high); hex 5.5 mm across flats (x), 6.326 mm across corners (y); no threads; one solid |
| `McMaster-92290A265.step` | 92290A265_NO THREADS_Super-Corrosion-Resistant 316 Stainless Steel Socket Head Screw.STEP (SolidWorks 2024, AP203, mm) | mcmaster.com 92290A265, "3-D STEP no threads" | Axis +Z through origin, z from -27.5 to 27.5 mm (M5 × 50 under the head plus the 5 mm head); Ø8.5 mm head at +Z, Ø5 mm plain shank to -Z; no threads; one solid |
| `McMaster-91116A350.step` | 91116A350_18-8 Stainless Steel Oversized Washer.STEP (SolidWorks 2024, AP203, mm) | mcmaster.com 91116A350, "3-D STEP" | Axis +Z through origin, z from -0.6 to 0.6 mm (1.2 mm thick); Ø15 mm OD; one solid |
| `McMaster-93625A225.step` | 93625A225_NO THREADS_18-8 Stainless Steel Nylon-Insert Locknut.STEP (SolidWorks 2024, AP203, mm) | mcmaster.com 93625A225, "3-D STEP no threads" | Axis +Y through origin, y from -2.5 to 2.5 mm (5 mm high); hex 8 mm across flats (x), 9.11 mm across corners (z); nylon insert at +Y; no threads; two solids (nut, insert) |
| `Kozak-TS250-80-2500.step` | TS250-80-2500.STEP (SolidWorks 2013, AP214, mm) | kozakusa.com TS250-80-2500, "3D MODELS" zip | Axis +X through origin, x from -1.984 to 61.516 mm, 63.5 mm (2.5 in) overall, Ø6.35 mm (1/4 in) envelope; two solids |
| `Kozak-TB250-80-625.step` | TB250-80-625.STEP (SolidWorks 2013, AP214, mm) | kozakusa.com TB250-80-625, "3D" zip | Axis +X, off origin: (y, z) = (94.65, 0) mm, x from -60.966 to -45.091 mm, 15.875 mm (5/8 in) long, Ø8.941 mm envelope; one solid |
| `Kozak-KB250-80.step` | KB250-80.STEP (SolidWorks 2013, AP214, mm) | kozakusa.com KB250-80, "3D MODELS" zip | Axis +X through origin, x from -1.538 to 9.892 mm, 11.43 mm long, Ø12.7 mm (0.5 in) envelope; one solid |

Thorlabs CAD downloads are listed per product through the site's GraphQL API at
`https://www.thorlabs.com/graphql`, e.g. `{ products(storeId: "Thorlabs-Website", filter: "name:\"SM1RC/M\"")
{ items { name assets { group optiUrl } } } }`; the `Step` asset is the one build123d can read (the `CAD PDF`
asset is the drawing filed in `docs/reference/`). SolidWorks (`.sldprt`) and eDrawing files are not usable here.

Project policy: where a vendor model is available, use its exact values in preference to rounded dimensions
from the drawing. Thorlabs SM1 parts are inch-primary, so their models are exact while the drawings' mm values
are rounded (e.g. SMR1/M 0.400 in = 10.16 mm, drawn as 10.2 mm). The reverse also occurs: the metric TR50/M
model is rounded to inches (1.969 in, 0.499 in), so its exact metric nominals (50 mm, Ø12.7 mm) are used.
