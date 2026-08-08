"""
DIYPlotterOS - G-code preview
-----------------------------------------------------
Renders a .gcode file as an image, showing exactly what
the plotter would draw -- WITHOUT touching any hardware.
Pen-down moves are drawn as solid lines; pen-up travel
moves are shown as thin dashed grey lines so you can see
if the pen is jumping around oddly.

Setup:
    pip install matplotlib

Usage:
    python gcode_preview.py flower.gcode
    (creates flower_preview.png and opens it)
"""

import sys
import os
import matplotlib.pyplot as plt


def parse_gcode(filepath):
    pen_down = False
    x, y = 0.0, 0.0
    down_segments = []   # list of (x1,y1,x2,y2) while pen is down
    up_segments = []     # list of (x1,y1,x2,y2) while pen is up (travel)

    with open(filepath, "r") as f:
        for raw_line in f:
            line = raw_line.split(";")[0].strip()
            if not line:
                continue

            tokens = line.split()
            cmd = tokens[0].upper() if tokens else ""

            if cmd == "M3":
                pen_down = True
                continue
            if cmd == "M5":
                pen_down = False
                continue
            if cmd in ("G0", "G1"):
                newx, newy = x, y
                for tok in tokens[1:]:
                    if tok.upper().startswith("X"):
                        newx = float(tok[1:])
                    elif tok.upper().startswith("Y"):
                        newy = float(tok[1:])
                if pen_down:
                    down_segments.append((x, y, newx, newy))
                else:
                    up_segments.append((x, y, newx, newy))
                x, y = newx, newy

    return down_segments, up_segments


def main():
    if len(sys.argv) < 2:
        print("Usage: python gcode_preview.py <file.gcode>")
        sys.exit(1)

    infile = sys.argv[1]
    down_segments, up_segments = parse_gcode(infile)

    fig, ax = plt.subplots(figsize=(6, 6))

    for (x1, y1, x2, y2) in up_segments:
        ax.plot([x1, x2], [y1, y2], color="lightgrey", linewidth=0.5, linestyle="--")

    for (x1, y1, x2, y2) in down_segments:
        ax.plot([x1, x2], [y1, y2], color="black", linewidth=1.2)

    ax.set_aspect("equal")
    ax.set_title(f"Preview: {os.path.basename(infile)}\n(solid = pen down, dashed grey = pen up travel)")
    ax.set_xlabel("X (mm)")
    ax.set_ylabel("Y (mm)")
    ax.grid(True, linewidth=0.3, alpha=0.5)

    outname = os.path.splitext(infile)[0] + "_preview.png"
    plt.savefig(outname, dpi=150, bbox_inches="tight")
    print(f"Saved preview: {outname}")
    print(f"Pen-down moves: {len(down_segments)}, travel moves: {len(up_segments)}")

    plt.show()


if __name__ == "__main__":
    main()
