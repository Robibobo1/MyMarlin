#!/usr/bin/env python3
"""Input shaping ringing tower for BugBuster (Marlin, 0.6 mm nozzle).

Prints a single-wall square tower as a continuous spiral (vase style) with
sharp corners, at high acceleration, while sweeping the input shaping
frequency with M593 as Z rises. Find the height where ringing after the
corners is weakest, separately on the X faces and the Y faces, then:
    F = F_START + (F_END - F_START) * (h - SWEEP_FROM_Z) / (HEIGHT - SWEEP_FROM_Z)
The LCD also shows the current frequency (M117) during the print.

Test accelerations (M201/M204) and spreadCycle on X/Y (M569 S0) are applied
after the purge and restored from EEPROM (M501) at the end, so nothing is
saved permanently.

Usage: python3 ringing_tower.py [pla|petg] [off | verify FX FY] > out.gcode
  off: input shaping stays off; measure ripple spacing: f = 66.7 * N / D (mm)
"""
import math
import sys

MATERIAL = (sys.argv[1] if len(sys.argv) > 1 else "petg").lower()
# "off": no frequency sweep, shaping stays off; measure the ripples instead:
#   f = SPEED * N / D  (N ripples counted over D mm after a corner), SPEED = 66.7
SWEEP = not (len(sys.argv) > 2 and sys.argv[2].lower() in ("off", "verify"))
# "verify FX FY": shaping fixed at FX (X) and FY (Y) for the whole tower, 30 mm tall
VERIFY = (float(sys.argv[3]), float(sys.argv[4])) if len(sys.argv) > 4 and sys.argv[2].lower() == "verify" else None
TEMPS = {  # nozzle first layer, nozzle, bed, fan (0-255)
    "petg": (240, 240, 80, 128),   # 240 all along: more melt margin for the hotend
    "pla": (210, 205, 60, 255),
}[MATERIAL]

# Geometry (printer coordinates: X 0..264, Y 0..300)
CX, CY = 132.0, 150.0      # tower center
SIDE = 80.0                # square side (mm)
HEIGHT = 30.0 if VERIFY else 60.0   # total height (mm)
FIRST_LAYER = 0.25         # first layer height (mm)
LAYER = 0.15               # spiral pitch per revolution (mm)
WIDTH = 0.65               # extrusion width for a 0.6 mm nozzle
FIRST_WIDTH = 0.7
BASE_LOOPS = 3             # first-layer loops for adhesion

# Motion for the test
FLOW = 6.5                 # mm3/s target (8 gave extruder "sneezes" at the corners)
SPEED = round(FLOW / (0.15 * 0.65), 1)   # mm/s on the walls (= 66.7 for 0.15 x 0.65)
FIRST_SPEED = 25.0         # mm/s first layer
TEST_ACCEL_X, TEST_ACCEL_Y = 4000, 2500   # Y 3000 made the heavy bed skip steps
TEST_ACCEL_PRINT = 3000

# Frequency sweep (SHAPING_MIN_FREQ is 20 Hz in this firmware)
F_START, F_END = 20.0, 60.0
SWEEP_FROM_Z = 1.0         # below this, shaping is off (F0)

FIL_AREA = math.pi * (1.75 / 2) ** 2


def e_per_mm(h, w):
    return h * w / FIL_AREA


def freq_at(z):
    if not SWEEP or z < SWEEP_FROM_Z:
        return 0.0
    return F_START + (F_END - F_START) * (z - SWEEP_FROM_Z) / (HEIGHT - SWEEP_FROM_Z)


def square(inset):
    h = SIDE / 2 - inset
    return [(CX - h, CY - h), (CX + h, CY - h), (CX + h, CY + h), (CX - h, CY + h)]


out = []
w = out.append
t1, t, bed, fan = TEMPS
if VERIFY:
    w(f"; BugBuster input shaping CHECK tower - {MATERIAL.upper()}, 0.6 mm nozzle - shaping fixed X{VERIFY[0]:g} Y{VERIFY[1]:g} Hz")
else:
    w(f"; BugBuster input shaping ringing tower - {MATERIAL.upper()}, 0.6 mm nozzle" + ("" if SWEEP else " - SHAPING OFF, measure ripples: f = {:g} * N / D".format(SPEED)))
