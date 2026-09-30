"""Export the alternative one-piece holder and optionally show cassette fit."""
import argparse
from pathlib import Path
import cadquery as cq
from schlieren.parts.carriage_2 import build_carriage_2, build_carriage_2_assembly


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--show',action='store_true')
    parser.add_argument('--travel',type=float,default=0)
    parser.add_argument('--output',type=Path,default=Path('exports'))
    args=parser.parse_args()
    part=build_carriage_2()
    for kind in ('step','stl'):
        path=args.output/kind/f'carriage_2.{kind}'
        path.parent.mkdir(parents=True,exist_ok=True)
        cq.exporters.export(part,str(path))
        print(path)
    if args.show:
        from ocp_vscode import show
        show(build_carriage_2_assembly(travel=args.travel))


if __name__=='__main__':
    main()
