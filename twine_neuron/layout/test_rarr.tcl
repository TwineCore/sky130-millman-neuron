load rtest -silent
foreach {i x} {0 0 1 1.0 2 2.2 3 3.6} {
  box [expr {$x}]um 0um [expr {$x}]um 0um
  getcell res_unit
}
select top cell
drc catchup
drc style drc(full)
drc check
drc catchup
puts "DRCCOUNT [drc listall count total]"
foreach e [drc listall why] { puts "WHY $e" }
quit -noprompt
