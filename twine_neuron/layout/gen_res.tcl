# Cellule unité R_U : xhigh_po w=0.35 L=52.61 (générateur PDK de magic), sans anneau
load res_unit -silent
box 0 0 0 0
magic::gencell sky130::sky130_fd_pr__res_xhigh_po_0p35 xr0 l 52.61 w 0.35 nx 1 m 1 guard 0
select top cell
expand
puts "BBOX [box values]"
save res_unit
gds write res_unit.gds
quit -noprompt
