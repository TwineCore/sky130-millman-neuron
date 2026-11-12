#!/bin/bash
# Phase 3 complète (détachée) : corners puis Monte Carlo
cd /foss/designs/twine_neuron
python3 -u sim/run_phase3.py all -j 3 > sim/out/phase3_corners.log 2>&1
python3 -u sim/run_mc.py dcnet N=200 > sim/out/phase3_mc_dcnet.log 2>&1
python3 -u sim/run_mc.py comp N=200 -j 4 > sim/out/phase3_mc_comp.log 2>&1
echo FIN > sim/out/phase3_done.flag
