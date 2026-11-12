#!/bin/bash
# Phase 6, PEX v3 : coins post-layout (dccrit/settle/power, 2 en parallèle) puis fonctionnel par porte aux 5 coins,
# puis ré-agrégation (run_phase3 saute les points déjà calculés et relit les *_metrics_func.csv)
cd /foss/designs/twine_neuron
export TN_CTAG=p TN_NETLIST=/foss/designs/twine_neuron/pex/twine_neuron_pex.spice TN_RSHUNT=1e12
python3 -u sim/run_phase3.py post -j 2 2>&1 | grep -v INFO
python3 -u sim/post_func_corners.py 2>&1 | grep -v INFO
python3 -u sim/run_phase3.py post -j 2 2>&1 | grep -v INFO
echo DONE
