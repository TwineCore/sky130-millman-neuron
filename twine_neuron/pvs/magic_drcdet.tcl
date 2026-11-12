gds read ../layout/twine_neuron.gds
load twine_neuron
select top cell
drc style drc(full)
drc check
drc catchup
foreach {why boxes} [drc listall why] {
  set n [llength $boxes]
  set b [lindex $boxes 0]
  puts "DRCW $n | $why | [lrange $boxes 0 2]"
}
quit -noprompt
