# BugBuster — modified Creality CR-10

Custom Marlin build (`bugfix-2.1.x`). PrusaSlicer profiles: `BugBuster_PrusaSlicer_bundle.ini`.

## Hardware upgrades

- 2 diagonal braces on the frame for stability
- Dual motorized Z axes (auto-aligned with `G34`)
- Z axes on linear rails (no wheels)
- Mainboard: BTT SKR V1.4 Turbo
- 24 V power supply for the electronics and hotend; the bed heater stays on 12 V
- TMC2209 drivers on all axes
- BLTouch probe + Unified Bed Leveling, corner adjustment from the LCD
- Hard rubber feet, stiffer bed-leveling springs
- OctoPrint connected to the board over USB

## Current configuration

| Item | State |
|---|---|
| Extruder | Direct drive, metal dual-gear extruder kit (139 steps/mm) on a Creality 42-40 motor. Filament path: ~60 mm from the gears to the hotend entry, ~110 mm from the gears to the nozzle (a Bowden setup was tried and dropped: slow, messy retractions). Wave patterns from the head's weight → fix with input shaping |
| Filament sensor | BTT Smart Filament Sensor V2.0. Wiring per BTT manual: black (GND) + green (motion) → E0-DET; red (5V) + blue (switch) → E1-DET. **Switch mode since 2026-10-15**: firmware reads the blue wire on E1-DET (`FIL_RUNOUT_PIN P1_25`, pins file patched to allow the override); the encoder gave false runouts even at 25 mm. Runout = switch opens, then 10 mm more before `M600` |
| X homing | Original microswitch on X-STOP, actuated by a printed part on the direct-drive carriage (sensorless dropped: it pushed hard enough to tilt the extruder). X driver DIAG must be disconnected |
| Y homing | Original microswitch on Y-STOP, Y driver DIAG disconnected |
| Printable area | **264 × 300 mm** (X0 = 21 mm from the bed's left edge; Y0 = bed front edge) |
| Bed | Original aluminium plate, dished: mesh 2026-10-14 = center ≈ +0.03, edges +0.2…+0.4 (0.39 mm spread), corners within 0.1 of each other after tramming. A glass plate worked better |
| Probe | BLTouch, offset X-45 **Y-11** (re-measured 2026-10-14 with the direct drive) **Z-1.85** (tuned on the first layer 2026-10-15) |
| Nozzle | **0.6 mm** (PrusaSlicer profiles "… 0.6 @BugBuster"; the "… 0.4 @BugBuster" profiles reappear if the printer nozzle is set back to 0.4. PrusaSlicer hides the text after "@", so the nozzle size must come before it) |
| Leveling | UBL 10×10 grid, mesh stored in slot 1 |
| Printing | Over USB from OctoPrint, or from the SKR's **onboard SD slot** (`SDCARD_CONNECTION ONBOARD`, 2026-10-15: before, Marlin looked for the card in the CR10 display, which has no slot → `No SD card` / `Media Init Fail`). The onboard card is also shared with the Pi over USB (needed for OctoPrint's Firmware Updater, `lpc1768` method); only one side can use it at a time |

## Motion settings (EEPROM, `M503` on 2026-10-14, after flashing + `M502`/`M500`)

| Setting | Value |
|---|---|
| Steps/mm (`M92`) | X80 Y80 Z400 E139 |
| Max feedrate (`M203`) | X500 Y500 Z5 E25 mm/s |
| Max acceleration (`M201`) | X1500 Y1250 Z100 **E3000** (2026-10-15: E10000 caused the violent extruder "sneezes") |
| Acceleration (`M204`) | Print 1000, **retract 1000**, travel 1500 |
| Junction deviation | 0.013 |
| Hotend PID (`M301`) | P19.87 I1.44 D68.53 (autotune 210 °C, fan 100 %, new hotend, 2026-10-14) |
| Linear Advance | Off (`M900 K0`) |
| Input shaping | **Removed from the firmware** (2026-10-15) — see *Why input shaping is off* |
| Motor current (`M906`) | X1000 Y1000 Z800 E800 |
| Babystep | 4 steps = 0.01 mm per knob click |

