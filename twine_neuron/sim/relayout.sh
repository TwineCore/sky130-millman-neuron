#!/bin/bash
# layout -> PVS -> PEX -> capacités des paires (dans le conteneur)
set -e
cd /foss/designs/twine_neuron/layout && python3 layout_neuron.py | tail -8
bash /foss/designs/twine_neuron/pvs/pvs.sh
cd /foss/designs/twine_neuron/pvs && head -1 klayout_drc_summary.txt && grep MAGIC_DRC_COUNT magic_pvs.log && grep "Final result" lvs.out
cd /foss/designs/twine_neuron/pex && magic -dnull -noconsole -rcfile /foss/pdks/sky130A/libs.tech/magic/sky130A.magicrc pex.tcl > pex.log 2>&1
grep -c "Antenna violation" ../pvs/antenna_pex.log || true
python3 pex_pairs.py
