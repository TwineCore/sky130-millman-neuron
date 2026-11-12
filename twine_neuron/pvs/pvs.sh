#!/bin/bash
# DRC KLayout + DRC magic + extraction magic + LVS netgen (dans le conteneur, depuis pvs/)
cd /foss/designs/twine_neuron/pvs
GDS=../layout/twine_neuron.gds
klayout -b -r /foss/pdks/sky130A/libs.tech/klayout/drc/sky130A_mr.drc -rd input=$GDS -rd report=/foss/designs/twine_neuron/pvs/klayout_drc.lyrdb \
  -rd feol=true -rd beol=true -rd offgrid=true > klayout_drc.log 2>&1
python3 - <<PY > klayout_drc_summary.txt
import xml.etree.ElementTree as ET, collections
t = ET.parse("klayout_drc.lyrdb").getroot()
cats = {c.findtext("name"): c.findtext("description") for c in t.iter("category")}
cnt = collections.Counter(i.findtext("category").strip("\x27") for i in t.iter("item"))
print("categories checked:", len(cats), " violations:", sum(cnt.values()))
for k, v in cnt.most_common():
    print(f"{v:6d}  {k:22s} {cats.get(k, cats.get(chr(39)+k+chr(39), str()))}")
PY
cat > magic_pvs.tcl <<TCL
gds read $GDS
load twine_neuron
select top cell
drc style drc(full)
drc check
drc catchup
set n [drc listall count total]
puts "MAGIC_DRC_COUNT \$n"
set fo [open magic_drc.txt w]
foreach {c why} [drc listall why] { puts \$fo "\$c" }
close \$fo
extract do local
extract all
ext2spice lvs
ext2spice -o twine_neuron_ext.spice
quit -noprompt
TCL
magic -dnull -noconsole -rcfile /foss/pdks/sky130A/libs.tech/magic/sky130A.magicrc magic_pvs.tcl > magic_pvs.log 2>&1
grep MAGIC_DRC_COUNT magic_pvs.log
netgen -batch lvs "twine_neuron_ext.spice twine_neuron" "../netlist/twine_neuron.spice twine_neuron" \
  /foss/pdks/sky130A/libs.tech/netgen/sky130A_setup.tcl lvs.out > netgen.log 2>&1
grep -E "Final result|Circuits match|Netlists do not|pin lists|[Pp]roperty errors|Number of devices|Number of nets" lvs.out | sort | uniq -c | head -20
head -25 klayout_drc_summary.txt
