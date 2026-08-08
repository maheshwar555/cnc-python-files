"""
DIYPlotterOS - G-code path sorter
-----------------------------------------------------
Reorders subpaths in a .gcode file to minimize total
pen-up travel distance. This reduces the number of long
jumps between sections, which is the main cause of
misalignment between letters/shapes in complex prints.

Usage:
    python sort_gcode.py input.gcode output.gcode
"""

import sys
import math


def parse_gcode(filepath):
    """Parse gcode into a list of subpaths.
    Each subpath is a list of lines between M3 and M5."""
    subpaths = []
    current = []
    header = []
    footer = []
    in_body = False
    pen_down = False

    with open(filepath, "r") as f:
        lines = [l.rstrip() for l in f.readlines()]

    i = 0
    # collect header (everything before first M3)
    while i < len(lines):
        line = lines[i].split(";")[0].strip()
        if line == "M3":
            in_body = True
            break
        header.append(lines[i])
        i += 1

    # parse subpaths
    current_travel = None
    current_draw = []

    while i < len(lines):
        line = lines[i].split(";")[0].strip()

        if line == "M3":
            pen_down = True
            current_draw = []
        elif line == "M5":
            if pen_down and current_draw:
                subpaths.append({
                    "travel": current_travel,
                    "draw": current_draw,
                    "start": get_xy(current_draw[0]) if current_draw else (0, 0),
                    "end": get_xy(current_draw[-1]) if current_draw else (0, 0)
                })
            pen_down = False
            current_travel = None
            current_draw = []
        elif line.startswith("G1"):
            if pen_down:
                current_draw.append(lines[i])
            else:
                current_travel = lines[i]
        elif line.startswith("G0"):
            if not pen_down:
                current_travel = lines[i]
        i += 1

    return header, subpaths


def get_xy(line):
    """Extract X,Y coordinates from a G1 line."""
    x, y = 0.0, 0.0
    parts = line.split(";")[0].strip().split()
    for p in parts:
        if p.upper().startswith("X"):
            try: x = float(p[1:])
            except: pass
        elif p.upper().startswith("Y"):
            try: y = float(p[1:])
            except: pass
    return (x, y)


def distance(a, b):
    return math.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2)


def sort_subpaths(subpaths):
    """Greedy nearest-neighbor sort to minimize pen-up travel."""
    if not subpaths:
        return []

    sorted_paths = []
    remaining = list(subpaths)
    current_pos = (0, 0)

    while remaining:
        # find nearest subpath start to current position
        nearest_idx = 0
        nearest_dist = float("inf")
        for i, sp in enumerate(remaining):
            d = distance(current_pos, sp["start"])
            if d < nearest_dist:
                nearest_dist = d
                nearest_idx = i

        chosen = remaining.pop(nearest_idx)
        sorted_paths.append(chosen)
        current_pos = chosen["end"]

    return sorted_paths


def write_gcode(header, subpaths, outfile):
    with open(outfile, "w") as f:
        # write header
        for line in header:
            f.write(line + "\n")

        for sp in subpaths:
            # travel move to start of subpath (pen up)
            sx, sy = sp["start"]
            f.write(f"G1 X{sx:.3f} Y{sy:.3f}\n")
            f.write("M3\n")
            for line in sp["draw"]:
                f.write(line + "\n")
            f.write("M5\n")

        # return home
        f.write("G1 X0.000 Y0.000\n")
        f.write("M5\n")


def main():
    if len(sys.argv) != 3:
        print("Usage: python sort_gcode.py input.gcode output.gcode")
        sys.exit(1)

    infile = sys.argv[1]
    outfile = sys.argv[2]

    print(f"Reading {infile}...")
    header, subpaths = parse_gcode(infile)
    print(f"Found {len(subpaths)} subpaths")

    print("Sorting paths to minimize travel distance...")
    sorted_paths = sort_subpaths(subpaths)

    print(f"Writing {outfile}...")
    write_gcode(header, sorted_paths, outfile)
    print(f"Done. Saved to {outfile}")


if __name__ == "__main__":
    main()
