"""Print the field lens station's placement and optics (§7.9); optionally render or show it with the slit head."""

import argparse
from pathlib import Path

from schlieren.cli._common import add_figure_option, add_show_option, render, show
from schlieren.parts.field_lens import FieldLensParameters, build_field_lens_head_assembly

DEFAULT_FIGURE = Path("docs/design/figures/field-lens.png")
# From the mirror side, above and to the right, as the slit head's figure: the lens station ahead of the blades.
FIGURE_VIEW_DIRECTION = (0.9, 1.0, 0.6)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    add_show_option(parser, "Display the slit head and field lens station on their posts in OCP CAD Viewer")
    parser.add_argument(
        "--rotation", type=float, default=0.0, help="Slit head degrees about the optical axis; 0 = horizontal"
    )
    add_figure_option(parser, DEFAULT_FIGURE, "the slit head with the field lens station")
    args = parser.parse_args()
    p = FieldLensParameters()
    p.validate()
    print(f"Lens plano face {p.lens_plano_y:.2f} mm ahead of the blade-seat plane, on the tube's lip")
    print(
        f"Tube thread end {p.tube_end_y:.2f} mm ahead, {p.fold_clearance} mm over the blades' folds, between "
        f"the toe fingers"
    )
    print(
        f"Post {p.post_y:.2f} mm ahead of the blade plane, {p.post_spacing:.1f} mm from the slit head's post"
    )
    print(
        f"Cone from the lit end (±{p.stage.lit_half_length:g} mm) centers {p.chief_ray_shift():+.1f} mm from the "
        f"mirror's center, against {p.unlensed_shift:.0f} mm without the lens"
    )
    print(
        f"Focal length for this position {p.ideal_focal_length:.1f} mm; the lens is {p.lens_focal_length} mm"
    )
    print(
        f"Footprint {p.cone_scale:.3f} of its size without the lens: ±{p.fill_cone_half_angle:.2f}° fills the "
        f"mirror, an iris of Ø{p.fill_iris_diameter:.1f} mm"
    )
    if args.figure:
        render(build_field_lens_head_assembly(p), args.figure, FIGURE_VIEW_DIRECTION)
    if args.show:
        show(build_field_lens_head_assembly(p, args.rotation, side_screws=True))


if __name__ == "__main__":
    main()
