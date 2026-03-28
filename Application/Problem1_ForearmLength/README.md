# Problem 1 — Forearm Length Fault

## Fault
Elbow link manufactured at 0.24m — 37% shorter than CAD spec of 0.38m.

## Effect
Both arms receive identical joint commands. Correct arm reaches Coke can with 1.5mm error. Faulty arm EE falls 0.14m short — gripper cannot close on can.

## OpenCAD Correction
1. Grasp failure detected — EE miss exceeds threshold
2. Root cause: forearm_length = 0.24m (correct = 0.38m, Δ = −37%)
3. Part('forearm').extrude(Sketch().circle(r=0.024), depth=0.38)
4. Geometry rebuilt → simulation reloaded → corrected arm succeeds

## Verified Configs (68 dry-run tests passed)
```python
HOME_Q  = [0,  1.10, -2.00, -0.70]
HOVER_Q = [0,  0.75, -0.70, -1.45]
PICK_Q  = [0,  0.95, -0.70, -1.45]   # EE dist to can = 0.0015m
LIFT_Q  = [0,  0.65, -0.90, -1.20]
PLACE_Q = [pi,-0.20, -1.45,  1.90]   # EE dist to table = 0.084m
```
