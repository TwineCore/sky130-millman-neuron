#!/usr/bin/env python3
"""Capacités PEX totales des nœuds différentiels du comparateur, identifiés par topologie (noms anonymes) :
XN/XP = drains de la paire w=6 l=1 (grille VP/VM) ; OUTN/OUTP = drains des nfet w=2 l=0.15 de source XN/XP ;
SN/RP = sorties des inverseurs nfet w=0.42 de grille OUTN/OUTP ; Q/QB.
Usage : python3 pex/pex_pairs.py [pex/twine_neuron_pex.spice]  -> affichage + pex/pex_pairs.csv"""
import collections, csv, os, re, sys
P = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "twine_neuron_pex.spice")
U = {"f": 1e-15, "p": 1e-12, "a": 1e-18}
base = lambda n: re.split(r"\.(t|n)\d+$", n)[0]
val = lambda s: float(s[:-1]) * U[s[-1]] if s[-1] in U else float(s)
cap, mos, cc = collections.Counter(), [], collections.Counter()
for l in open(P):
    f = l.split()
    if l.startswith("C"):
        for n in f[1:3]:
            cap[base(n)] += val(f[3])
        cc[frozenset((base(f[1]), base(f[2])))] += val(f[3])
    elif l.startswith("X") and "fet_01v8" in l:
        kv = dict(x.split("=") for x in f[6:] if "=" in x)
        mos.append(dict(d=base(f[1]), g=base(f[2]), s=base(f[3]), w=float(kv["w"]), l=float(kv["l"]), t=f[5]))
pair = [m for m in mos if m["w"] == 6 and m["l"] == 1]
tail = collections.Counter(n for m in pair for n in (m["d"], m["s"])).most_common(1)[0][0]
nd = {}
for m in pair:
    nd["XN" if m["g"] == "VP" else "XP"] = m["s"] if m["d"] == tail else m["d"]
for m in mos:
    if "nfet" in m["t"] and m["w"] == 2 and m["l"] == 0.15:
        for k, o in (("XN", "OUTN"), ("XP", "OUTP")):
            if nd.get(k) in (m["s"], m["d"]):
                nd[o] = m["d"] if m["s"] == nd[k] else m["s"]
for m in mos:
    if "nfet" in m["t"] and m["w"] == 0.42:
        for k, o in (("OUTN", "SN"), ("OUTP", "RP")):
            if m["g"] == nd.get(k):
                nd[o] = m["d"] if m["s"].startswith("VSS") else m["s"]
nd["Q"], nd["QB"] = "Q", "QB"
rows = []
for a, b in (("XN", "XP"), ("OUTN", "OUTP"), ("SN", "RP"), ("Q", "QB")):
    ca, cb = cap[nd.get(a)] * 1e15, cap[nd.get(b)] * 1e15
    rows.append(dict(pair=f"{a}/{b}", net_a=nd.get(a), C_a_fF=round(ca, 3), net_b=nd.get(b), C_b_fF=round(cb, 3),
                     dC_fF=round(ca - cb, 3), dC_rel_pct=round(100 * (ca - cb) / max(ca, cb), 2)))
    print(f"{a:5s}/{b:5s} {ca:8.3f} / {cb:8.3f} fF   Δ = {ca-cb:+.3f} fF ({rows[-1]['dC_rel_pct']:+.1f} %)")
# couplages vers les agresseurs communs (phase 6 : l'injection asymétrique de CLK causait l'offset post-layout)
nd["CLK"], nd["VP"], nd["VM"], nd["TAIL"] = "CLK", "VP", "VM", tail
for a, b in (("XN", "XP"), ("OUTN", "OUTP"), ("SN", "RP"), ("Q", "QB")):
    for ag in ("CLK", "TAIL"):
        ca, cb = (cc[frozenset((nd.get(x), nd[ag]))] * 1e15 for x in (a, b))
        rows.append(dict(pair=f"{a}/{b}<-{ag}", net_a=nd.get(a), C_a_fF=round(ca, 3), net_b=nd.get(b),
                         C_b_fF=round(cb, 3), dC_fF=round(ca - cb, 3),
                         dC_rel_pct=round(100 * (ca - cb) / max(ca, cb, 1e-9), 2)))
        print(f"  C({ag:4s}-{a}) / C({ag}-{b}) {ca:6.3f} / {cb:6.3f} fF   Δ = {ca-cb:+.3f} fF")
with open(os.path.join(os.path.dirname(P), "pex_pairs.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