## Why input shaping is off

Input shaping (`INPUT_SHAPING_X/Y`) is **disabled in the firmware on purpose** (2026-10-15). Don't re-enable it without reading this.

**What was tried**
1. Sweep tower (`calibration/ringing_tower.py`, shaping swept 20→60 Hz with `M593`, test accel X4000 Y2500/3000):
   the Y axis (bed) ground and skipped steps — short Y moves, layer shifts — always starting around Z≈2 mm, i.e. exactly when shaping switched on at ~20 Hz. Same result in stealthChop and in spreadCycle, at Y 3000 and Y 2500.
2. Same tower with shaping **off** (`ringing_tower.py petg off`): printed cleanly, no grinding. Ripple spacing at 66.7 mm/s gave ~22 Hz and ~27 Hz (front/back faces = Y, left/right = X).
3. Check tower with shaping fixed at `M593 X F22 Y F27`: **the bed ground instantly**.

**Conclusion**: on this printer (heavy 300×300 Y bed, TMC2209, SKR 1.4 Turbo), enabling shaping on Y makes the bed motor grind and lose steps, whatever the motor mode or acceleration. Not worth chasing: some ghosting is acceptable, so shaping was removed (it also frees ~5 KB of RAM).

**Consequences**
- Accelerations stay moderate (`M201` X1500 Y1250, `M204` P1000 T1500): raising them without shaping would only add ghosting, and the bed skips steps above ~2500 anyway.
- `HYBRID_THRESHOLD` stays on (spreadCycle above 100 mm/s) to protect the bed from skipped steps.
- If ever retried: re-enable `INPUT_SHAPING_X` only (keep Y off), and test with the check tower: `python3 calibration/ringing_tower.py petg verify 22 0` (Y F0 = no shaping on Y).

## LCD / host features

- **Main menu → BugBuster tools** (only when idle): Home + align Z (G34) · Build mesh → slot 1 (bed 60 °C, ~10 min, activates and saves) · Load mesh slot 1 · Nozzle service pos (Z100, front center) · Cooldown + motors off
- Double-click on status screen = Z babystep (0.01 mm/click, saved into probe offset with `M500`)
- Prepare → Load / Unload filament; preheat shortcut; Info menu; mute option
- Progress + remaining time on the LCD for OctoPrint prints (`M73` from PrusaSlicer)
- Cancel a single object during a print (`M486`, PrusaSlicer "Label objects: firmware")
- OctoPrint can stop the printer instantly (`EMERGENCY_PARSER`) and shows Marlin prompts (filament change, pause)
- Driver monitoring: overheating drivers get their current reduced automatically
- `HYBRID_THRESHOLD`: X/Y switch from stealthChop (quiet) to spreadCycle (torque) above 100 mm/s, Z above 3 mm/s. **Kept on purpose** (2026-10-15): the heavy Y bed has caused layer shifts in the past; travel at 150 mm/s is louder but safer. Adjust with `M913 X<mm/s> Y<mm/s>` + `M500`

## DIAG pins (SKR 1.4 Turbo)

