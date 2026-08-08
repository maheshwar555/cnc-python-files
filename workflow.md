# DIYPlotterOS — Image Printing Workflow (Cheat Sheet)

Your setup: Uno + L293D shield + 2 DVD drives + servo
Working area: ~30mm x 24mm (safe zone)
Port: COM5

## Files you need (all in your Downloads folder)
- plotter.ino + config.h        -> Arduino firmware (only re-upload if changed)
- svg_to_gcode.py                -> converts traced SVG -> G-code
- gcode_preview.py                -> preview before printing (no hardware needed)
- gcode_sender.py                -> sends G-code to the Arduino

## Every time you want to print a NEW image:

### 1. Pick a good source image
- Simple, high-contrast, bold outlines work best
- Avoid busy photos / lots of fine texture — it won't resolve at this size

### 2. Trace it in Inkscape
1. File -> Open -> your image
2. Select the image -> Path -> Trace Bitmap
3. Choose "Brightness cutoff", adjust threshold slider until preview looks like
   a clean silhouette
4. Click OK, close the dialog
5. Click the original photo underneath, delete it (keep only the traced shape)
6. Path -> Simplify (Ctrl+L) once or twice — reduces noisy detail
7. File -> Save As -> "Plain SVG" -> save into your Downloads folder
   ⚠️ Check the filename afterward with: dir *.svg
   (Windows sometimes hides the real extension — you may get name.svg.svg)

### 3. Convert SVG to G-code
Open Command Prompt:
    cd "C:\Users\anil kumar\Downloads"
    python svg_to_gcode.py yourimage.svg yourimage.gcode

Wait for: "Wrote yourimage.gcode: N subpaths, scaled to fit 30x24mm"

### 4. Preview it BEFORE printing (no hardware needed)
    python gcode_preview.py yourimage.gcode

Check the popup window:
- Does it look like a clean, recognizable, connected shape?
- If it looks scrambled/messy already in the preview -> go back to step 2,
  simplify more in Inkscape, re-save, re-convert.
- If it looks clean here -> safe to print for real.

### 5. Print it for real
1. Power OFF the plotter
2. Manually recenter the carriage on BOTH axes (middle of rail travel)
3. Power back ON
4. Close Arduino IDE's Serial Monitor if it's open (frees the COM port)
5. Run:
    python gcode_sender.py COM5 yourimage.gcode
6. Watch it print. If it ends in "Done." with no errors, you're finished.

## If something goes wrong

| Symptom                                  | Likely cause / fix                                  |
|-------------------------------------------|-------------------------------------------------------|
| "Access is denied" / PermissionError      | Close Serial Monitor, unplug/replug USB, retry        |
| "File not found"                          | Wrong filename (check for hidden .svg.svg / .txt) or wrong folder — run `dir` to check |
| Motors grind at rail edge                 | Carriage wasn't recentered before powering on         |
| Drawing looks doubled/offset lines        | Backlash — try raising BACKLASH_X/Y in config.h        |
| Drawing drifts / gets worse over time     | Already fixed in current firmware (position tracking) |
| A section is fully offset/detached        | Try raising BACKLASH_X/Y and/or lowering MOTOR_SPEED   |
| Arduino resets mid-print ("ready" reappears) | Motors/servo need external power, not just USB      |

## Current calibration (already tuned, don't change unless recalibrating)
    X_STEPS 6.8
    Y_STEPS 9.9
    PEN_UP 130
    PEN_DOWN 100
    MOTOR_SPEED 20
    BACKLASH_X 10
    BACKLASH_Y 10
    X_MIN -18 / X_MAX 18
    Y_MIN -15 / Y_MAX 15
