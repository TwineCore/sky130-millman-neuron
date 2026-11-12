cd /foss/designs/twine_neuron/xschem && export PDK=sky130A && xschem -q -x -n -s -o ../netlist --rcfile ./xschemrc twine_neuron.sch > ../netlist/xschem_netlist.log 2>&1
grep -ciE "error|warning" ../netlist/xschem_netlist.log; grep -E "^XS1P0|^XCMP|^XG0P|^XHM" ../netlist/twine_neuron.spice; grep -E "^XM1 |^XR1 " ../netlist/twine_neuron.spice | head -2
