#!/usr/bin/env python3
"""Génère les schémas xschem hiérarchiques du neurone Millman (sky130A).

    python3 xschem/gen_xschem.py            -> xschem/*.sym, xschem/*.sch

Hiérarchie : slice_w{1,2,4,8,16}, slice_half (= synapse_slice paramétrées), millman_node,
comparator, twine_neuron (top), tb_twine_neuron (testbench xschem).
Connexions par labels : chaque pin d'instance reçoit un lab_pin placé sur ses coordonnées.
Toutes les dimensions sont ici (bloc SIZING) — itérations documentées dans LOG.md.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))

# ================================================================ SIZING (itération 1)
SIZING = dict(
    L_U=52.61,        # µm, unité R_U xhigh_po_0p35 (calc/out/model_summary.txt)
    G0_N=13,          # unités R_U en parallèle (G0 = 52 Gu)
    WN_DRV=0.42, WP_DRV=1.0, L_DRV=0.15,   # pile tri-state, multiplicité = poids (Ron/R constant)
    WN_INV=0.42, WP_INV=0.84,              # inverseurs internes (D->DB, EN->ENB)
    # comparateur StrongARM
    W_TAIL=4.0, L_TAIL=0.15,
    W_IN=6.0, L_IN=1.0, M_IN=2,            # W·L = 12 µm² par côté
    W_LN=2.0, W_LP=2.0, L_LAT=0.15,
    W_PRE=1.0,
    WN_SR=0.5, WP_SR=1.0,      # NOR (itération 1)
    WN_BUF=0.42, WP_BUF=0.84,  # tampons OUTP/OUTN (itération 1)
)
# réalisation des slices (n_série, n_parallèle, multiplicité driver)
SLICES = {"w1": (4, 1, 1), "w2": (2, 1, 2), "w4": (1, 1, 4), "w8": (1, 2, 8), "w16": (1, 4, 16), "half": (8, 1, 1)}

HDR = "v {xschem version=3.4.8RC file_version=1.2}\n"
PDK_PINS = {
    "sky130_fd_pr/nfet_01v8.sym": {"D": (20, -30), "G": (-20, 0), "S": (20, 30), "B": (20, 0)},
    "sky130_fd_pr/pfet_01v8.sym": {"D": (20, 30), "G": (-20, 0), "S": (20, -30), "B": (20, 0)},
    "sky130_fd_pr/res_xhigh_po_0p35.sym": {"P": (0, -30), "M": (0, 30), "B": (-20, 0)},
}
SYM_PINS = dict(PDK_PINS)


def fmt(v):
    return f"{v:g}"


class Sch:
    def __init__(self):
        self.body = []
        self.nlab = 0

    def label(self, x, y, net):
        self.nlab += 1
        self.body.append(f"C {{lab_pin.sym}} {fmt(x)} {fmt(y)} 0 0 {{name=l{self.nlab} sig_type=std_logic lab={net}}}")

    def inst(self, sym, x, y, props, conns):
        self.body.append(f"C {{{sym}}} {fmt(x)} {fmt(y)} 0 0 {{{props}}}")
        pins = SYM_PINS[sym]
        assert set(conns) == set(pins), (sym, conns.keys(), pins.keys())
        for p, net in conns.items():
            dx, dy = pins[p]
            self.label(x + dx, y + dy, net)

    def mos(self, kind, name, x, y, d, g, s, b, W, L, m=1):
        name = name[1:] if name.startswith("X") else name   # spiceprefix=X déjà ajouté par le symbole
        props = (f"name={name} L={fmt(L)} W={fmt(W)} nf=1 mult={m} "
                 f"ad=\"expr('int((@nf + 1)/2) * @W / @nf * 0.29')\" "
                 f"pd=\"expr('2*int((@nf + 1)/2) * (@W / @nf + 0.29)')\" "
                 f"as=\"expr('int((@nf + 2)/2) * @W / @nf * 0.29')\" "
                 f"ps=\"expr('2*int((@nf + 2)/2) * (@W / @nf + 0.29)')\" "
                 f"nrd=\"expr('0.29 / @W ')\" nrs=\"expr('0.29 / @W ')\" sa=0 sb=0 sd=0 "
                 f"model={kind}fet_01v8 spiceprefix=X")
        self.inst(f"sky130_fd_pr/{kind}fet_01v8.sym", x, y, props, {"D": d, "G": g, "S": s, "B": b})

    def res(self, name, x, y, p, m, b, L, mult=1):
        # ngspice ignore m=/mult= sur le sous-circuit res_xhigh_po (vérifié : sim/pdk_char/mult_check.spice),
        # donc chaque unité en parallèle est une instance distincte (aussi 1 instance = 1 unité en layout).
        name = name[1:] if name.startswith("X") else name
        for k in range(mult):
            nk = name if mult == 1 else f"{name}_{k}"
            props = f"name={nk} L={fmt(L)} model=res_xhigh_po_0p35 spiceprefix=X mult=1"
            self.inst("sky130_fd_pr/res_xhigh_po_0p35.sym", x + 40 * k, y + 160 * k, props, {"P": p, "M": m, "B": b})

    def port(self, kind, name, x, y):
        self.body.append(f"C {{{kind}.sym}} {fmt(x)} {fmt(y)} 0 0 {{name=p_{name} lab={name}}}")

    def text(self, s, x, y, size=0.4):
        self.body.append(f"T {{{s}}} {fmt(x)} {fmt(y)} 0 0 {size} {size} {{}}")

    def write(self, name, extra_g=""):
        with open(os.path.join(HERE, name + ".sch"), "w") as f:
            f.write(HDR + f"G {{{extra_g}}}\nK {{}}\nV {{}}\nS {{}}\nE {{}}\n" + "\n".join(self.body) + "\n")


def symbol(name, pins_in, pins_out, pins_io, title=None):
    """Symbole rectangulaire : entrées à gauche, sorties à droite, alims en haut/bas (pins_io)."""
    n = max(len(pins_in), len(pins_out), 1)
    h = 20 * n + 20
    w = 120
    pos, lines = {}, []
    lines.append(f"L 4 {-w/2} {-h/2} {w/2} {-h/2} {{}}")
    lines.append(f"L 4 {-w/2} {h/2} {w/2} {h/2} {{}}")
    lines.append(f"L 4 {-w/2} {-h/2} {-w/2} {h/2} {{}}")
    lines.append(f"L 4 {w/2} {-h/2} {w/2} {h/2} {{}}")
    boxes = []

    def pin(p, x, y, d, tx, ty, just):
        pos[p] = (x, y)
        boxes.append(f"B 5 {x-2.5} {y-2.5} {x+2.5} {y+2.5} {{name={p} dir={d}}}")
        lines.append(f"T {{{p}}} {tx} {ty} 0 {just} 0.2 0.2 {{}}")

    for i, p in enumerate(pins_in):
        y = -h / 2 + 20 + 20 * i
        pin(p, -w / 2 - 20, y, "in", -w / 2 + 4, y - 6, 0)
        lines.append(f"L 4 {-w/2-20} {y} {-w/2} {y} {{}}")
    for i, p in enumerate(pins_out):
        y = -h / 2 + 20 + 20 * i
        pin(p, w / 2 + 20, y, "out", w / 2 - 4, y - 6, 1)
        lines.append(f"L 4 {w/2} {y} {w/2+20} {y} {{}}")
    for i, p in enumerate(pins_io):
        x = -w / 2 + 20 + 40 * i
        y = -h / 2 - 20 if p.upper().startswith("VDD") else h / 2 + 20
        pin(p, x, y, "inout", x + 3, y + (4 if y < 0 else -16), 0)
        lines.append(f"L 4 {x} {y} {x} {(-h/2 if y < 0 else h/2)} {{}}")
    txt = [f"T {{@symname}} {-w/2} {-h/2-40} 0 0 0.3 0.3 {{}}", f"T {{@name}} {-w/2} {h/2+25} 0 0 0.25 0.25 {{}}"]
    if title:
        txt.append(f"T {{{title}}} {-w/2+4} {-h/2+2} 0 0 0.15 0.15 {{layer=13}}")
    with open(os.path.join(HERE, name + ".sym"), "w") as f:
        f.write(HDR + 'K {type=subcircuit\nformat="@name @pinlist @symname"\ntemplate="name=x1"\n}\n'
                "G {}\nV {}\nS {}\nE {}\n" + "\n".join(lines + boxes + txt) + "\n")
    SYM_PINS[name + ".sym"] = pos
    return pos


Z = SIZING

# ================================================================ synapse_slice (6 variantes)
for sname, (ns, npar, mdrv) in SLICES.items():
    cell = f"slice_{sname}"
    s = Sch()
    for p, k, x in (("D", "ipin", -400), ("EN", "ipin", -400), ("OUT", "opin", 700),
                    ("VDD", "iopin", -400), ("VSS", "iopin", -400)):
        s.port(k, p, x, {"D": -200, "EN": -100, "OUT": 0, "VDD": -300, "VSS": 100}[p])
    # inverseurs internes
    s.mos("p", "XMPI1", -200, -260, "DB", "D", "VDD", "VDD", Z["WP_INV"], Z["L_DRV"])
    s.mos("n", "XMNI1", -200, -160, "DB", "D", "VSS", "VSS", Z["WN_INV"], Z["L_DRV"])
    s.mos("p", "XMPI2", -200, 40, "ENB", "EN", "VDD", "VDD", Z["WP_INV"], Z["L_DRV"])
    s.mos("n", "XMNI2", -200, 140, "ENB", "EN", "VSS", "VSS", Z["WN_INV"], Z["L_DRV"])
    # pile tri-state : sortie = D quand EN = 1, Hi-Z sinon
    s.mos("p", "XMP1", 100, -240, "NP1", "DB", "VDD", "VDD", Z["WP_DRV"], Z["L_DRV"], mdrv)
    s.mos("p", "XMP2", 100, -140, "DRV", "ENB", "NP1", "VDD", Z["WP_DRV"], Z["L_DRV"], mdrv)
    s.mos("n", "XMN2", 100, -40, "DRV", "EN", "NN1", "VSS", Z["WN_DRV"], Z["L_DRV"], mdrv)
    s.mos("n", "XMN1", 100, 60, "NN1", "DB", "VSS", "VSS", Z["WN_DRV"], Z["L_DRV"], mdrv)
    # résistances : ns unités en série (ou npar en parallèle)
    nodes = ["DRV"] + [f"RN{i}" for i in range(1, ns)] + ["OUT"]
    for i in range(ns):
        s.res(f"XR{i+1}", 400 + 80 * i, -100, nodes[i], nodes[i + 1], "VSS", Z["L_U"], npar)
    w = {"half": "0.5", "w1": "1", "w2": "2", "w4": "4", "w8": "8", "w16": "16"}[sname]
    s.text(f"synapse_slice poids {w} Gu : {ns} R_U en série x {npar} en // ; driver x{mdrv}", -400, -420)
    s.write(cell)
    symbol(cell, ["D", "EN"], ["OUT"], ["VDD", "VSS"], title=f"w={w}")

# ================================================================ millman_node (G0)
s = Sch()
for p, k, y in (("NODE", "iopin", 0), ("VDD", "iopin", -100), ("VSS", "iopin", 100)):
    s.port(k, p, -300, y)
s.res("XRG0", 0, 0, "VDD", "NODE", "VSS", Z["L_U"], Z["G0_N"])
s.text(f"millman_node : G0 = {Z['G0_N']} R_U en // vers VDD ({4*Z['G0_N']} Gu), pas de capa explicite", -300, -250)
s.write("millman_node")
symbol("millman_node", [], ["NODE"], ["VDD", "VSS"], title="G0")

# ================================================================ comparateur StrongARM + SR
s = Sch()
for p, k, y in (("INP", "ipin", 0), ("INN", "ipin", 50), ("CLK", "ipin", 100), ("Q", "opin", 150),
                ("QB", "opin", 200), ("VDD", "iopin", 250), ("VSS", "iopin", 300)):
    s.port(k, p, -600, y)
s.mos("n", "XMT", 0, 400, "TAIL", "CLK", "VSS", "VSS", Z["W_TAIL"], Z["L_TAIL"])
s.mos("n", "XM1", -150, 300, "XN", "INP", "TAIL", "VSS", Z["W_IN"], Z["L_IN"], Z["M_IN"])
s.mos("n", "XM2", 150, 300, "XP", "INN", "TAIL", "VSS", Z["W_IN"], Z["L_IN"], Z["M_IN"])
s.mos("n", "XM3", -150, 180, "OUTN", "OUTP", "XN", "VSS", Z["W_LN"], Z["L_LAT"])
s.mos("n", "XM4", 150, 180, "OUTP", "OUTN", "XP", "VSS", Z["W_LN"], Z["L_LAT"])
s.mos("p", "XM5", -150, 60, "OUTN", "OUTP", "VDD", "VDD", Z["W_LP"], Z["L_LAT"])
s.mos("p", "XM6", 150, 60, "OUTP", "OUTN", "VDD", "VDD", Z["W_LP"], Z["L_LAT"])
s.mos("p", "XS1", -350, 60, "OUTN", "CLK", "VDD", "VDD", Z["W_PRE"], Z["L_LAT"])
s.mos("p", "XS2", 350, 60, "OUTP", "CLK", "VDD", "VDD", Z["W_PRE"], Z["L_LAT"])
s.mos("p", "XS3", -350, 200, "XN", "CLK", "VDD", "VDD", Z["W_PRE"], Z["L_LAT"])
s.mos("p", "XS4", 350, 200, "XP", "CLK", "VDD", "VDD", Z["W_PRE"], Z["L_LAT"])
# itération 1 : tampons inverseurs (charge symétrique et indépendante de l'état pendant le reset)
# puis latch SR en NOR : SN = !OUTN (monte si INP > INN), RP = !OUTP ; Q = NOR(RP, QB), QB = NOR(SN, Q)
for nm, a, o, x in (("N", "OUTN", "SN", 600), ("P", "OUTP", "RP", 750)):
    s.mos("p", f"XPB{nm}", x, -250, o, a, "VDD", "VDD", Z["WP_BUF"], Z["L_LAT"])
    s.mos("n", f"XNB{nm}", x, -130, o, a, "VSS", "VSS", Z["WN_BUF"], Z["L_LAT"])
for nm, a, b, o, x in (("A", "RP", "QB", "Q", 950), ("B", "SN", "Q", "QB", 1250)):
    s.mos("p", f"XP{nm}1", x, -250, f"T{nm}", a, "VDD", "VDD", Z["WP_SR"], Z["L_LAT"])
    s.mos("p", f"XP{nm}2", x, -130, o, b, f"T{nm}", "VDD", Z["WP_SR"], Z["L_LAT"])
    s.mos("n", f"XN{nm}1", x, 0, o, a, "VSS", "VSS", Z["WN_SR"], Z["L_LAT"])
    s.mos("n", f"XN{nm}2", x + 120, 0, o, b, "VSS", "VSS", Z["WN_SR"], Z["L_LAT"])
s.text("comparator : StrongARM NMOS (paire W*L = 12 um2) + tampons + latch SR NOR ; Q = 1 si INP > INN ; CLK = 1 : décision",
       -600, -300)
s.write("comparator")
symbol("comparator", ["INP", "INN", "CLK"], ["Q", "QB"], ["VDD", "VSS"], title="StrongARM+SR")

# ================================================================ top twine_neuron
TOP_IN = ([f"DP{i}" for i in range(1, 5)] + [f"DM{i}" for i in range(1, 5)] +
          [f"EN{i}_{k}" for i in range(1, 5) for k in range(3)] + ["DBP", "DBM"] +
          [f"ENB_{k}" for k in range(5)] + ["HEN", "CLK"])
TOP_OUT = ["Q", "QB", "VP", "VM"]
s = Sch()
for i, p in enumerate(TOP_IN):
    s.port("ipin", p, -1600, -800 + 30 * i)
for i, p in enumerate(TOP_OUT):
    s.port("opin", p, 1800, -800 + 30 * i)
s.port("iopin", "VDD", -1600, 400)
s.port("iopin", "VSS", -1600, 430)
y = -700
W_SL = ("w1", "w2", "w4")
for i in range(1, 5):
    for side, dnet, node in (("P", f"DP{i}", "VP"), ("M", f"DM{i}", "VM")):
        for k, sl in enumerate(W_SL):
            x = -1000 + 300 * k + (1000 if side == "M" else 0)
            s.inst(f"slice_{sl}.sym", x, y, f"name=XS{i}{side}{k}",
                   {"D": dnet, "EN": f"EN{i}_{k}", "OUT": node, "VDD": "VDD", "VSS": "VSS"})
    y += 160
for side, dnet, node in (("P", "DBP", "VP"), ("M", "DBM", "VM")):
    for k, sl in enumerate(("w1", "w2", "w4", "w8", "w16")):
        x = -1000 + 300 * k if side == "P" else -1000 + 300 * k
        s.inst(f"slice_{sl}.sym", x, y, f"name=XB{side}{k}",
               {"D": dnet, "EN": f"ENB_{k}", "OUT": node, "VDD": "VDD", "VSS": "VSS"})
    y += 160
# demi-LSB : V− piloté à 1, V+ piloté à 0
s.inst("slice_half.sym", -1000, y, "name=XHP", {"D": "VSS", "EN": "HEN", "OUT": "VP", "VDD": "VDD", "VSS": "VSS"})
s.inst("slice_half.sym", -700, y, "name=XHM", {"D": "VDD", "EN": "HEN", "OUT": "VM", "VDD": "VDD", "VSS": "VSS"})
s.inst("millman_node.sym", -300, y, "name=XG0P", {"NODE": "VP", "VDD": "VDD", "VSS": "VSS"})
s.inst("millman_node.sym", 0, y, "name=XG0M", {"NODE": "VM", "VDD": "VDD", "VSS": "VSS"})
s.inst("comparator.sym", 1400, -300, "name=XCMP",
       {"INP": "VP", "INN": "VM", "CLK": "CLK", "Q": "Q", "QB": "QB", "VDD": "VDD", "VSS": "VSS"})
s.text("twine_neuron : 4 synapses (bancs +/- 3 b, équilibrage par synapse), biais 5 b +/-, demi-LSB, G0 x2, comparateur",
       -1600, -900)
s.write("twine_neuron")
symbol("twine_neuron", TOP_IN, TOP_OUT, ["VDD", "VSS"], title="neurone Millman")

# ================================================================ testbench xschem (stimuli = fichier inclus)
s = Sch()
conn = {p: p.lower() for p in TOP_IN + TOP_OUT}
conn.update({"VDD": "vdd", "VSS": "0"})
s.inst("twine_neuron.sym", 0, 0, "name=XDUT", conn)
s.body.append('C {code_shown.sym} -900 -600 0 0 {name=STIM only_toplevel=false value="'
              '.lib /foss/pdks/sky130A/libs.tech/ngspice/sky130.lib.spice tt\n'
              '.include tb_stimuli.spice"}')
s.text("tb_twine_neuron : stimuli et analyses générés par sim/tn.py dans netlist/tb_stimuli.spice", -900, -700)
s.write("tb_twine_neuron")

print("xschem: généré", sorted(f for f in os.listdir(HERE) if f.endswith((".sch", ".sym"))))
