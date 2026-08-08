"""
DIYPlotterOS - SVG to G-code converter
-----------------------------------------------------
Converts a traced SVG (from Inkscape's Trace Bitmap) into
G-code using this project's exact command set: G90, G1, M3, M5.

Setup:
    pip install svgelements

Usage:
    python svg_to_gcode.py photo.svg photo.gcode [width_mm] [height_mm]

Defaults to 30mm x 24mm if width/height aren't given.
"""

import sys
from svgelements import SVG, Path, Move, Close


def flatten_path(path, samples_per_curve=20):
    """Break a path (including curves) into a list of subpaths,
    each a list of (x, y) points connected by straight lines."""
    subpaths = []
    current = []
    for seg in path.segments():
        if isinstance(seg, Move):
            if len(current) > 1:
                subpaths.append(current)
            current = [(seg.end.x, seg.end.y)]
        elif isinstance(seg, Close):
            if current:
                current.append(current[0])
        else:
            for i in range(1, samples_per_curve + 1):
                t = i / samples_per_curve
                pt = seg.point(t)
                current.append((pt.x, pt.y))
    if len(current) > 1:
        subpaths.append(current)
    return subpaths


def main():
    if len(sys.argv) < 3:
        print("Usage: python svg_to_gcode.py input.svg output.gcode [width_mm] [height_mm]")
        sys.exit(1)

    infile = sys.argv[1]
    outfile = sys.argv[2]
    target_w = float(sys.argv[3]) if len(sys.argv) > 3 else 30
    target_h = float(sys.argv[4]) if len(sys.argv) > 4 else 24

    svg = SVG.parse(infile)
    all_subpaths = []
    minx = miny = float("inf")
    maxx = maxy = float("-inf")

    for element in svg.elements():
        if isinstance(element, Path) and len(element) > 0:
            for sp in flatten_path(element):
                all_subpaths.append(sp)
                for (x, y) in sp:
                    minx = min(minx, x)
                    maxx = max(maxx, x)
                    miny = min(miny, y)
                    maxy = max(maxy, y)

    if not all_subpaths:
        print("No paths found in SVG. Did you trace the bitmap in Inkscape first?")
        sys.exit(1)

    width = maxx - minx
    height = maxy - miny
    scale = min(target_w / width, target_h / height) if width > 0 and height > 0 else 1

    def transform(x, y):
        # Scale, center on origin, and flip Y (SVG is Y-down, plotter is Y-up)
        nx = (x - minx) * scale - (width * scale) / 2
        ny = -((y - miny) * scale - (height * scale) / 2)
        return nx, ny

    with open(outfile, "w") as f:
        f.write("G90\n")
        f.write("M5\n")
        for sp in all_subpaths:
            if len(sp) < 2:
                continue
            x0, y0 = transform(*sp[0])
            f.write(f"G1 X{x0:.3f} Y{y0:.3f}\n")
            f.write("M3\n")
            for (x, y) in sp[1:]:
                nx, ny = transform(x, y)
                f.write(f"G1 X{nx:.3f} Y{ny:.3f}\n")
            f.write("M5\n")
        f.write("G1 X0.000 Y0.000\n")
        f.write("M5\n")

    print(f"Wrote {outfile}: {len(all_subpaths)} subpaths, scaled to fit {target_w}x{target_h}mm")


if __name__ == "__main__":
    main()
