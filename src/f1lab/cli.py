import argparse
from pathlib import Path
from .data import demo, real


def main():
    p=argparse.ArgumentParser(description="Prepare F1 Telemetry Lab data")
    p.add_argument("mode", choices=["demo","real"])
    p.add_argument("--output",type=Path)
    p.add_argument("--year",type=int,default=2024)
    p.add_argument("--drivers",nargs=2,default=["NOR","LEC"])
    args=p.parse_args()
    output=args.output or Path("data")/args.mode
    if args.mode=="demo": demo(output)
    else: real(output,year=args.year,drivers=args.drivers)
    print(f"Validated export: {output.resolve()}")


if __name__=="__main__": main()
