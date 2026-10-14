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
| Extruder | Direct drive (a Bowden setup was tried and dropped: slow, messy retractions). Wave patterns from the head's weight → fix with input shaping |
| Filament sensor | On the direct drive, plugged into E0DET, enabled by default |
| X/Y homing | Original microswitches on X-STOP / Y-STOP (sensorless homing disabled: it ground against the frame). X/Y DIAG jumpers removed |
| Bed | Original aluminium plate, not flat (~0.2 mm dish: -1.2 corners, -1.4 center). A glass plate worked better |
| Probe | BLTouch, offset X-45 Y-14 Z-1.42 |
| Leveling | UBL 10×10 grid, mesh stored in slot 1 |
| Printing | Over USB from OctoPrint. Onboard SD enabled, so firmware can be flashed from OctoPrint (Firmware Updater plugin, `lpc1768` method) |

## Motion settings (EEPROM, `M503` on 2026-10-09)

| Setting | Value |
|---|---|
| Steps/mm (`M92`) | X80 Y80 Z400 E139 |
| Max feedrate (`M203`) | X500 Y500 Z5 E25 mm/s |
| Max acceleration (`M201`) | X1500 Y1250 Z100 E10000 |
| Acceleration (`M204`) | Print 1000, retract 1500, travel 1500 |
| Junction deviation | 0.013 |
| Linear Advance | Off (`M900 K0`) |
| Input shaping | Off (`M593 F0` on X and Y) |
| Motor current (`M906`) | X1000 Y1000 Z800 E800 |

## Known issues / to-do

- [ ] **After flashing** (EEPROM layout changed): `M502`, `M500`, then check `M503`
- [ ] **Endstops**: test with `M119` (press each switch by hand) before the first `G28`
- [ ] **Probe offset**: re-measure `NOZZLE_TO_PROBE_OFFSET` if the BLTouch mount moved with the direct drive
- [ ] **E-steps**: 100 mm extrusion test on the direct drive (currently 139)
- [ ] **Bed flatness**: aluminium plate has a ~0.2 mm dish and the probe can't reach X > 270. Plain glass is too shiny → glass + magnetic textured PEI sheet, or textured coated glass. Then rebuild the UBL mesh (slot 1)
- [ ] **Input shaping**: calibrate (ringing tower), then raise acceleration to cut print times