On this board the TMC2209 DIAG pin reaches the endstop / DET connector **directly through the driver socket** (no jumper; BTT: cut the DIAG pin if StallGuard isn't used). Marlin can't read StallGuard over UART (`SPI_ENDSTOPS` is TMC2130/5160 only), so the pin itself decides:

| Driver | DIAG pin | Goes to |
|---|---|---|
| X | **Bend out** (physical switch since 2026-10-14) | X-STOP |
| Y | **Bend out** | Y-STOP (switch) |
| Z | Bend out (optional, Z-STOP unused) | Z-STOP |
| E0 | **Bend out** | E0-DET (filament motion signal) |
| E1 (= Z2) | **Bend out** | E1-DET (filament sensor 5V + switch) |

## Known issues / to-do

- [x] **After flashing** (EEPROM layout changed): `M502`, `M500`, then check `M503` — done 2026-10-14, firmware built Oct 14 14:32
- [x] **Endstops** (OK 2026-10-14): `M119` before the first `G28`: Y must read `open` released / `TRIGGERED` pressed by hand. If Y stays `open` when pressed, the Y driver DIAG is still connected → bend out its DIAG pin. Keep the UART jumper under each driver
- [x] ~~X sensorless calibration~~ (`M914 X77` at 650 mA) — replaced by the physical switch
  1. `M84`, push the X carriage by hand to the middle. Keep a hand on the power switch / board reset (without `EMERGENCY_PARSER`, OctoPrint can't interrupt a running `G28`)
  2. `G28 X`
     - stops **before** the end of travel (false trigger) → too sensitive → **lower** `M914 X` by 5
     - **bangs / grinds** at the end → not sensitive enough → **raise** `M914 X` by 5
     - stops cleanly at the end with a soft tap → OK
  3. Repeat from different start positions (near the end, middle, far) and 5× in a row. Check repeatability: after each `G28 X`, `G1 X5 F3000` and compare the nozzle against a mark/feeler gauge, it must land at the same spot
  4. Take the middle of the working range, `M914 X<value>`, `M500`, and write the value here
- [x] **X physical switch** (firmware built 2026-10-14): — done 2026-10-14/15, switch works
- [x] **Usable range measured** (2026-10-14): X home = 21 mm inside the bed's left edge, X limit 265 (15 mm before the right edge); Y home = 4 mm in front of the bed. Firmware: `X_BED_SIZE 264`, `X_MAX_POS 264`, `Y_MIN_POS -4` (Y0 = bed front edge), `Y_MAX_POS 301`. Probe (45 mm left of nozzle) reaches X 5..219 → `G34` points X20/X215, tramming right inset 50. PrusaSlicer bed: 264 × 300
- [x] **Origin check** — OK 2026-10-14, nozzle at front-left corner (new direct-drive carriage): after `G28`, `G1 X0 Y0 Z5`: the nozzle must sit at the bed's front-left corner. If not, adjust `X_MIN_POS` / `Y_MIN_POS` (negative = home is outside the bed) and the bed size in PrusaSlicer stays 300×300
- [ ] **Hotend fan**: must spin whenever the printer is on (no auto-fan pin configured: `E0_AUTO_FAN_PIN -1`). If it is on a switched fan port, tell Claude to set `E0_AUTO_FAN_PIN`
- [ ] **Hotend type**: if it is a PTFE-lined (non all-metal) hotend, stay ≤ 240 °C (`HEATER_0_MAXTEMP` is 275)
- [x] **Filament sensor** (M119 OK 2026-10-14): check black lands on GND and red on 5V per the board silkscreen. Push filament slowly by hand: `M119` filament state must toggle every ~2.88 mm (blue LED flashes). Z2 driver sits in the E1 socket → bend out its DIAG pin (E1-DET carries the sensor's switch output). False runouts → raise `M412 D` by 1–2 mm + `M500`
- [x] **Probe offset X/Y**: X-45 Y-11 (`M851 Y-11`, firmware updated)
- [x] **Probe offset Z**: -1.92 (Z Probe Wizard, firmware updated)
- [x] **Bed prep + mesh** (2026-10-14): G34, bed tramming, mesh saved in slot 1. Column 9 (X249) was left empty by a single `G29 P3` → `G29 P3`, `G29 S1`, `M500`. Leveling was left OFF by the menu script → `G29 A` + `M500` (menu fixed in the next firmware build)
- [x] **E-steps**: nozzle at 205 °C, mark filament 120 mm above the extruder, `M83` + `G1 E100 F100`. ~20 mm left = OK. Extruder: metal dual-gear upgrade kit (with idler washers) on a Creality 42-40 motor (BJ42D22-23V01, 1 A / 0.4 N·m). Manufacturer value is **139 steps/mm**, so the current setting matches; the test only fine-tunes it. Lubricate the gears — confirmed 2026-10-15: 139 correct
- [x] **Next firmware flash**: build of 2026-10-14 includes hotend PID 19.87/1.44/68.53, probe offset Z-1.92 / Y-11, 0.6 nozzle for G26, mesh menu fix: `G29 A` + smart fill twice (no `M502` needed) — flashed 2026-10-15
- [ ] **Filament sensor in switch mode** (firmware built 2026-10-15): flash, `M412 S1 D10` + `M500` (EEPROM still holds D25), then `M119` with filament in / pulled out (red LED) must toggle. If stuck: bend out the E1 (= Z2) driver DIAG pin, it shares E1-DET
- [x] **E0 "sneeze"** — fixed 2026-10-15 by `M201 E3000` + `M204 R1000` (firmware + PrusaSlicer limits updated). Was: (random, very fast, very strong extruder moves; existed with the Bowden too): send `M122` and check E0 communicates (suspect: driver in standalone mode → own current + wrong microstepping). Check the UART jumper under the E0 socket matches the others. Driver swap test: problem follows the driver → bad driver; stays on the E0 socket → jumper/socket
- [x] **Purge line**: now along X at the front edge (X20→X200, Y16/Y16.6), inside the measured mesh (X5 was extrapolated and printed too high)
- [x] **First-layer travel scraped the bed**: PrusaSlicer lowered to 0.2 mm and travelled fast across the dished bed → Z-hop 0.4 mm on the first layer only (`retract_lift 0.4`, `retract_lift_below 0.3`), re-import the bundle
- [x] **Hotend max flow test** (PETG at 240 °C, nozzle raised `G1 Z50`, `M83`): `G1 E50 F100` (4 mm³/s), `F150` (6), `F200` (8), `F250` (10). Highest speed with a smooth strand and no extruder clicking = max; set PrusaSlicer `filament_max_volumetric_speed` to ~80 % of it (PETG currently 8, PLA 12 — probably too high) — done 2026-10-15: 10 mm³/s extrudes cleanly but strains the extruder mount; PETG limited to 6.5 mm³/s in PrusaSlicer (tower ran perfectly at 6.5)
- [x] **Benchy** (2026-10-15): good result — 0.6 nozzle, mesh active, purge line along X, no sneeze, no false runout
- [x] **Filament change** (OK 2026-10-15): test `M600` once (park, unload 130 mm, insert, auto-load 100 mm (gears→nozzle ≈ 110 mm, the purge does the last 10 mm), purge 50 mm). If the load doesn't reach the nozzle or purges too much, adjust with `M603 L<load> U<unload>` + `M500`. Also try LCD Prepare → Load/Unload filament
- [x] **E motor current**: check the rated current on the motor label (800 mA RMS set, OK for a 1 A motor) — Creality 42-40, 1 A: 800 mA is fine
- [ ] **Bed flatness**: aluminium plate has a ~0.2 mm dish and the probe can't reach X > 270. Plain glass is too shiny → glass + magnetic textured PEI sheet, or textured coated glass. Then rebuild the UBL mesh (slot 1)
- [ ] **Retraction**: profiles use 1.0 mm at 25 mm/s (short ~60 mm path, slightly more than a pure direct drive). Tune 0.6–2.0 mm with a retraction test
- [x] ~~Input shaping~~ — abandoned 2026-10-15 (Y grinding with shaping on). Accelerations stay at X1500 Y1250 / print 1000 / travel 1500: the bed never accelerates as hard as in the tower test (Y 2500). Tower files kept in `calibration/` for reference
- [x] **After flashing the no-shaping firmware** (flashed 2026-10-15) (EEPROM layout changed): `M502`, `M500`, then `G29 L1`, `G29 A`, `M500` (re-activate the mesh), check `M503`
