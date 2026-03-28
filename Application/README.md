# OpenCAD — Sim-to-Real Gap Correction: Demonstration Simulations

**Authors:** Shreya Priya, Dean Hu
**Target venue:** CoRL 2026

## Overview

This folder contains MuJoCo simulation scripts demonstrating OpenCAD's ability to autonomously detect and correct geometric faults in robot CAD models that cause sim-to-real performance gaps.

Each simulation runs two identical robot arms side by side receiving identical joint commands. The left arm has correct geometry (ground truth). The right arm has a deliberate geometric fault causing it to fail the task. OpenCAD detects the fault, corrects the geometry, and the corrected arm succeeds.

## Structure
```
Application/
├── Problem1_ForearmLength/   — elbow link 37% too short
├── Problem2_WristOffset/     — wrist lateral offset 7.7% wrong (in progress)
└── Problem3_JointFriction/   — joint friction 112% too high (in progress)
```

## Problem Descriptions

**Problem 1 — Forearm Length:** Forearm link is 0.24m vs correct 0.38m. At identical joint commands the faulty arm's EE falls 0.14m short of the Coke can. OpenCAD rebuilds the forearm to correct length. Corrected arm succeeds.

**Problem 2 — Wrist Offset:** Wrist joint has 7.7% lateral offset error. Faulty arm consistently misses target to one side. OpenCAD corrects the offset parameter.

**Problem 3 — Joint Friction:** Friction coefficients 112% too high. Faulty arm stalls before completing trajectory. OpenCAD corrects the friction model.

## Requirements
```
python >= 3.10
mujoco >= 3.0
numpy, pillow, imageio[ffmpeg]
```

## Running Problem 1
```bash
cd Problem1_ForearmLength
python render_video1_final.py
```
