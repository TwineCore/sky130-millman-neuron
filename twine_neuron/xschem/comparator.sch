v {xschem version=3.4.8RC file_version=1.2}
G {}
K {}
V {}
S {}
E {}
C {ipin.sym} -600 0 0 0 {name=p_INP lab=INP}
C {ipin.sym} -600 50 0 0 {name=p_INN lab=INN}
C {ipin.sym} -600 100 0 0 {name=p_CLK lab=CLK}
C {opin.sym} -600 150 0 0 {name=p_Q lab=Q}
C {opin.sym} -600 200 0 0 {name=p_QB lab=QB}
C {iopin.sym} -600 250 0 0 {name=p_VDD lab=VDD}
C {iopin.sym} -600 300 0 0 {name=p_VSS lab=VSS}
C {sky130_fd_pr/nfet_01v8.sym} 0 400 0 0 {name=MT L=0.15 W=4 nf=1 mult=1 ad="expr('int((@nf + 1)/2) * @W / @nf * 0.29')" pd="expr('2*int((@nf + 1)/2) * (@W / @nf + 0.29)')" as="expr('int((@nf + 2)/2) * @W / @nf * 0.29')" ps="expr('2*int((@nf + 2)/2) * (@W / @nf + 0.29)')" nrd="expr('0.29 / @W ')" nrs="expr('0.29 / @W ')" sa=0 sb=0 sd=0 model=nfet_01v8 spiceprefix=X}
C {lab_pin.sym} 20 370 0 0 {name=l1 sig_type=std_logic lab=TAIL}
C {lab_pin.sym} -20 400 0 0 {name=l2 sig_type=std_logic lab=CLK}
C {lab_pin.sym} 20 430 0 0 {name=l3 sig_type=std_logic lab=VSS}
C {lab_pin.sym} 20 400 0 0 {name=l4 sig_type=std_logic lab=VSS}
C {sky130_fd_pr/nfet_01v8.sym} -150 300 0 0 {name=M1 L=1 W=6 nf=1 mult=2 ad="expr('int((@nf + 1)/2) * @W / @nf * 0.29')" pd="expr('2*int((@nf + 1)/2) * (@W / @nf + 0.29)')" as="expr('int((@nf + 2)/2) * @W / @nf * 0.29')" ps="expr('2*int((@nf + 2)/2) * (@W / @nf + 0.29)')" nrd="expr('0.29 / @W ')" nrs="expr('0.29 / @W ')" sa=0 sb=0 sd=0 model=nfet_01v8 spiceprefix=X}
C {lab_pin.sym} -130 270 0 0 {name=l5 sig_type=std_logic lab=XN}
C {lab_pin.sym} -170 300 0 0 {name=l6 sig_type=std_logic lab=INP}
C {lab_pin.sym} -130 330 0 0 {name=l7 sig_type=std_logic lab=TAIL}
C {lab_pin.sym} -130 300 0 0 {name=l8 sig_type=std_logic lab=VSS}
C {sky130_fd_pr/nfet_01v8.sym} 150 300 0 0 {name=M2 L=1 W=6 nf=1 mult=2 ad="expr('int((@nf + 1)/2) * @W / @nf * 0.29')" pd="expr('2*int((@nf + 1)/2) * (@W / @nf + 0.29)')" as="expr('int((@nf + 2)/2) * @W / @nf * 0.29')" ps="expr('2*int((@nf + 2)/2) * (@W / @nf + 0.29)')" nrd="expr('0.29 / @W ')" nrs="expr('0.29 / @W ')" sa=0 sb=0 sd=0 model=nfet_01v8 spiceprefix=X}
C {lab_pin.sym} 170 270 0 0 {name=l9 sig_type=std_logic lab=XP}
C {lab_pin.sym} 130 300 0 0 {name=l10 sig_type=std_logic lab=INN}
C {lab_pin.sym} 170 330 0 0 {name=l11 sig_type=std_logic lab=TAIL}
C {lab_pin.sym} 170 300 0 0 {name=l12 sig_type=std_logic lab=VSS}
C {sky130_fd_pr/nfet_01v8.sym} -150 180 0 0 {name=M3 L=0.15 W=2 nf=1 mult=1 ad="expr('int((@nf + 1)/2) * @W / @nf * 0.29')" pd="expr('2*int((@nf + 1)/2) * (@W / @nf + 0.29)')" as="expr('int((@nf + 2)/2) * @W / @nf * 0.29')" ps="expr('2*int((@nf + 2)/2) * (@W / @nf + 0.29)')" nrd="expr('0.29 / @W ')" nrs="expr('0.29 / @W ')" sa=0 sb=0 sd=0 model=nfet_01v8 spiceprefix=X}
C {lab_pin.sym} -130 150 0 0 {name=l13 sig_type=std_logic lab=OUTN}
C {lab_pin.sym} -170 180 0 0 {name=l14 sig_type=std_logic lab=OUTP}
C {lab_pin.sym} -130 210 0 0 {name=l15 sig_type=std_logic lab=XN}
C {lab_pin.sym} -130 180 0 0 {name=l16 sig_type=std_logic lab=VSS}
C {sky130_fd_pr/nfet_01v8.sym} 150 180 0 0 {name=M4 L=0.15 W=2 nf=1 mult=1 ad="expr('int((@nf + 1)/2) * @W / @nf * 0.29')" pd="expr('2*int((@nf + 1)/2) * (@W / @nf + 0.29)')" as="expr('int((@nf + 2)/2) * @W / @nf * 0.29')" ps="expr('2*int((@nf + 2)/2) * (@W / @nf + 0.29)')" nrd="expr('0.29 / @W ')" nrs="expr('0.29 / @W ')" sa=0 sb=0 sd=0 model=nfet_01v8 spiceprefix=X}
C {lab_pin.sym} 170 150 0 0 {name=l17 sig_type=std_logic lab=OUTP}
C {lab_pin.sym} 130 180 0 0 {name=l18 sig_type=std_logic lab=OUTN}
C {lab_pin.sym} 170 210 0 0 {name=l19 sig_type=std_logic lab=XP}
C {lab_pin.sym} 170 180 0 0 {name=l20 sig_type=std_logic lab=VSS}
C {sky130_fd_pr/pfet_01v8.sym} -150 60 0 0 {name=M5 L=0.15 W=2 nf=1 mult=1 ad="expr('int((@nf + 1)/2) * @W / @nf * 0.29')" pd="expr('2*int((@nf + 1)/2) * (@W / @nf + 0.29)')" as="expr('int((@nf + 2)/2) * @W / @nf * 0.29')" ps="expr('2*int((@nf + 2)/2) * (@W / @nf + 0.29)')" nrd="expr('0.29 / @W ')" nrs="expr('0.29 / @W ')" sa=0 sb=0 sd=0 model=pfet_01v8 spiceprefix=X}
C {lab_pin.sym} -130 90 0 0 {name=l21 sig_type=std_logic lab=OUTN}
C {lab_pin.sym} -170 60 0 0 {name=l22 sig_type=std_logic lab=OUTP}
C {lab_pin.sym} -130 30 0 0 {name=l23 sig_type=std_logic lab=VDD}
C {lab_pin.sym} -130 60 0 0 {name=l24 sig_type=std_logic lab=VDD}
C {sky130_fd_pr/pfet_01v8.sym} 150 60 0 0 {name=M6 L=0.15 W=2 nf=1 mult=1 ad="expr('int((@nf + 1)/2) * @W / @nf * 0.29')" pd="expr('2*int((@nf + 1)/2) * (@W / @nf + 0.29)')" as="expr('int((@nf + 2)/2) * @W / @nf * 0.29')" ps="expr('2*int((@nf + 2)/2) * (@W / @nf + 0.29)')" nrd="expr('0.29 / @W ')" nrs="expr('0.29 / @W ')" sa=0 sb=0 sd=0 model=pfet_01v8 spiceprefix=X}
C {lab_pin.sym} 170 90 0 0 {name=l25 sig_type=std_logic lab=OUTP}
C {lab_pin.sym} 130 60 0 0 {name=l26 sig_type=std_logic lab=OUTN}
C {lab_pin.sym} 170 30 0 0 {name=l27 sig_type=std_logic lab=VDD}
C {lab_pin.sym} 170 60 0 0 {name=l28 sig_type=std_logic lab=VDD}
C {sky130_fd_pr/pfet_01v8.sym} -350 60 0 0 {name=S1 L=0.15 W=1 nf=1 mult=1 ad="expr('int((@nf + 1)/2) * @W / @nf * 0.29')" pd="expr('2*int((@nf + 1)/2) * (@W / @nf + 0.29)')" as="expr('int((@nf + 2)/2) * @W / @nf * 0.29')" ps="expr('2*int((@nf + 2)/2) * (@W / @nf + 0.29)')" nrd="expr('0.29 / @W ')" nrs="expr('0.29 / @W ')" sa=0 sb=0 sd=0 model=pfet_01v8 spiceprefix=X}
C {lab_pin.sym} -330 90 0 0 {name=l29 sig_type=std_logic lab=OUTN}
C {lab_pin.sym} -370 60 0 0 {name=l30 sig_type=std_logic lab=CLK}
C {lab_pin.sym} -330 30 0 0 {name=l31 sig_type=std_logic lab=VDD}
C {lab_pin.sym} -330 60 0 0 {name=l32 sig_type=std_logic lab=VDD}
C {sky130_fd_pr/pfet_01v8.sym} 350 60 0 0 {name=S2 L=0.15 W=1 nf=1 mult=1 ad="expr('int((@nf + 1)/2) * @W / @nf * 0.29')" pd="expr('2*int((@nf + 1)/2) * (@W / @nf + 0.29)')" as="expr('int((@nf + 2)/2) * @W / @nf * 0.29')" ps="expr('2*int((@nf + 2)/2) * (@W / @nf + 0.29)')" nrd="expr('0.29 / @W ')" nrs="expr('0.29 / @W ')" sa=0 sb=0 sd=0 model=pfet_01v8 spiceprefix=X}
C {lab_pin.sym} 370 90 0 0 {name=l33 sig_type=std_logic lab=OUTP}
C {lab_pin.sym} 330 60 0 0 {name=l34 sig_type=std_logic lab=CLK}
C {lab_pin.sym} 370 30 0 0 {name=l35 sig_type=std_logic lab=VDD}
C {lab_pin.sym} 370 60 0 0 {name=l36 sig_type=std_logic lab=VDD}
C {sky130_fd_pr/pfet_01v8.sym} -350 200 0 0 {name=S3 L=0.15 W=1 nf=1 mult=1 ad="expr('int((@nf + 1)/2) * @W / @nf * 0.29')" pd="expr('2*int((@nf + 1)/2) * (@W / @nf + 0.29)')" as="expr('int((@nf + 2)/2) * @W / @nf * 0.29')" ps="expr('2*int((@nf + 2)/2) * (@W / @nf + 0.29)')" nrd="expr('0.29 / @W ')" nrs="expr('0.29 / @W ')" sa=0 sb=0 sd=0 model=pfet_01v8 spiceprefix=X}
C {lab_pin.sym} -330 230 0 0 {name=l37 sig_type=std_logic lab=XN}
C {lab_pin.sym} -370 200 0 0 {name=l38 sig_type=std_logic lab=CLK}
C {lab_pin.sym} -330 170 0 0 {name=l39 sig_type=std_logic lab=VDD}
C {lab_pin.sym} -330 200 0 0 {name=l40 sig_type=std_logic lab=VDD}
C {sky130_fd_pr/pfet_01v8.sym} 350 200 0 0 {name=S4 L=0.15 W=1 nf=1 mult=1 ad="expr('int((@nf + 1)/2) * @W / @nf * 0.29')" pd="expr('2*int((@nf + 1)/2) * (@W / @nf + 0.29)')" as="expr('int((@nf + 2)/2) * @W / @nf * 0.29')" ps="expr('2*int((@nf + 2)/2) * (@W / @nf + 0.29)')" nrd="expr('0.29 / @W ')" nrs="expr('0.29 / @W ')" sa=0 sb=0 sd=0 model=pfet_01v8 spiceprefix=X}
C {lab_pin.sym} 370 230 0 0 {name=l41 sig_type=std_logic lab=XP}
C {lab_pin.sym} 330 200 0 0 {name=l42 sig_type=std_logic lab=CLK}
C {lab_pin.sym} 370 170 0 0 {name=l43 sig_type=std_logic lab=VDD}
C {lab_pin.sym} 370 200 0 0 {name=l44 sig_type=std_logic lab=VDD}
C {sky130_fd_pr/pfet_01v8.sym} 600 -250 0 0 {name=PBN L=0.15 W=0.84 nf=1 mult=1 ad="expr('int((@nf + 1)/2) * @W / @nf * 0.29')" pd="expr('2*int((@nf + 1)/2) * (@W / @nf + 0.29)')" as="expr('int((@nf + 2)/2) * @W / @nf * 0.29')" ps="expr('2*int((@nf + 2)/2) * (@W / @nf + 0.29)')" nrd="expr('0.29 / @W ')" nrs="expr('0.29 / @W ')" sa=0 sb=0 sd=0 model=pfet_01v8 spiceprefix=X}
C {lab_pin.sym} 620 -220 0 0 {name=l45 sig_type=std_logic lab=SN}
C {lab_pin.sym} 580 -250 0 0 {name=l46 sig_type=std_logic lab=OUTN}
C {lab_pin.sym} 620 -280 0 0 {name=l47 sig_type=std_logic lab=VDD}
C {lab_pin.sym} 620 -250 0 0 {name=l48 sig_type=std_logic lab=VDD}
C {sky130_fd_pr/nfet_01v8.sym} 600 -130 0 0 {name=NBN L=0.15 W=0.42 nf=1 mult=1 ad="expr('int((@nf + 1)/2) * @W / @nf * 0.29')" pd="expr('2*int((@nf + 1)/2) * (@W / @nf + 0.29)')" as="expr('int((@nf + 2)/2) * @W / @nf * 0.29')" ps="expr('2*int((@nf + 2)/2) * (@W / @nf + 0.29)')" nrd="expr('0.29 / @W ')" nrs="expr('0.29 / @W ')" sa=0 sb=0 sd=0 model=nfet_01v8 spiceprefix=X}
C {lab_pin.sym} 620 -160 0 0 {name=l49 sig_type=std_logic lab=SN}
C {lab_pin.sym} 580 -130 0 0 {name=l50 sig_type=std_logic lab=OUTN}
C {lab_pin.sym} 620 -100 0 0 {name=l51 sig_type=std_logic lab=VSS}
C {lab_pin.sym} 620 -130 0 0 {name=l52 sig_type=std_logic lab=VSS}
C {sky130_fd_pr/pfet_01v8.sym} 750 -250 0 0 {name=PBP L=0.15 W=0.84 nf=1 mult=1 ad="expr('int((@nf + 1)/2) * @W / @nf * 0.29')" pd="expr('2*int((@nf + 1)/2) * (@W / @nf + 0.29)')" as="expr('int((@nf + 2)/2) * @W / @nf * 0.29')" ps="expr('2*int((@nf + 2)/2) * (@W / @nf + 0.29)')" nrd="expr('0.29 / @W ')" nrs="expr('0.29 / @W ')" sa=0 sb=0 sd=0 model=pfet_01v8 spiceprefix=X}
C {lab_pin.sym} 770 -220 0 0 {name=l53 sig_type=std_logic lab=RP}
C {lab_pin.sym} 730 -250 0 0 {name=l54 sig_type=std_logic lab=OUTP}
C {lab_pin.sym} 770 -280 0 0 {name=l55 sig_type=std_logic lab=VDD}
C {lab_pin.sym} 770 -250 0 0 {name=l56 sig_type=std_logic lab=VDD}
C {sky130_fd_pr/nfet_01v8.sym} 750 -130 0 0 {name=NBP L=0.15 W=0.42 nf=1 mult=1 ad="expr('int((@nf + 1)/2) * @W / @nf * 0.29')" pd="expr('2*int((@nf + 1)/2) * (@W / @nf + 0.29)')" as="expr('int((@nf + 2)/2) * @W / @nf * 0.29')" ps="expr('2*int((@nf + 2)/2) * (@W / @nf + 0.29)')" nrd="expr('0.29 / @W ')" nrs="expr('0.29 / @W ')" sa=0 sb=0 sd=0 model=nfet_01v8 spiceprefix=X}
C {lab_pin.sym} 770 -160 0 0 {name=l57 sig_type=std_logic lab=RP}
C {lab_pin.sym} 730 -130 0 0 {name=l58 sig_type=std_logic lab=OUTP}
C {lab_pin.sym} 770 -100 0 0 {name=l59 sig_type=std_logic lab=VSS}
C {lab_pin.sym} 770 -130 0 0 {name=l60 sig_type=std_logic lab=VSS}
C {sky130_fd_pr/pfet_01v8.sym} 950 -250 0 0 {name=PA1 L=0.15 W=1 nf=1 mult=1 ad="expr('int((@nf + 1)/2) * @W / @nf * 0.29')" pd="expr('2*int((@nf + 1)/2) * (@W / @nf + 0.29)')" as="expr('int((@nf + 2)/2) * @W / @nf * 0.29')" ps="expr('2*int((@nf + 2)/2) * (@W / @nf + 0.29)')" nrd="expr('0.29 / @W ')" nrs="expr('0.29 / @W ')" sa=0 sb=0 sd=0 model=pfet_01v8 spiceprefix=X}
C {lab_pin.sym} 970 -220 0 0 {name=l61 sig_type=std_logic lab=TA}
C {lab_pin.sym} 930 -250 0 0 {name=l62 sig_type=std_logic lab=RP}
C {lab_pin.sym} 970 -280 0 0 {name=l63 sig_type=std_logic lab=VDD}
C {lab_pin.sym} 970 -250 0 0 {name=l64 sig_type=std_logic lab=VDD}
C {sky130_fd_pr/pfet_01v8.sym} 950 -130 0 0 {name=PA2 L=0.15 W=1 nf=1 mult=1 ad="expr('int((@nf + 1)/2) * @W / @nf * 0.29')" pd="expr('2*int((@nf + 1)/2) * (@W / @nf + 0.29)')" as="expr('int((@nf + 2)/2) * @W / @nf * 0.29')" ps="expr('2*int((@nf + 2)/2) * (@W / @nf + 0.29)')" nrd="expr('0.29 / @W ')" nrs="expr('0.29 / @W ')" sa=0 sb=0 sd=0 model=pfet_01v8 spiceprefix=X}
C {lab_pin.sym} 970 -100 0 0 {name=l65 sig_type=std_logic lab=Q}
C {lab_pin.sym} 930 -130 0 0 {name=l66 sig_type=std_logic lab=QB}
C {lab_pin.sym} 970 -160 0 0 {name=l67 sig_type=std_logic lab=TA}
C {lab_pin.sym} 970 -130 0 0 {name=l68 sig_type=std_logic lab=VDD}
C {sky130_fd_pr/nfet_01v8.sym} 950 0 0 0 {name=NA1 L=0.15 W=0.5 nf=1 mult=1 ad="expr('int((@nf + 1)/2) * @W / @nf * 0.29')" pd="expr('2*int((@nf + 1)/2) * (@W / @nf + 0.29)')" as="expr('int((@nf + 2)/2) * @W / @nf * 0.29')" ps="expr('2*int((@nf + 2)/2) * (@W / @nf + 0.29)')" nrd="expr('0.29 / @W ')" nrs="expr('0.29 / @W ')" sa=0 sb=0 sd=0 model=nfet_01v8 spiceprefix=X}
C {lab_pin.sym} 970 -30 0 0 {name=l69 sig_type=std_logic lab=Q}
C {lab_pin.sym} 930 0 0 0 {name=l70 sig_type=std_logic lab=RP}
C {lab_pin.sym} 970 30 0 0 {name=l71 sig_type=std_logic lab=VSS}
C {lab_pin.sym} 970 0 0 0 {name=l72 sig_type=std_logic lab=VSS}
C {sky130_fd_pr/nfet_01v8.sym} 1070 0 0 0 {name=NA2 L=0.15 W=0.5 nf=1 mult=1 ad="expr('int((@nf + 1)/2) * @W / @nf * 0.29')" pd="expr('2*int((@nf + 1)/2) * (@W / @nf + 0.29)')" as="expr('int((@nf + 2)/2) * @W / @nf * 0.29')" ps="expr('2*int((@nf + 2)/2) * (@W / @nf + 0.29)')" nrd="expr('0.29 / @W ')" nrs="expr('0.29 / @W ')" sa=0 sb=0 sd=0 model=nfet_01v8 spiceprefix=X}
C {lab_pin.sym} 1090 -30 0 0 {name=l73 sig_type=std_logic lab=Q}
C {lab_pin.sym} 1050 0 0 0 {name=l74 sig_type=std_logic lab=QB}
C {lab_pin.sym} 1090 30 0 0 {name=l75 sig_type=std_logic lab=VSS}
C {lab_pin.sym} 1090 0 0 0 {name=l76 sig_type=std_logic lab=VSS}
C {sky130_fd_pr/pfet_01v8.sym} 1250 -250 0 0 {name=PB1 L=0.15 W=1 nf=1 mult=1 ad="expr('int((@nf + 1)/2) * @W / @nf * 0.29')" pd="expr('2*int((@nf + 1)/2) * (@W / @nf + 0.29)')" as="expr('int((@nf + 2)/2) * @W / @nf * 0.29')" ps="expr('2*int((@nf + 2)/2) * (@W / @nf + 0.29)')" nrd="expr('0.29 / @W ')" nrs="expr('0.29 / @W ')" sa=0 sb=0 sd=0 model=pfet_01v8 spiceprefix=X}
C {lab_pin.sym} 1270 -220 0 0 {name=l77 sig_type=std_logic lab=TB}
C {lab_pin.sym} 1230 -250 0 0 {name=l78 sig_type=std_logic lab=SN}
C {lab_pin.sym} 1270 -280 0 0 {name=l79 sig_type=std_logic lab=VDD}
C {lab_pin.sym} 1270 -250 0 0 {name=l80 sig_type=std_logic lab=VDD}
C {sky130_fd_pr/pfet_01v8.sym} 1250 -130 0 0 {name=PB2 L=0.15 W=1 nf=1 mult=1 ad="expr('int((@nf + 1)/2) * @W / @nf * 0.29')" pd="expr('2*int((@nf + 1)/2) * (@W / @nf + 0.29)')" as="expr('int((@nf + 2)/2) * @W / @nf * 0.29')" ps="expr('2*int((@nf + 2)/2) * (@W / @nf + 0.29)')" nrd="expr('0.29 / @W ')" nrs="expr('0.29 / @W ')" sa=0 sb=0 sd=0 model=pfet_01v8 spiceprefix=X}
C {lab_pin.sym} 1270 -100 0 0 {name=l81 sig_type=std_logic lab=QB}
C {lab_pin.sym} 1230 -130 0 0 {name=l82 sig_type=std_logic lab=Q}
C {lab_pin.sym} 1270 -160 0 0 {name=l83 sig_type=std_logic lab=TB}
C {lab_pin.sym} 1270 -130 0 0 {name=l84 sig_type=std_logic lab=VDD}
C {sky130_fd_pr/nfet_01v8.sym} 1250 0 0 0 {name=NB1 L=0.15 W=0.5 nf=1 mult=1 ad="expr('int((@nf + 1)/2) * @W / @nf * 0.29')" pd="expr('2*int((@nf + 1)/2) * (@W / @nf + 0.29)')" as="expr('int((@nf + 2)/2) * @W / @nf * 0.29')" ps="expr('2*int((@nf + 2)/2) * (@W / @nf + 0.29)')" nrd="expr('0.29 / @W ')" nrs="expr('0.29 / @W ')" sa=0 sb=0 sd=0 model=nfet_01v8 spiceprefix=X}
C {lab_pin.sym} 1270 -30 0 0 {name=l85 sig_type=std_logic lab=QB}
C {lab_pin.sym} 1230 0 0 0 {name=l86 sig_type=std_logic lab=SN}
C {lab_pin.sym} 1270 30 0 0 {name=l87 sig_type=std_logic lab=VSS}
C {lab_pin.sym} 1270 0 0 0 {name=l88 sig_type=std_logic lab=VSS}
C {sky130_fd_pr/nfet_01v8.sym} 1370 0 0 0 {name=NB2 L=0.15 W=0.5 nf=1 mult=1 ad="expr('int((@nf + 1)/2) * @W / @nf * 0.29')" pd="expr('2*int((@nf + 1)/2) * (@W / @nf + 0.29)')" as="expr('int((@nf + 2)/2) * @W / @nf * 0.29')" ps="expr('2*int((@nf + 2)/2) * (@W / @nf + 0.29)')" nrd="expr('0.29 / @W ')" nrs="expr('0.29 / @W ')" sa=0 sb=0 sd=0 model=nfet_01v8 spiceprefix=X}
C {lab_pin.sym} 1390 -30 0 0 {name=l89 sig_type=std_logic lab=QB}
C {lab_pin.sym} 1350 0 0 0 {name=l90 sig_type=std_logic lab=Q}
C {lab_pin.sym} 1390 30 0 0 {name=l91 sig_type=std_logic lab=VSS}
C {lab_pin.sym} 1390 0 0 0 {name=l92 sig_type=std_logic lab=VSS}
T {comparator : StrongARM NMOS (paire W*L = 12 um2) + tampons + latch SR NOR ; Q = 1 si INP > INN ; CLK = 1 : décision} -600 -300 0 0 0.4 0.4 {}
