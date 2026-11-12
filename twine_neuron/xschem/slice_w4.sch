v {xschem version=3.4.8RC file_version=1.2}
G {}
K {}
V {}
S {}
E {}
C {ipin.sym} -400 -200 0 0 {name=p_D lab=D}
C {ipin.sym} -400 -100 0 0 {name=p_EN lab=EN}
C {opin.sym} 700 0 0 0 {name=p_OUT lab=OUT}
C {iopin.sym} -400 -300 0 0 {name=p_VDD lab=VDD}
C {iopin.sym} -400 100 0 0 {name=p_VSS lab=VSS}
C {sky130_fd_pr/pfet_01v8.sym} -200 -260 0 0 {name=MPI1 L=0.15 W=0.84 nf=1 mult=1 ad="expr('int((@nf + 1)/2) * @W / @nf * 0.29')" pd="expr('2*int((@nf + 1)/2) * (@W / @nf + 0.29)')" as="expr('int((@nf + 2)/2) * @W / @nf * 0.29')" ps="expr('2*int((@nf + 2)/2) * (@W / @nf + 0.29)')" nrd="expr('0.29 / @W ')" nrs="expr('0.29 / @W ')" sa=0 sb=0 sd=0 model=pfet_01v8 spiceprefix=X}
C {lab_pin.sym} -180 -230 0 0 {name=l1 sig_type=std_logic lab=DB}
C {lab_pin.sym} -220 -260 0 0 {name=l2 sig_type=std_logic lab=D}
C {lab_pin.sym} -180 -290 0 0 {name=l3 sig_type=std_logic lab=VDD}
C {lab_pin.sym} -180 -260 0 0 {name=l4 sig_type=std_logic lab=VDD}
C {sky130_fd_pr/nfet_01v8.sym} -200 -160 0 0 {name=MNI1 L=0.15 W=0.42 nf=1 mult=1 ad="expr('int((@nf + 1)/2) * @W / @nf * 0.29')" pd="expr('2*int((@nf + 1)/2) * (@W / @nf + 0.29)')" as="expr('int((@nf + 2)/2) * @W / @nf * 0.29')" ps="expr('2*int((@nf + 2)/2) * (@W / @nf + 0.29)')" nrd="expr('0.29 / @W ')" nrs="expr('0.29 / @W ')" sa=0 sb=0 sd=0 model=nfet_01v8 spiceprefix=X}
C {lab_pin.sym} -180 -190 0 0 {name=l5 sig_type=std_logic lab=DB}
C {lab_pin.sym} -220 -160 0 0 {name=l6 sig_type=std_logic lab=D}
C {lab_pin.sym} -180 -130 0 0 {name=l7 sig_type=std_logic lab=VSS}
C {lab_pin.sym} -180 -160 0 0 {name=l8 sig_type=std_logic lab=VSS}
C {sky130_fd_pr/pfet_01v8.sym} -200 40 0 0 {name=MPI2 L=0.15 W=0.84 nf=1 mult=1 ad="expr('int((@nf + 1)/2) * @W / @nf * 0.29')" pd="expr('2*int((@nf + 1)/2) * (@W / @nf + 0.29)')" as="expr('int((@nf + 2)/2) * @W / @nf * 0.29')" ps="expr('2*int((@nf + 2)/2) * (@W / @nf + 0.29)')" nrd="expr('0.29 / @W ')" nrs="expr('0.29 / @W ')" sa=0 sb=0 sd=0 model=pfet_01v8 spiceprefix=X}
C {lab_pin.sym} -180 70 0 0 {name=l9 sig_type=std_logic lab=ENB}
C {lab_pin.sym} -220 40 0 0 {name=l10 sig_type=std_logic lab=EN}
C {lab_pin.sym} -180 10 0 0 {name=l11 sig_type=std_logic lab=VDD}
C {lab_pin.sym} -180 40 0 0 {name=l12 sig_type=std_logic lab=VDD}
C {sky130_fd_pr/nfet_01v8.sym} -200 140 0 0 {name=MNI2 L=0.15 W=0.42 nf=1 mult=1 ad="expr('int((@nf + 1)/2) * @W / @nf * 0.29')" pd="expr('2*int((@nf + 1)/2) * (@W / @nf + 0.29)')" as="expr('int((@nf + 2)/2) * @W / @nf * 0.29')" ps="expr('2*int((@nf + 2)/2) * (@W / @nf + 0.29)')" nrd="expr('0.29 / @W ')" nrs="expr('0.29 / @W ')" sa=0 sb=0 sd=0 model=nfet_01v8 spiceprefix=X}
C {lab_pin.sym} -180 110 0 0 {name=l13 sig_type=std_logic lab=ENB}
C {lab_pin.sym} -220 140 0 0 {name=l14 sig_type=std_logic lab=EN}
C {lab_pin.sym} -180 170 0 0 {name=l15 sig_type=std_logic lab=VSS}
C {lab_pin.sym} -180 140 0 0 {name=l16 sig_type=std_logic lab=VSS}
C {sky130_fd_pr/pfet_01v8.sym} 100 -240 0 0 {name=MP1 L=0.15 W=1 nf=1 mult=4 ad="expr('int((@nf + 1)/2) * @W / @nf * 0.29')" pd="expr('2*int((@nf + 1)/2) * (@W / @nf + 0.29)')" as="expr('int((@nf + 2)/2) * @W / @nf * 0.29')" ps="expr('2*int((@nf + 2)/2) * (@W / @nf + 0.29)')" nrd="expr('0.29 / @W ')" nrs="expr('0.29 / @W ')" sa=0 sb=0 sd=0 model=pfet_01v8 spiceprefix=X}
C {lab_pin.sym} 120 -210 0 0 {name=l17 sig_type=std_logic lab=NP1}
C {lab_pin.sym} 80 -240 0 0 {name=l18 sig_type=std_logic lab=DB}
C {lab_pin.sym} 120 -270 0 0 {name=l19 sig_type=std_logic lab=VDD}
C {lab_pin.sym} 120 -240 0 0 {name=l20 sig_type=std_logic lab=VDD}
C {sky130_fd_pr/pfet_01v8.sym} 100 -140 0 0 {name=MP2 L=0.15 W=1 nf=1 mult=4 ad="expr('int((@nf + 1)/2) * @W / @nf * 0.29')" pd="expr('2*int((@nf + 1)/2) * (@W / @nf + 0.29)')" as="expr('int((@nf + 2)/2) * @W / @nf * 0.29')" ps="expr('2*int((@nf + 2)/2) * (@W / @nf + 0.29)')" nrd="expr('0.29 / @W ')" nrs="expr('0.29 / @W ')" sa=0 sb=0 sd=0 model=pfet_01v8 spiceprefix=X}
C {lab_pin.sym} 120 -110 0 0 {name=l21 sig_type=std_logic lab=DRV}
C {lab_pin.sym} 80 -140 0 0 {name=l22 sig_type=std_logic lab=ENB}
C {lab_pin.sym} 120 -170 0 0 {name=l23 sig_type=std_logic lab=NP1}
C {lab_pin.sym} 120 -140 0 0 {name=l24 sig_type=std_logic lab=VDD}
C {sky130_fd_pr/nfet_01v8.sym} 100 -40 0 0 {name=MN2 L=0.15 W=0.42 nf=1 mult=4 ad="expr('int((@nf + 1)/2) * @W / @nf * 0.29')" pd="expr('2*int((@nf + 1)/2) * (@W / @nf + 0.29)')" as="expr('int((@nf + 2)/2) * @W / @nf * 0.29')" ps="expr('2*int((@nf + 2)/2) * (@W / @nf + 0.29)')" nrd="expr('0.29 / @W ')" nrs="expr('0.29 / @W ')" sa=0 sb=0 sd=0 model=nfet_01v8 spiceprefix=X}
C {lab_pin.sym} 120 -70 0 0 {name=l25 sig_type=std_logic lab=DRV}
C {lab_pin.sym} 80 -40 0 0 {name=l26 sig_type=std_logic lab=EN}
C {lab_pin.sym} 120 -10 0 0 {name=l27 sig_type=std_logic lab=NN1}
C {lab_pin.sym} 120 -40 0 0 {name=l28 sig_type=std_logic lab=VSS}
C {sky130_fd_pr/nfet_01v8.sym} 100 60 0 0 {name=MN1 L=0.15 W=0.42 nf=1 mult=4 ad="expr('int((@nf + 1)/2) * @W / @nf * 0.29')" pd="expr('2*int((@nf + 1)/2) * (@W / @nf + 0.29)')" as="expr('int((@nf + 2)/2) * @W / @nf * 0.29')" ps="expr('2*int((@nf + 2)/2) * (@W / @nf + 0.29)')" nrd="expr('0.29 / @W ')" nrs="expr('0.29 / @W ')" sa=0 sb=0 sd=0 model=nfet_01v8 spiceprefix=X}
C {lab_pin.sym} 120 30 0 0 {name=l29 sig_type=std_logic lab=NN1}
C {lab_pin.sym} 80 60 0 0 {name=l30 sig_type=std_logic lab=DB}
C {lab_pin.sym} 120 90 0 0 {name=l31 sig_type=std_logic lab=VSS}
C {lab_pin.sym} 120 60 0 0 {name=l32 sig_type=std_logic lab=VSS}
C {sky130_fd_pr/res_xhigh_po_0p35.sym} 400 -100 0 0 {name=R1 L=52.61 model=res_xhigh_po_0p35 spiceprefix=X mult=1}
C {lab_pin.sym} 400 -130 0 0 {name=l33 sig_type=std_logic lab=DRV}
C {lab_pin.sym} 400 -70 0 0 {name=l34 sig_type=std_logic lab=OUT}
C {lab_pin.sym} 380 -100 0 0 {name=l35 sig_type=std_logic lab=VSS}
T {synapse_slice poids 4 Gu : 1 R_U en série x 1 en // ; driver x4} -400 -420 0 0 0.4 0.4 {}
