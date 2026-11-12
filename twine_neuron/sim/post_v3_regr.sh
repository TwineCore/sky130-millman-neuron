#!/bin/bash
# Régression post-layout v3 (pistes du comparateur en miroir) : func par porte (séquentiel, mémoire) puis dccrit/power/settle
cd /foss/designs/twine_neuron
export TN_NETLIST=/foss/designs/twine_neuron/pex/twine_neuron_pex.spice TN_RSHUNT=1e12
for g in AND OR NAND; do
  TN_FUNC_GATES=$g TN_TAG=post_$g python3 -u sim/run_phase2.py func 2>&1 | grep -v INFO
done
TN_TAG=post python3 -u sim/run_phase2.py dccrit power settle 2>&1 | grep -v INFO