w(f"; Sweep {F_START:g} -> {F_END:g} Hz from Z{SWEEP_FROM_Z:g} to Z{HEIGHT:g}")
w(f"; F = {F_START:g} + {F_END - F_START:g} * (h - {SWEEP_FROM_Z:g}) / {HEIGHT - SWEEP_FROM_Z:g}")
w(f"M140 S{bed}")
w("M104 S150")
w("G90")
w("M83")
w("M107")
w("G28")
w("G29 L1")
w("M420 S1")
w("G1 Z10 F300")
w(f"M190 S{bed}")
w(f"M109 S{t1}")
# Purge line along X at the front edge (inside the measured mesh)
w("G1 X20 Y16 F6000")
w("G1 Z0.3 F300")
w("G1 X200 Y16 E15 F1500")
w("G1 X200 Y16.6 F3000")
w("G1 X20 Y16.6 E15 F1500")
w("G1 Z2 F300")
w("G1 E-1 F1500")

# First layer: a few loops at normal acceleration, shaping off
w("M593 F0")
start = square(0)[0]
w(f"G1 X{start[0]:.3f} Y{start[1]:.3f} F6000")
w(f"G1 Z{FIRST_LAYER:.3f} F300")
w("G1 E1 F1500")
epm = e_per_mm(FIRST_LAYER, FIRST_WIDTH)
for loop in range(BASE_LOOPS):
    pts = square(loop * FIRST_WIDTH * 0.9)
    w(f"G1 X{pts[0][0]:.3f} Y{pts[0][1]:.3f} F6000")
    for i in range(1, 5):
        x0, y0 = pts[i - 1]
        x1, y1 = pts[i % 4]
        d = math.hypot(x1 - x0, y1 - y0)
        w(f"G1 X{x1:.3f} Y{y1:.3f} E{d * epm:.5f} F{FIRST_SPEED * 60:.0f}")
w(f"G1 X{start[0]:.3f} Y{start[1]:.3f} F6000")

# Test accelerations for the spiral wall
w("M569 S0 X Y")          # spreadCycle for full torque during the test (restored by M501)
w(f"M201 X{TEST_ACCEL_X} Y{TEST_ACCEL_Y}")
w(f"M204 P{TEST_ACCEL_PRINT} T{TEST_ACCEL_PRINT}")
w(f"M104 S{t}")

# Spiral wall: Z rises continuously, LAYER per revolution
pts = square(0)
epm = e_per_mm(LAYER, WIDTH)
z = FIRST_LAYER
rev = 0
last_f = None
last_lcd = None
while z < HEIGHT:
    if rev == 2:
        w(f"M106 S{fan}")
    # M593 synchronizes the planner (full stop at the start corner), so only
    # change the frequency every 0.5 mm, together with the LCD message.
    if int(z * 2) != last_lcd:
        if VERIFY:
            if last_f is None:
                w(f"M593 X F{VERIFY[0]:g}")
                w(f"M593 Y F{VERIFY[1]:g}")
                last_f = VERIFY
            w(f"M117 Z{z:.1f} IS X{VERIFY[0]:g} Y{VERIFY[1]:g}")
        else:
            f = round(freq_at(z), 1)
            if f != last_f:
                w(f"M593 F{f:.1f}")
                last_f = f
            w(f"M117 Z{z:.1f} IS {f:.1f}Hz")
        last_lcd = int(z * 2)
    for i in range(1, 5):
        x0, y0 = pts[i - 1]
        x1, y1 = pts[i % 4]
        d = math.hypot(x1 - x0, y1 - y0)
        z += LAYER / 4
        w(f"G1 X{x1:.3f} Y{y1:.3f} Z{z:.4f} E{d * epm:.5f} F{SPEED * 60:.0f}")
    rev += 1

# End: restore settings from EEPROM (accelerations, shaping), park, cool down
w("G1 E-1 F1500")
w("M400")
w("M501")
w(f"G1 Z{min(z + 10, 400):.2f} F300")
w("G1 X10 Y290 F3000")
w("M107")
w("M104 S0")
w("M140 S0")
w("M84 X Y E")
w("M117 Ringing tower done")
print("\n".join(out))
