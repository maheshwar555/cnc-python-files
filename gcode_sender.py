"""
DIYPlotterOS - G-code sender
-----------------------------------------------------
Streams a .gcode file to the Arduino over USB serial,
one line at a time, waiting for "ok" after each line.

Setup:
    pip install pyserial

Usage:
    python gcode_sender.py COM5 drawing.gcode        (Windows)
    python gcode_sender.py /dev/ttyUSB0 drawing.gcode (Linux/Mac)

Find your port name:
    Arduino IDE -> Tools -> Port
"""

import sys
import time
import serial

BAUD_RATE = 9600


def send_gcode(port, filepath):
    print(f"Connecting to {port} at {BAUD_RATE} baud...")
    ser = serial.Serial(port, BAUD_RATE, timeout=5)
    time.sleep(2)  # wait for Arduino to reset after serial connect

    # flush any startup message ("DIYPlotterOS ready")
    ser.reset_input_buffer()

    with open(filepath, "r") as f:
        lines = [line.strip() for line in f if line.strip()]

    total = len(lines)
    print(f"Sending {total} lines from {filepath}")

    for i, line in enumerate(lines, start=1):
        # skip pure comment lines
        if line.startswith(";") or line.startswith("("):
            continue

        ser.write((line + "\n").encode())

        response = ser.readline().decode(errors="ignore").strip()
        while response and "ok" not in response.lower():
            print(f"  Arduino: {response}")
            response = ser.readline().decode(errors="ignore").strip()

        print(f"[{i}/{total}] {line}  -> ok")

    ser.close()
    print("Done.")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python gcode_sender.py <port> <file.gcode>")
        sys.exit(1)

    send_gcode(sys.argv[1], sys.argv[2])
