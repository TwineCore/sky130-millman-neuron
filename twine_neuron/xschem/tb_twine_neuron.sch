v {xschem version=3.4.8RC file_version=1.2}
G {}
K {}
V {}
S {}
E {}
C {twine_neuron.sym} 0 0 0 0 {name=XDUT}
C {lab_pin.sym} -80 -280 0 0 {name=l1 sig_type=std_logic lab=dp1}
C {lab_pin.sym} -80 -260 0 0 {name=l2 sig_type=std_logic lab=dp2}
C {lab_pin.sym} -80 -240 0 0 {name=l3 sig_type=std_logic lab=dp3}
C {lab_pin.sym} -80 -220 0 0 {name=l4 sig_type=std_logic lab=dp4}
C {lab_pin.sym} -80 -200 0 0 {name=l5 sig_type=std_logic lab=dm1}
C {lab_pin.sym} -80 -180 0 0 {name=l6 sig_type=std_logic lab=dm2}
C {lab_pin.sym} -80 -160 0 0 {name=l7 sig_type=std_logic lab=dm3}
C {lab_pin.sym} -80 -140 0 0 {name=l8 sig_type=std_logic lab=dm4}
C {lab_pin.sym} -80 -120 0 0 {name=l9 sig_type=std_logic lab=en1_0}
C {lab_pin.sym} -80 -100 0 0 {name=l10 sig_type=std_logic lab=en1_1}
C {lab_pin.sym} -80 -80 0 0 {name=l11 sig_type=std_logic lab=en1_2}
C {lab_pin.sym} -80 -60 0 0 {name=l12 sig_type=std_logic lab=en2_0}
C {lab_pin.sym} -80 -40 0 0 {name=l13 sig_type=std_logic lab=en2_1}
C {lab_pin.sym} -80 -20 0 0 {name=l14 sig_type=std_logic lab=en2_2}
C {lab_pin.sym} -80 0 0 0 {name=l15 sig_type=std_logic lab=en3_0}
C {lab_pin.sym} -80 20 0 0 {name=l16 sig_type=std_logic lab=en3_1}
C {lab_pin.sym} -80 40 0 0 {name=l17 sig_type=std_logic lab=en3_2}
C {lab_pin.sym} -80 60 0 0 {name=l18 sig_type=std_logic lab=en4_0}
C {lab_pin.sym} -80 80 0 0 {name=l19 sig_type=std_logic lab=en4_1}
C {lab_pin.sym} -80 100 0 0 {name=l20 sig_type=std_logic lab=en4_2}
C {lab_pin.sym} -80 120 0 0 {name=l21 sig_type=std_logic lab=dbp}
C {lab_pin.sym} -80 140 0 0 {name=l22 sig_type=std_logic lab=dbm}
C {lab_pin.sym} -80 160 0 0 {name=l23 sig_type=std_logic lab=enb_0}
C {lab_pin.sym} -80 180 0 0 {name=l24 sig_type=std_logic lab=enb_1}
C {lab_pin.sym} -80 200 0 0 {name=l25 sig_type=std_logic lab=enb_2}
C {lab_pin.sym} -80 220 0 0 {name=l26 sig_type=std_logic lab=enb_3}
C {lab_pin.sym} -80 240 0 0 {name=l27 sig_type=std_logic lab=enb_4}
C {lab_pin.sym} -80 260 0 0 {name=l28 sig_type=std_logic lab=hen}
C {lab_pin.sym} -80 280 0 0 {name=l29 sig_type=std_logic lab=clk}
C {lab_pin.sym} 80 -280 0 0 {name=l30 sig_type=std_logic lab=q}
C {lab_pin.sym} 80 -260 0 0 {name=l31 sig_type=std_logic lab=qb}
C {lab_pin.sym} 80 -240 0 0 {name=l32 sig_type=std_logic lab=vp}
C {lab_pin.sym} 80 -220 0 0 {name=l33 sig_type=std_logic lab=vm}
C {lab_pin.sym} -40 -320 0 0 {name=l34 sig_type=std_logic lab=vdd}
C {lab_pin.sym} 0 320 0 0 {name=l35 sig_type=std_logic lab=0}
C {code_shown.sym} -900 -600 0 0 {name=STIM only_toplevel=false value=".lib /foss/pdks/sky130A/libs.tech/ngspice/sky130.lib.spice tt
.include tb_stimuli.spice"}
T {tb_twine_neuron : stimuli et analyses générés par sim/tn.py dans netlist/tb_stimuli.spice} -900 -700 0 0 0.4 0.4 {}
