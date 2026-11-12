"""tn.py — bibliothèque de simulation du neurone Millman (s'exécute DANS le conteneur eda-tools).

- construit les testbenches autour du netlist xschem (netlist/twine_neuron.spice ou une netlist PEX)
- traduit un code (w[4], b, h, x[4]) en niveaux des broches de contrôle
- lance ngspice en batch, archive .spice/.log dans sim/out/, parse les lignes « RES k=v ... »
"""
import os
import re
import subprocess
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTD = os.path.join(ROOT, "sim", "out")
os.makedirs(OUTD, exist_ok=True)
LIB = "/foss/pdks/sky130A/libs.tech/ngspice/sky130.lib.spice"
NETLIST = os.path.join(ROOT, "netlist", "twine_neuron.spice")

VDD = 1.8
G0 = 52
WBITS = (1, 2, 4)
BBITS = (1, 2, 4, 8, 16)
T_EVAL = 100e-9          # période d'évaluation (10 MHz)
T_CLK_R = 85e-9          # front montant (itération 2 : 85 ns de stabilisation ; décision ≈ 0.5 ns)
T_CLK_F = 95e-9
T_SAMPLE = 92e-9         # échantillonnage de Q
TR = 0.2e-9              # fronts numériques


def subckt_pins(netlist=None, name="twine_neuron"):
    txt = open(netlist or NETLIST).read()
    m = re.search(rf"^\.subckt {name} (.*?)\n(?!\+)", txt, re.M | re.S)
    return m.group(1).replace("\n+", " ").split()


def levels(w, b, h, x, vdd=VDD):
    """Niveaux (V) des entrées de contrôle pour un code signé."""
    lv = {}
    for i in range(4):
        m = abs(int(w[i]))
        for k in range(3):
            lv[f"EN{i+1}_{k}"] = vdd * ((m >> k) & 1)
        lv[f"DP{i+1}"] = vdd * x[i] * (w[i] > 0)
        lv[f"DM{i+1}"] = vdd * x[i] * (w[i] < 0)
    for k in range(5):
        lv[f"ENB_{k}"] = vdd * ((abs(int(b)) >> k) & 1)
    lv["DBP"] = vdd * (b > 0)
    lv["DBM"] = vdd * (b < 0)
    lv["HEN"] = vdd * h
    return lv


def ideal(w, b, h, x, vdd=VDD, g0=G0):
    """Modèle de Millman idéal (identique à calc/millman_model.py)."""
    S = sum(abs(int(v)) for v in w) + abs(b) + 0.5 * h
    D = S + g0
    hp = g0 + sum(w[i] * x[i] for i in range(4) if w[i] > 0) + max(b, 0)
    hn = g0 + sum(-w[i] * x[i] for i in range(4) if w[i] < 0) + max(-b, 0) + 0.5 * h
    vp, vn = vdd * hp / D, vdd * hn / D
    return dict(vp=vp, vn=vn, dv=vp - vn, D=D, S=S, lsb=vdd / D,
                s=int(sum(w[i] * x[i] for i in range(4))) + b)


def header(title, corner="tt", temp=27, vdd=VDD, netlist=None):
    return (f"* {title}\n.lib {LIB} {corner}\n.include {netlist or NETLIST}\n.temp {temp}\n"
            f".option savecurrents=0\nVVDD vdd 0 {vdd}\n"
            # sans état initial, le point de polarisation DC tombe sur le point métastable du latch SR NOR
            # (Q = QB = 0.85 V, 24.5 µA de courant traversant : sim/out/dbg_leak.spice)
            f".nodeset v(q)=0 v(qb)={vdd}\n"
            # post-layout : nœuds internes flottants (piles tri-state coupées) -> non-convergence de .op
            # avec la netlist PEX ; rshunt 1e12 Ω (1.8 pA max, << I_LSB ≈ 1.5 µA) seulement si TN_RSHUNT
            # + nodeset V± : le modèle xhigh_po (coefficients en tension négatifs) admet une solution .op
            # parasite (V+ = −1760 V : sim/out/dbg_post_op.log) avec la netlist PEX
            + (f".option rshunt={os.environ['TN_RSHUNT']}\n.nodeset v(vp)={0.75*vdd:.3f} v(vm)={0.75*vdd:.3f}\n"
               if os.environ.get("TN_RSHUNT") else ""))


def dut_line(netlist=None, name="XDUT"):
    pins = subckt_pins(netlist)
    nets = ["vdd" if p == "VDD" else "0" if p == "VSS" else p.lower() for p in pins]
    return f"{name} " + " ".join(nets) + " twine_neuron\n"


CTRL = ([f"DP{i}" for i in range(1, 5)] + [f"DM{i}" for i in range(1, 5)] +
        [f"EN{i}_{k}" for i in range(1, 5) for k in range(3)] + ["DBP", "DBM"] +
        [f"ENB_{k}" for k in range(5)] + ["HEN"])


def dc_sources(lv, clk=0.0):
    s = "".join(f"V{p} {p.lower()} 0 DC {lv[p]:.4g}\n" for p in CTRL)
    return s + f"VCLK clk 0 DC {clk}\n"


def alters(lv):
    return "".join(f"alter @v{p.lower()}[dc] = {lv[p]:.4g}\n" for p in CTRL)


def pwl(points):
    """points = [(t, v), ...] constants par morceaux -> PWL avec fronts TR."""
    out, last = [], None
    for t, v in points:
        if last is None:
            out.append((0.0, v))
        elif v != last:
            out.append((t, last))
            out.append((t + TR, v))
        last = v
    return "PWL(" + " ".join(f"{t:.4e} {v:.4g}" for t, v in out) + ")"


def slot_sources(codes, vdd=VDD, t0=0.0):
    """codes = liste de (w, b, h, x) par période ; renvoie les sources PWL (contrôle + horloge)."""
    lvs = [levels(*c, vdd=vdd) for c in codes]
    s = ""
    for p in CTRL:
        s += f"V{p} {p.lower()} 0 " + pwl([(t0 + k * T_EVAL, lv[p]) for k, lv in enumerate(lvs)]) + "\n"
    ck = []
    for k in range(len(codes)):
        ck += [(t0 + k * T_EVAL, 0.0), (t0 + k * T_EVAL + T_CLK_R, vdd), (t0 + k * T_EVAL + T_CLK_F, 0.0)]
    s += "VCLK clk 0 " + pwl(ck) + "\n"
    return s


def run(text, name, timeout=3600, allow=()):
    sp = os.path.join(OUTD, name + ".spice")
    with open(sp, "w") as f:
        f.write(text)
    r = subprocess.run(["ngspice", "-b", sp], capture_output=True, text=True, cwd=OUTD, timeout=timeout)
    out = r.stdout + r.stderr
    with open(os.path.join(OUTD, name + ".log"), "w") as f:
        f.write(out)
    errs = [l for l in out.splitlines() if re.search(r"^Error|error:|Error on line", l, re.I)
            and not any(a in l for a in allow) and "no such variable" not in l]
    if errs:
        errs = errs[:5]
        raise RuntimeError(f"ngspice {name}: " + " | ".join(errs))
    return out


def parse_res(out):
    rows = []
    for l in out.splitlines():
        if l.startswith("RES "):
            rows.append({k: float(v) for k, v in (kv.split("=") for kv in l.split()[1:])})
    return rows


def wrdata(path):
    """Lit un fichier wrdata ngspice : colonnes (t, v1, t, v2, ...) -> (t, [v1, v2, ...])."""
    d = np.loadtxt(path)
    return d[:, 0], [d[:, j] for j in range(1, d.shape[1], 2)]
