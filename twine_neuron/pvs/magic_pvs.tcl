gds read ../layout/twine_neuron.gds
load twine_neuron
select top cell
drc style drc(full)
drc check
drc catchup
set n [drc listall count total]
puts "MAGIC_DRC_COUNT $n"
set fo [open magic_drc.txt w]
foreach {c why} [drc listall why] { puts $fo "$c" }
close $fo
extract do local
extract all
ext2spice lvs
ext2spice -o twine_neuron_ext.spice
quit -noprompt
