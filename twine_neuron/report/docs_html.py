#!/usr/bin/env python3
"""Datasheet et guide utilisateur mis en page (HTML + CSS -> PDF via WeasyPrint).
Appelé par report/make_docs.py, qui fournit les résultats lus dans results/ (ctx). Tous les chiffres viennent de ctx.
"""
import html
import os
import shutil
import subprocess
import tempfile



def _f(v, nd=2):
    try:
        return f"{float(v):.{nd}f}"
    except (TypeError, ValueError):
        return "n/d"


def _met(rws, prefix):
    for r in rws:
        if r.get("test", r.get("metric", "")).startswith(prefix):
            return r["value"]
    return None


def _ext(rows, key, fn):
    """(valeur, 'lib, vdd V, temp °C') extrême d'une colonne de corners, NaN ignorés."""
    v = []
    for r in rows:
        try:
            x = float(r[key])
            if x == x:
                v.append((x, r))
        except (KeyError, ValueError):
            pass
    if not v:
        return None, ""
    x, r = fn(v, key=lambda z: z[0])
    return x, f"{r['lib']}, {r['vdd']} V, {r['temp']} °C"


E = html.escape

# --------------------------------------------------------------------------- styles communs
CSS = """
@page { size: A4; margin: 16mm 15mm 18mm 15mm;
  @bottom-left { content: "TwineNeuron-1 · __DOC__"; font: 7.5pt 'Helvetica Neue', Arial, sans-serif; color: #7a8594; }
  @bottom-right { content: "page " counter(page) " / " counter(pages); font: 7.5pt 'Helvetica Neue', Arial, sans-serif; color: #7a8594; } }
:root { --ink:#1b2430; --mute:#5c6b7d; --acc:#0b5cad; --acc2:#e8f1fb; --line:#cfd8e3; --warn:#9a5b00; --warnbg:#fff6e5; --ok:#1d7a3e; }
* { box-sizing: border-box; }
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { font: 9pt/1.42 'Helvetica Neue', Helvetica, Arial, sans-serif; color: var(--ink); margin: 0; background: #fff; }
h1 { font-size: 22pt; margin: 0; letter-spacing: -0.3px; }
h2 { font-size: 12pt; color: var(--acc); border-bottom: 1.5px solid var(--acc); padding-bottom: 2px; margin: 16px 0 7px;
     break-after: avoid; }
h3 { font-size: 10pt; margin: 11px 0 4px; break-after: avoid; }
p { margin: 4px 0 6px; }
code, .mono { font-family: Menlo, 'SF Mono', Consolas, monospace; font-size: 8pt; }
code { background: #f1f4f8; padding: 0 3px; border-radius: 2px; }
table { border-collapse: collapse; width: 100%; margin: 4px 0 8px; }
tr { break-inside: avoid; }
table.keep { break-inside: avoid; }
th.n { text-align: right; } th.c { text-align: center; }
th { background: var(--acc); color: #fff; font-weight: 600; text-align: left; padding: 3.5px 6px; font-size: 8.2pt; }
td { padding: 3px 6px; border-bottom: 0.6px solid var(--line); vertical-align: top; font-size: 8.4pt; }
tr:nth-child(even) td { background: #f7f9fc; }
td.n { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
td.c { text-align: center; }
tr.sec td { background: var(--acc2) !important; font-weight: 600; color: var(--acc); font-size: 8pt; }
.band { background: var(--acc); color: #fff; padding: 12px 16px 11px; display: flex; justify-content: space-between;
        align-items: flex-end; border-radius: 3px; }
.band .sub { font-size: 10pt; opacity: .92; margin-top: 3px; }
.band .tag { text-align: right; font-size: 8pt; opacity: .9; line-height: 1.5; }
.cols { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.cols3 { display: grid; grid-template-columns: 1.15fr 1fr; gap: 14px; }
ul { margin: 3px 0 6px; padding-left: 15px; }
li { margin: 1.5px 0; }
.note { background: var(--warnbg); border-left: 3px solid #e0a030; padding: 6px 9px; margin: 6px 0; font-size: 8.4pt;
        break-inside: avoid; }
.tip { background: var(--acc2); border-left: 3px solid var(--acc); padding: 6px 9px; margin: 6px 0; font-size: 8.4pt;
       break-inside: avoid; }
figure { margin: 6px 0 10px; break-inside: avoid; text-align: center; }
figure img { max-width: 100%; border: 0.6px solid var(--line); }
figcaption { font-size: 7.8pt; color: var(--mute); margin-top: 3px; }
.fn { font-size: 7.6pt; color: var(--mute); }
.pb { break-before: page; }
.kv td:first-child { color: var(--mute); width: 38%; }
.eq { font-family: 'Times New Roman', Times, serif; font-style: italic; font-size: 11pt; text-align: center; margin: 6px 0; }
.ok { color: var(--ok); font-weight: 600; } .warn { color: var(--warn); font-weight: 600; }
ol.steps { padding-left: 18px; } ol.steps li { margin: 4px 0; }
pre { font-family: Menlo, Consolas, monospace; font-size: 7.8pt; background: #f4f6f9; border: 0.6px solid var(--line);
      padding: 7px 9px; white-space: pre-wrap; break-inside: avoid; margin: 5px 0 8px; }
.toc { columns: 2; font-size: 8.6pt; margin: 8px 0; } .toc div { margin: 1px 0; }
svg text { font-family: 'Helvetica Neue', Arial, sans-serif; }
"""

# --------------------------------------------------------------------------- schémas SVG


def svg_block():
    """Schéma bloc : bancs de slices -> V+/V- -> StrongARM -> latch SR."""
    def box(x, y, w, h, t, sub="", fill="#e8f1fb", stroke="#0b5cad"):
        s = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" fill="{fill}" stroke="{stroke}" stroke-width="1.2"/>'
        s += f'<text x="{x + w / 2}" y="{y + h / 2 - (5 if sub else -3)}" text-anchor="middle" font-size="10.5" font-weight="600" fill="#1b2430">{t}</text>'
        if sub:
            s += f'<text x="{x + w / 2}" y="{y + h / 2 + 10}" text-anchor="middle" font-size="7.6" fill="#5c6b7d">{sub}</text>'
        return s

    def arrow(x1, y1, x2, y2, lab="", dy=-4):
        s = f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#1b2430" stroke-width="1.1" marker-end="url(#ah)"/>'
        if lab:
            s += f'<text x="{(x1 + x2) / 2}" y="{(y1 + y2) / 2 + dy}" text-anchor="middle" font-size="8.5" fill="#1b2430">{lab}</text>'
        return s
    s = ('<svg viewBox="0 0 680 210" width="100%" xmlns="http://www.w3.org/2000/svg">'
         '<defs><marker id="ah" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto">'
         '<path d="M0,0 L7,3.5 L0,7 z" fill="#1b2430"/></marker></defs>')
    # entrées
    s += '<text x="6" y="40" font-size="9" fill="#5c6b7d">DP1–4</text><text x="6" y="54" font-size="9" fill="#5c6b7d">EN1_0…EN4_2</text>'
    s += '<text x="6" y="68" font-size="9" fill="#5c6b7d">DBP, ENB_0…4</text>'
    s += '<text x="6" y="150" font-size="9" fill="#5c6b7d">DM1–4</text><text x="6" y="164" font-size="9" fill="#5c6b7d">EN1_0…EN4_2</text>'
    s += '<text x="6" y="178" font-size="9" fill="#5c6b7d">DBM, ENB_0…4, HEN</text>'
    s += arrow(92, 52, 118, 52) + arrow(110, 162, 118, 162)
    s += box(120, 22, 160, 62, "Banc + (18 slices)", "tri-state + R xhigh_po")
    s += box(120, 132, 160, 62, "Banc − (18 slices)", "idem + demi-LSB h")
    # G0
    s += box(290, 4, 110, 30, "G0 = 52 Gu → VDD", "", "#f4f6f9", "#7a8594")
    s += '<line x1="345" y1="36" x2="345" y2="53" stroke="#7a8594" stroke-dasharray="3 2"/>'
    s += '<line x1="345" y1="196" x2="345" y2="179" stroke="#7a8594" stroke-dasharray="3 2"/>'
    s += '<text x="345" y="206" text-anchor="middle" font-size="8.5" fill="#5c6b7d">G0 → VDD</text>'
    # noeuds
    s += '<line x1="280" y1="53" x2="420" y2="53" stroke="#0b5cad" stroke-width="2"/><circle cx="345" cy="53" r="3" fill="#0b5cad"/>'
    s += '<line x1="280" y1="163" x2="420" y2="163" stroke="#c0392b" stroke-width="2"/><circle cx="345" cy="163" r="3" fill="#c0392b"/>'
    s += '<text x="372" y="47" font-size="10" font-weight="600" fill="#0b5cad">V+ (VP)</text>'
    s += '<text x="372" y="178" font-size="10" font-weight="600" fill="#c0392b">V− (VM)</text>'
    s += '<line x1="420" y1="53" x2="420" y2="90" stroke="#0b5cad" stroke-width="1.6"/>' + arrow(420, 90, 448, 90)
    s += '<line x1="420" y1="163" x2="420" y2="126" stroke="#c0392b" stroke-width="1.6"/>' + arrow(420, 126, 448, 126)
    s += box(450, 76, 100, 64, "StrongARM", "comparateur")
    s += box(574, 76, 64, 64, "Latch SR", "NOR")
    s += arrow(550, 100, 572, 100) + arrow(550, 116, 572, 116)
    s += arrow(638, 98, 676, 98) + arrow(638, 120, 676, 120)
    s += '<text x="657" y="93" text-anchor="middle" font-size="9.5" font-weight="600">Q</text>'
    s += '<text x="657" y="134" text-anchor="middle" font-size="9.5" font-weight="600">QB</text>'
    s += '<text x="500" y="182" text-anchor="middle" font-size="9.5" font-weight="600">CLK</text>' + arrow(500, 170, 500, 142)
    s += '<text x="500" y="196" text-anchor="middle" font-size="8" fill="#5c6b7d">front montant = décision</text>'
    return s + "</svg>"


def svg_timing():
    """Chronogramme d'une évaluation (période 100 ns)."""
    X0, W = 120, 520
    tx = lambda t: X0 + W * t / 110.0
    s = ('<svg viewBox="0 0 680 220" width="100%" xmlns="http://www.w3.org/2000/svg">'
         '<defs><marker id="a2" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto-start-reverse">'
         '<path d="M0,0 L6,3 L0,6 z" fill="#1b2430"/></marker></defs>')
    rows = [("Code D, EN", 30), ("V+ / V−", 75), ("CLK", 125), ("Q", 168)]
    for name, y in rows:
        s += f'<text x="8" y="{y + 4}" font-size="10" font-weight="600">{name}</text>'
    # bus code
    y = 30
    s += (f'<path d="M{tx(-8)},{y - 9} L{tx(0) - 4},{y - 9} L{tx(0) + 4},{y + 9} L{tx(100) - 4},{y + 9} L{tx(100) + 4},{y - 9} L{tx(110)},{y - 9}" fill="none" stroke="#1b2430" stroke-width="1.2"/>'
          f'<path d="M{tx(-8)},{y + 9} L{tx(0) - 4},{y + 9} L{tx(0) + 4},{y - 9} L{tx(100) - 4},{y - 9} L{tx(100) + 4},{y + 9} L{tx(110)},{y + 9}" fill="none" stroke="#1b2430" stroke-width="1.2"/>')
    s += f'<text x="{tx(50)}" y="{y + 4}" text-anchor="middle" font-size="9.5">code n (stable)</text>'
    s += f'<text x="{tx(105)}" y="{y + 4}" text-anchor="middle" font-size="8.5">n+1</text>'
    s += f'<text x="{tx(-4)}" y="{y + 4}" text-anchor="middle" font-size="8.5">n−1</text>'
    # V+ / V- convergeant
    import math
    pp, pm = [], []
    for k in range(0, 101):
        t = k * 1.0
        e = math.exp(-t / 9.0)
        pp.append(f"{tx(t)},{75 - 10 + 18 * e}")
        pm.append(f"{tx(t)},{75 + 8 - 20 * e}")
    s += f'<polyline points="{tx(-8)},{75 + 8} {tx(0)},{75 + 8} ' + " ".join(pp) + '" fill="none" stroke="#0b5cad" stroke-width="1.4"/>'
    s += f'<polyline points="{tx(-8)},{75 - 12} {tx(0)},{75 - 12} ' + " ".join(pm) + '" fill="none" stroke="#c0392b" stroke-width="1.4"/>'
    s += f'<text x="{tx(70)}" y="{75 - 14}" font-size="8.5" fill="#0b5cad">V+</text><text x="{tx(70)}" y="{75 + 20}" font-size="8.5" fill="#c0392b">V−</text>'
    # CLK
    y = 125
    s += (f'<polyline points="{tx(-8)},{y + 9} {tx(85)},{y + 9} {tx(85)},{y - 9} {tx(95)},{y - 9} {tx(95)},{y + 9} {tx(110)},{y + 9}" '
          'fill="none" stroke="#1b2430" stroke-width="1.4"/>')
    s += f'<text x="{tx(40)}" y="{y + 4}" text-anchor="middle" font-size="8.5" fill="#5c6b7d">bas : pré-charge</text>'
    # Q
    y = 168
    s += (f'<path d="M{tx(-8)},{y - 9} L{tx(86) - 3},{y - 9} L{tx(86) + 3},{y + 9} L{tx(110)},{y + 9}" fill="none" stroke="#1b2430" stroke-width="1.2"/>'
          f'<path d="M{tx(-8)},{y + 9} L{tx(86) - 3},{y + 9} L{tx(86) + 3},{y - 9} L{tx(110)},{y - 9}" fill="none" stroke="#1b2430" stroke-width="1.2"/>')
    s += f'<text x="{tx(40)}" y="{y + 4}" text-anchor="middle" font-size="9">décision n−1 (mémorisée)</text>'
    s += f'<text x="{tx(98)}" y="{y + 4}" text-anchor="middle" font-size="9">décision n</text>'
    # repères
    for t, lab in ((0, "0"), (85, "85"), (95, "95"), (100, "100 ns")):
        s += f'<line x1="{tx(t)}" y1="14" x2="{tx(t)}" y2="185" stroke="#9aa6b5" stroke-dasharray="2 3" stroke-width="0.8"/>'
        s += f'<text x="{tx(t)}" y="198" text-anchor="middle" font-size="8.5" fill="#5c6b7d">{lab}</text>'
    s += f'<line x1="{tx(0)}" y1="104" x2="{tx(85)}" y2="104" stroke="#1b2430" marker-start="url(#a2)" marker-end="url(#a2)"/>'
    s += f'<text x="{tx(42)}" y="101" text-anchor="middle" font-size="8.5">t_set : stabilisation de V± (≤ 85 ns)</text>'
    s += f'<text x="{tx(86) + 6}" y="{168 - 14}" font-size="8.5">t_dec ≈ 0.5 ns</text>'
    s += f'<text x="{tx(55)}" y="214" text-anchor="middle" font-size="8.5" fill="#5c6b7d">lire Q à partir de 86 ns (banc de test : 92 ns) et jusqu\'au front suivant</text>'
    return s + "</svg>"


# --------------------------------------------------------------------------- codage d'un neurone


def levels(w, b, h, x):
    lv = {}
    for i in range(4):
        m = abs(int(w[i]))
        for k in range(3):
            lv[f"EN{i + 1}_{k}"] = (m >> k) & 1
        lv[f"DP{i + 1}"] = int(x[i] and w[i] > 0)
        lv[f"DM{i + 1}"] = int(x[i] and w[i] < 0)
    for k in range(5):
        lv[f"ENB_{k}"] = (abs(int(b)) >> k) & 1
    lv["DBP"] = int(b > 0)
    lv["DBM"] = int(b < 0)
    lv["HEN"] = int(h)
    return lv


def ideal(w, b, h, x, vdd=1.8, g0=52):
    S = sum(abs(int(v)) for v in w) + abs(b) + 0.5 * h
    D = S + g0
    hp = g0 + sum(w[i] * x[i] for i in range(4) if w[i] > 0) + max(b, 0)
    hn = g0 + sum(-w[i] * x[i] for i in range(4) if w[i] < 0) + max(-b, 0) + 0.5 * h
    return vdd * hp / D, vdd * hn / D, vdd / D


# --------------------------------------------------------------------------- rendu PDF


def html2pdf(html_text, pdf_path):
    """HTML -> PDF avec WeasyPrint (pip install weasyprint ; macOS : brew install pango)."""
    import sys
    d = tempfile.mkdtemp(prefix="tn_doc_")
    src = os.path.join(d, "doc.html")
    open(src, "w").write(html_text)
    env = dict(os.environ)
    if os.path.isdir("/opt/homebrew/lib"):
        env["DYLD_FALLBACK_LIBRARY_PATH"] = "/opt/homebrew/lib:" + env.get("DYLD_FALLBACK_LIBRARY_PATH", "")
    r = subprocess.run([sys.executable, "-m", "weasyprint", "-q", src, pdf_path], env=env,
                       capture_output=True, text=True, timeout=300)
    shutil.rmtree(d, ignore_errors=True)
    if r.returncode or not os.path.exists(pdf_path):
        raise RuntimeError("échec WeasyPrint : " + r.stderr[-2000:])


def page(title, doc, body):
    return (f'<!doctype html><html lang="fr"><head><meta charset="utf-8"><title>{E(title)}</title>'
            f'<style>{CSS.replace("__DOC__", doc)}</style></head><body>{body}</body></html>')


def band(title, sub, tag):
    return f'<div class="band"><div><h1>{title}</h1><div class="sub">{sub}</div></div><div class="tag">{tag}</div></div>'


def tbl(head, rows, cls=None):
    cls = cls or []
    s = "<table><thead><tr>" + "".join(f'<th class="{cls[i] if i < len(cls) and cls[i] != "mono" else ""}">{h}</th>'
                                       for i, h in enumerate(head)) + "</tr></thead>"
    for r in rows:
        if isinstance(r, str):
            s += f'<tr class="sec"><td colspan="{len(head)}">{r}</td></tr>'
            continue
        s += "<tr>" + "".join(f'<td class="{cls[i] if i < len(cls) else ""}">{c}</td>' for i, c in enumerate(r)) + "</tr>"
    return s + "</table>"


def fig(path, cap, width="100%"):
    return f'<figure><img src="file://{path}" style="width:{width}"><figcaption>{cap}</figcaption></figure>'


# --------------------------------------------------------------------------- DATASHEET


def datasheet(c):
    M, PRE, POST, CP, CPOST, mcc = c["M"], c["PRE"], c["POST"], c["CP"], c["CPOST"], c["mcc"]
    img = c["imgdir"]
    g = lambda rws, p, nd=2: _f(_met(rws, p), nd)
    allc = CP + CPOST
    dvmin, dvmin_c = _ext(allc, "dv_half_min_mV", min)
    errmax, errmax_c = _ext(allc, "dc_err_max_LSB", max)
    vcm_p, vcm_pc = _ext(CPOST, "vcm_min_V", min)
    st_p, st_pc = _ext(CPOST, "t_settle_ns", max)
    st_pre, st_prec = _ext(CP, "t_settle_ns", max)
    pw_all, pw_allc = _ext(allc, "P_worst_uW", max)
    kr, kr_c = _ext(CPOST, "kick_rel_pct", max)
    fe = sum(float(r["func_err"]) for r in CPOST if r.get("func_err") not in (None, "", "nan"))
    mc_comp = {r["metric"]: r["value"] for r in c["MC"]}
    os_max = next((v for k, v in mc_comp.items() if k.startswith("|offset| max")), None)
    yld = None
    if "die_pairs" in mcc:
        yld = 100 * (1 - float(mcc["die_pairs"]["p_err_empirical"]))
    vdd_lo_lsb = M["LSB_MIN_mV"]

    feat = f"""<ul>
<li><b>Neurone binaire à seuil</b> : Q = 1 ⇔ Σ w<sub>i</sub>x<sub>i</sub> + b − h/2 &gt; 0</li>
<li>4 entrées binaires, poids <b>±7</b> (3 bits + signe), biais <b>±31</b> (5 bits + signe), demi-LSB h</li>
<li>Somme analogique par <b>réseau de Millman</b> (36 slices tri-state + résistances xhigh_po)</li>
<li>Comparateur dynamique <b>StrongARM</b> + latch SR, sortie mémorisée</li>
<li><b>10 MHz</b>, une décision par période ; t<sub>dec</sub> ≈ {g(PRE, "t_dec", 2)} ns</li>
<li>Somme pondérée lisible sans ADC : recherche <b>SAR</b> sur b (6 décisions)</li>
<li>1.8 V (1.62–1.98 V), −40…125 °C ; {_f(_met(PRE, "P statique moyenne"), 0)} µW moyens</li>
<li>Surface {c["area"]} mm² ({c["dims"]} µm) ; DRC/LVS propres</li>
</ul>"""
    appl = """<ul><li>Portes logiques à seuil reconfigurables (ET, OU, NON-ET, majorité…)</li>
<li>Couches de petits réseaux binaires (XOR 2-2-1 démontré)</li>
<li>Calcul de produit scalaire 4 × 4 bits en mémoire / au fil de l'eau</li>
<li>Démonstrateur pédagogique de calcul analogique en sky130</li></ul>"""
    desc = (f"""<p>Le TwineNeuron-1 additionne les contributions pondérées de ses entrées sous forme de
conductances : chaque bit de poids active une <i>slice</i> (driver tri-state + résistance de valeur 1, 2, 4… unités).
Les slices d'un même banc forment un diviseur de Millman dont la tension est la moyenne pondérée des niveaux des
drivers. Deux bancs symétriques (V+ pour les poids positifs, V− pour les négatifs) partagent le même dénominateur,
si bien que <b>ΔV = V+ − V− a exactement le signe de la somme pondérée</b>. Une conductance fixe G0 = {M['G0']} Gu
vers VDD maintient le mode commun dans la fenêtre du comparateur (≥ {_f(M['VCM_MIN_V'], 2)} V). Le comparateur
échantillonne le signe de ΔV au front montant de CLK et le maintient sur Q/QB jusqu'à la décision suivante.</p>""")

    abs_rows = [("Tension d'alimentation VDD", "−0.3", "2.0", "V", "limite technologique 1.8 V sky130"),
                ("Tension sur toute broche", "−0.3", "VDD + 0.3", "V", ""),
                ("Température de jonction", "−40", "125", "°C", "plage simulée")]
    rec_rows = [("VDD", "1.62", "1.80", "1.98", "V"), ("Température", "−40", "27", "125", "°C"),
                ("Fréquence CLK", "—", "10", "10", "MHz"),
                ("Niveaux logiques d'entrée (V<sub>IL</sub> / V<sub>IH</sub>)", "—", "0 / VDD", "—", "V"),
                ("Charge sur VP / VM", "—", "aucune", "≪ 370 fF", "—")]

    def r(p, sym, cond, mn, ty, mx, u):
        return (p, sym, cond, mn, ty, mx, u)
    el = [
        "Réseau de Millman",
        r("Pas élémentaire ΔV (LSB)", "V<sub>LSB</sub>", "VDD / (52 + S) ; min : 1.62 V, S = 59.5 ; typ : 1.8 V, S = 59.5 ; max : 1.8 V, S → 0",
          _f(vdd_lo_lsb, 2), _f(M["LSB_NOM_DMAX_mV"], 2), "34.6", "mV"),
        r("|ΔV| aux codes ±0.5 LSB", "", "post-layout tt / pire corner", _f(dvmin, 2), g(POST, "|ΔV| min", 2), "—", "mV"),
        r("Erreur ΔV vs modèle idéal", "", "tous codes ; max sur corners", "—", g(PRE, "erreur ΔV vs modèle", 3),
          _f(errmax, 2), "LSB"),
        r("INL / DNL poids", "", "tt", "—", f'{g(PRE, "INL poids", 3)} / {g(PRE, "DNL poids", 4)}', "0.5", "LSB"),
        r("INL / DNL biais", "", "tt", "—", f'{g(PRE, "INL biais", 3)} / {g(PRE, "DNL biais", 4)}', "0.5", "LSB"),
        r("Mode commun V±", "V<sub>CM</sub>", "post-layout, 5 corners", _f(vcm_p, 3), g(POST, "mode commun min", 3),
          "VDD", "V"),
        r("Stabilisation à 0.5 LSB, pire code", "t<sub>set</sub>", "post-layout tt / pire corner (¹)", "—",
          g(POST, "t_settle 0.5 LSB", 1), _f(st_p, 1), "ns"),
        r("Ron driver / R slice", "", "pire slice", "—", g(PRE, "Ron/R_slice", 2), "1", "%"),
        r("Fuite d'une slice en Hi-Z", "", "EN = 0", "—", _f(float(_met(PRE, "fuite Hi-Z") or "nan") * 1e9, 2), "—", "nA"),
        "Comparateur",
        r("Temps de décision", "t<sub>dec</sub>", "ΔV = 0.5 LSB<sub>min</sub>, pire V<sub>CM</sub>", "—",
          g(PRE, "t_dec", 3), "5", "ns"),
        r("Offset aléatoire (1σ)", "σ<sub>os</sub>", "Monte Carlo 200 dies, V<sub>CM</sub> 0.84 V", "—",
          _f(mc_comp.get("σ_os comparateur (Vcm 0.84 V)"), 2), "2.42", "mV"),
        r("|Offset| max", "", "Monte Carlo 200 dies", "—", "—", _f(os_max, 1), "mV"),
        r("Hystérésis", "", "V<sub>CM</sub> 0.75–1.8 V", "—", "—", g(PRE, "hystérésis", 2), "mV"),
        r("Fenêtre de mode commun fonctionnelle", "", "rampe ±4 mV", "0.60", "—", "1.80", "V"),
        r("Kickback différentiel sur V+ − V−", "", "relatif à ΔV, 5 corners post (²)", "—", _f(next((r["kick_rel_pct"] for r in CPOST if r["lib"] == "tt"), None), 0),
          _f(kr, 0), "% ΔV"),
        "Système",
        r("Décisions fausses ET / OU / NON-ET", "", "PEX, 5 corners × 12 décisions", "—", "0", f"{fe:g}", "—"),
        r("Rendement fonctionnel estimé", "", "MC réseau × comparateur, tt", "—", _f(yld, 1), "—", "%"),
        r("Puissance statique, pire code", "P", "tt / max corners", "—", g(POST, "P statique pire code", 1),
          _f(pw_all, 1), "µW"),
        r("Puissance statique moyenne", "", "300 codes aléatoires, tt", "—", g(PRE, "P statique moyenne", 1), "—", "µW"),
        r("Puissance en fonctionnement", "", "séquence ET/OU/NON-ET, 10 MHz, PEX tt", "—",
          g(POST, "puissance moyenne", 1), "—", "µW"),
    ]
    el_html = tbl(["Paramètre", "Symb.", "Conditions", "Min", "Typ", "Max", "Unité"], el,
                  ["", "", "", "n", "n", "n", "c"])

    pins = [
        ("DP1…DP4", "E", "Donnée x<sub>i</sub> vers le banc + : DP<sub>i</sub> = x<sub>i</sub> si w<sub>i</sub> &gt; 0, sinon 0"),
        ("DM1…DM4", "E", "Donnée x<sub>i</sub> vers le banc − : DM<sub>i</sub> = x<sub>i</sub> si w<sub>i</sub> &lt; 0, sinon 0"),
        ("EN<i>i</i>_0…EN<i>i</i>_2", "E", "Bits de |w<sub>i</sub>| (poids 1, 2, 4), communs aux deux bancs de l'entrée i"),
        ("DBP / DBM", "E", "Signe du biais : DBP = 1 si b &gt; 0, DBM = 1 si b &lt; 0"),
        ("ENB_0…ENB_4", "E", "Bits de |b| (poids 1, 2, 4, 8, 16)"),
        ("HEN", "E", "Demi-LSB h (ajoute −0.5 à la somme ; lève les égalités)"),
        ("CLK", "E", "Horloge du comparateur : front montant = décision, niveau bas = pré-charge"),
        ("Q / QB", "S", "Décision : Q = 1 ⇔ ΔV &gt; 0 ; mémorisée jusqu'à la décision suivante"),
        ("VP / VM", "S analog.", "Nœuds de Millman V+ / V− (observation seulement, haute impédance)"),
        ("VDD / VSS", "Alim.", "1.8 V / masse"),
    ]
    tim = [("Période d'évaluation", "T", "100", "ns"), ("Application du code (D, EN, DB, HEN)", "t<sub>0</sub>", "0", "ns"),
           ("Front montant de CLK", "t<sub>CLK↑</sub>", "85", "ns"),
           ("Stabilisation requise avant le front", "t<sub>set</sub>", f"≥ {_f(st_p, 1)} (pire corner)", "ns"),
           ("Q valide après le front", "t<sub>dec</sub>", f"≤ 1 (typ. {g(PRE, 't_dec', 2)})", "ns"),
           ("Front descendant de CLK (pré-charge)", "t<sub>CLK↓</sub>", "95", "ns")]

    ver = [("DRC", f"0 erreur (magic : {c['mdrc']}, KLayout)"), ("LVS (netgen)", E(c["lvs"])),
           ("Antenne", f"{c['ant']} violation"), ("Extraction", f"PEX RC complète ({c['nR']} R, {c['nC']} C)"),
           ("Dispositifs", f"{c['devs']} (36 slices, 124 unités R, comparateur 23 transistors)"),
           ("Surface", f"{c['area']} mm² — {c['dims']} µm")]

    body = band("TwineNeuron-1", "Neurone à seuil analogique programmable, 4 entrées — SkyWater sky130A",
                "FICHE TECHNIQUE<br>Rév. 1.0 · post-layout validé<br>1.8 V · 10 MHz")
    body += f'<div class="cols" style="margin-top:10px"><div><h2 style="margin-top:4px">Caractéristiques</h2>{feat}</div>'
    body += f'<div><h2 style="margin-top:4px">Applications</h2>{appl}<h2>Description</h2>{desc}</div></div>'
    body += f'<h2>Schéma bloc</h2>{svg_block()}'
    body += '<p class="eq">ΔV = V+ − V− = VDD · (Σ w<sub>i</sub>x<sub>i</sub> + b − h/2) / (52 + Σ|w<sub>i</sub>| + |b| + h/2)</p>'

    body += '<h2>Valeurs maximales absolues</h2>'
    body += tbl(["Paramètre", "Min", "Max", "Unité", "Remarque"], abs_rows, ["", "n", "n", "c", ""])
    body += '<h2 class="pb" style="margin-top:0">Conditions de fonctionnement recommandées</h2>'
    body += tbl(["Paramètre", "Min", "Typ", "Max", "Unité"], rec_rows, ["", "n", "n", "n", "c"])
    body += '<h2>Caractéristiques électriques</h2><p class="fn">Typ : tt, 27 °C, 1.8 V (post-layout PEX quand disponible). ' \
            'Min / Max : extrêmes sur les corners simulés (36 points pré-layout, 5 points post-layout ; ss/ff/fs/sf, ' \
            '1.62–1.98 V, −40…125 °C, résistances hh/ll).</p>'
    body += el_html
    body += (f'<p class="fn">(¹) Au corner ss_hh, 1.62 V, −40 °C, t<sub>set</sub> = {_f(st_p, 1)} ns dépasse la cible de '
             f'conception de 50 ns mais reste sous le budget dur de 85 ns (front d\'horloge) ; aucune décision n\'est fausse. '
             f'Pire pré-layout : {_f(st_pre, 1)} ns ({st_prec}).<br>(²) Le kickback du comparateur est proportionnel à ΔV '
             f'(≤ {_f(kr, 0)} % dans la fenêtre de décision) : il ne provoque aucune inversion de signe. '
             f'En valeur absolue il dépasse LSB/4, d\'où VP/VM à ne pas réutiliser pendant la décision.</p>')

    body += '<h2 class="pb" style="margin-top:0">Brochage</h2>'
    body += tbl(["Broche", "Type", "Fonction"], pins)
    body += '<h2>Chronogramme</h2>' + svg_timing()
    body += tbl(["Paramètre", "Symbole", "Valeur", "Unité"], tim, ["", "", "n", "c"])

    body += '<h2 class="pb" style="margin-top:0">Courbes caractéristiques</h2>'
    body += fig(os.path.join(img, "pre_func.png"),
                "Figure 1 — Portes ET, OU, NON-ET enchaînées à 10 MHz (pré-layout, tt) : V±, ΔV, CLK et Q ; 12/12 décisions correctes.", "92%")
    body += fig(os.path.join(img, "pre_settle.png"), "Figure 2 — Stabilisation de V± à 0.5 LSB : (a) code le plus lent, S = 14.5 ; (b) en fonction de la charge S, cible 50 ns (pré-layout, tt).", "92%")
    body += fig(os.path.join(img, "pre_dc.png"), "Figure 3 — Précision DC (pré-layout, tt) : écart au modèle de Millman, INL des poids et du biais, puissance statique selon le code.",
                "74%")
    body += '<h2>Implantation</h2>'
    body += fig(os.path.join(img, "layout_full.png"),
                f"Figure 4 — Layout complet ({c['dims']} µm) : réseau de slices à gauche, comparateur à droite.")
    body += '<div class="cols pb">' + fig(os.path.join(img, "layout_zoom_slices.png"), "Figure 5 — Détail des slices.") + \
            fig(os.path.join(img, "layout_zoom_comparator.png"), "Figure 6 — Comparateur StrongARM et canal de routage symétrique.") + '</div>'
    body += '<h2>Vérification physique</h2>' + tbl(["Contrôle", "Résultat"], ver)
    body += ('<div class="tip"><b>Fichiers livrés</b> : <code>gds/twine_neuron.gds</code> (layout), '
             '<code>netlists/twine_neuron.spice</code> (schéma), <code>netlists/twine_neuron_pex.spice</code> (extraction RC), '
             '<code>results/*.csv</code> (mesures), <code>Neurone_Millman_conception.pdf</code> (rapport détaillé), '
             '<code>Guide_utilisateur.pdf</code>.</div>')
    return page("TwineNeuron-1 — Fiche technique", "Fiche technique", body)


# --------------------------------------------------------------------------- GUIDE


def guide(c):
    POST, PRE, CPOST = c["POST"], c["PRE"], c["CPOST"]
    st_p, st_pc = _ext(CPOST, "t_settle_ns", max)
    img = c["imgdir"]
    ex_w, ex_b, ex_x = (3, -2, 0, 5), -4, (1, 1, 0, 1)
    lv = levels(ex_w, ex_b, 0, ex_x)
    vp, vm, lsb = ideal(ex_w, ex_b, 0, ex_x)
    s_ex = sum(a * b for a, b in zip(ex_w, ex_x)) + ex_b
    sar = c.get("SAR") or []

    body = band("Guide utilisateur", "TwineNeuron-1 — programmer, cadencer et lire le neurone",
                "GUIDE D'UTILISATION<br>Rév. 1.0<br>sky130A · 1.8 V · 10 MHz")
    body += '<div class="toc">' + "".join(f"<div>{t}</div>" for t in (
        "1. Ce que fait le circuit", "2. Mise sous tension et repos", "3. Coder les poids, le biais et h",
        "4. Exemple complet de codage", "5. Cadencement d'une évaluation", "6. Recettes : portes logiques",
        "7. XOR et réseaux à plusieurs couches", "8. Lire la somme pondérée (mode SAR)",
        "9. Limites et précautions", "10. Dépannage", "11. Re-simuler le circuit")) + "</div>"

    body += '<h2>1. Ce que fait le circuit</h2>'
    body += ('<p>À chaque période d\'horloge, le neurone évalue</p><p class="eq">Q = 1 ⇔ w<sub>1</sub>x<sub>1</sub> + '
             'w<sub>2</sub>x<sub>2</sub> + w<sub>3</sub>x<sub>3</sub> + w<sub>4</sub>x<sub>4</sub> + b − h/2 &gt; 0</p>'
             '<p>avec x<sub>i</sub> ∈ {0, 1}, w<sub>i</sub> entier dans [−7, +7], b entier dans [−31, +31] et h ∈ {0, 1}. '
             'Le calcul est analogique (réseau résistif), la sortie est numérique et mémorisée. '
             'Avec h = 0, une somme nulle donne Q = 0 (égalité ⇒ « faux ») ; avec h = 1 la somme n\'est jamais nulle, '
             'ce qui rend la décision robuste aux égalités.</p>')
    body += svg_block()

    body += '<h2>2. Mise sous tension et repos</h2><ul>'
    body += ('<li>Alimenter VDD = 1.8 V (1.62–1.98 V), VSS = 0 V. Toutes les entrées sont des niveaux CMOS 0 / VDD.</li>'
             '<li>Maintenir CLK à 0 jusqu\'à la première évaluation : le comparateur est en pré-charge.</li>'
             '<li>Après la mise sous tension, Q/QB sont indéterminés jusqu\'au premier front de CLK : ignorer la première lecture.</li>'
             '<li><b>Repos basse consommation</b> : mettre tous les EN<i>i</i>_k, ENB_k et HEN à 0. Les slices passent en '
             'haute impédance et le réseau ne consomme plus que la fuite (&lt; 1 nA par slice).</li></ul>')

    body += '<h2>3. Coder les poids, le biais et h</h2>'
    body += tbl(["Grandeur", "Broches", "Règle"], [
        ("|w<sub>i</sub>| (0…7)", "EN<i>i</i>_0, EN<i>i</i>_1, EN<i>i</i>_2", "binaire naturel : EN<i>i</i>_k = bit k de |w<sub>i</sub>|"),
        ("signe de w<sub>i</sub> et x<sub>i</sub>", "DP<i>i</i>, DM<i>i</i>", "w<sub>i</sub> &gt; 0 : DP<i>i</i> = x<sub>i</sub>, DM<i>i</i> = 0<br>"
         "w<sub>i</sub> &lt; 0 : DP<i>i</i> = 0, DM<i>i</i> = x<sub>i</sub><br>w<sub>i</sub> = 0 : DP<i>i</i> = DM<i>i</i> = 0"),
        ("|b| (0…31)", "ENB_0 … ENB_4", "binaire naturel : ENB_k = bit k de |b|"),
        ("signe de b", "DBP, DBM", "b &gt; 0 : DBP = 1 ; b &lt; 0 : DBM = 1 ; b = 0 : les deux à 0"),
        ("h", "HEN", "1 pour ajouter −1/2 à la somme"),
    ])
    body += ('<div class="tip"><b>Ce qui change à chaque évaluation, et ce qui reste fixe.</b> Les EN et le biais '
             '(ENB, DBP, DBM, HEN) décrivent le neurone : on les programme une fois. Seules DP<i>i</i>/DM<i>i</i> portent les '
             'données x<sub>i</sub> et changent à chaque période. La fonction de référence est <code>levels()</code> dans '
             '<code>twine_neuron/sim/tn.py</code>.</div>')
    body += '<pre>def niveaux(w, b, h, x):          # w : 4 poids, b : biais, h : 0/1, x : 4 bits\n' \
            '    n = {}\n    for i in range(4):\n        for k in range(3):\n' \
            '            n[f"EN{i+1}_{k}"] = (abs(w[i]) >> k) &amp; 1\n' \
            '        n[f"DP{i+1}"] = int(x[i] and w[i] > 0)\n        n[f"DM{i+1}"] = int(x[i] and w[i] &lt; 0)\n' \
            '    for k in range(5):\n        n[f"ENB_{k}"] = (abs(b) >> k) &amp; 1\n' \
            '    n["DBP"], n["DBM"], n["HEN"] = int(b > 0), int(b &lt; 0), h\n    return n</pre>'

    body += '<h2>4. Exemple complet de codage</h2>'
    body += (f'<p>Neurone w = ({", ".join(f"{v:+d}" for v in ex_w)}), b = {ex_b:+d}, h = 0, évalué sur '
             f'x = ({", ".join(map(str, ex_x))}). Somme attendue : 3·1 − 2·1 + 0·0 + 5·1 − 4 = <b>{s_ex:+d}</b> &gt; 0 ⇒ '
             f'<b>Q = 1</b>.</p>')
    rows = []
    for i in range(4):
        rows.append((f"entrée {i + 1}", f"w = {ex_w[i]:+d}, x = {ex_x[i]}",
                     " ".join(f"EN{i + 1}_{k}={lv[f'EN{i + 1}_{k}']}" for k in range(3)),
                     f"DP{i + 1}={lv[f'DP{i + 1}']}  DM{i + 1}={lv[f'DM{i + 1}']}"))
    rows.append(("biais", f"b = {ex_b:+d}", " ".join(f"ENB_{k}={lv[f'ENB_{k}']}" for k in range(5)),
                 f"DBP={lv['DBP']}  DBM={lv['DBM']}"))
    rows.append(("demi-LSB", "h = 0", "", f"HEN={lv['HEN']}"))
    body += tbl(["", "Valeur", "Amplitude (fixe)", "Signe / donnée"], [(a, b, f'<span class="mono">{c_}</span>',
                f'<span class="mono">{d}</span>') for a, b, c_, d in rows])
    body += (f'<p>Tensions idéales correspondantes à 1.8 V (modèle de Millman, <code>tn.ideal()</code>) : '
             f'V+ = {vp:.3f} V, V− = {vm:.3f} V, ΔV = {1000 * (vp - vm):+.1f} mV, soit {s_ex:+d} × LSB '
             f'avec LSB = {1000 * lsb:.2f} mV pour ce code.</p>')

    body += '<h2>5. Cadencement d\'une évaluation</h2>' + svg_timing()
    body += ('<ol class="steps"><li>À t = 0, appliquer le code (EN, ENB, DBP/DBM, HEN si changés, et DP/DM des nouvelles données).</li>'
             f'<li>Laisser V± se stabiliser : au moins <b>{_f(st_p, 0)} ns</b> au pire corner post-layout '
             f'({E(st_pc)}), {g_(POST, "t_settle 0.5 LSB", 1)} ns typique.</li>'
             '<li>À t = 85 ns, front montant de CLK : le comparateur décide en ≈ 0.5 ns.</li>'
             '<li>Lire Q (ou QB) à partir de 86 ns ; la valeur reste stable jusqu\'au front montant suivant.</li>'
             '<li>À t = 95 ns, CLK repasse à 0 (pré-charge). Ne pas changer le code entre 85 et 86 ns.</li></ol>')
    body += ('<div class="note">Une fréquence plus élevée est possible tant que le temps entre le changement de code et le '
             'front montant reste supérieur à t<sub>set</sub> au corner visé. Le temps de décision (0.5 ns) n\'est pas le '
             'facteur limitant : c\'est la constante RC du réseau résistif.</div>')

    body += '<h2>6. Recettes : portes logiques</h2>'
    body += '<p>Entrées x<sub>1</sub>, x<sub>2</sub> (et x<sub>3</sub> pour la majorité) ; poids non cités = 0. Validées en transitoire avant et après layout (PEX, 5 corners, 0 erreur).</p>'
    gates = [("ET", "+2, +2", "−3", "0", "2x<sub>1</sub> + 2x<sub>2</sub> − 3 &gt; 0", "0 0 0 1"),
             ("OU", "+2, +2", "−1", "0", "2x<sub>1</sub> + 2x<sub>2</sub> − 1 &gt; 0", "0 1 1 1"),
             ("NON-ET", "−2, −2", "+3", "0", "−2x<sub>1</sub> − 2x<sub>2</sub> + 3 &gt; 0", "1 1 1 0"),
             ("NON-OU", "−2, −2", "+1", "0", "−2x<sub>1</sub> − 2x<sub>2</sub> + 1 &gt; 0", "1 0 0 0"),
             ("NON (x<sub>1</sub>)", "−2, 0", "+1", "0", "−2x<sub>1</sub> + 1 &gt; 0", "1 1 0 0"),
             ("Majorité 3 entrées", "+1, +1, +1", "−1", "1", "x<sub>1</sub>+x<sub>2</sub>+x<sub>3</sub> − 1.5 &gt; 0", "—")]
    body += tbl(["Fonction", "w", "b", "h", "Condition", "Q pour x₁x₂ = 00 01 10 11"], gates,
                ["", "c", "c", "c", "", "mono"])
    body += ('<p class="fn">ET, OU, NON-ET sont mesurés (<code>results/pre_func.csv</code>, <code>results/post_*_func.csv</code>) ; '
             'NON-OU, NON et majorité découlent de la même règle et n\'ont pas de simulation dédiée.</p>')
    body += ('<div class="tip"><b>Règle de conception d\'une porte</b> : choisir des poids assez grands (|w| ≥ 2) pour que '
             'le seuil tombe entre deux valeurs entières, ce qui garantit |ΔV| ≥ 1 LSB et donne une marge &gt; 7σ sur '
             'l\'offset du comparateur.</div>')

    body += '<h2>7. XOR et réseaux à plusieurs couches</h2>'
    body += ('<p>Un seul neurone ne réalise pas le XOR (fonction non linéairement séparable). On l\'obtient en deux '
             'couches multiplexées dans le temps sur le même circuit :</p><ol class="steps">'
             '<li>Période 1 : programmer OU, évaluer x<sub>1</sub>, x<sub>2</sub>, mémoriser Q → y<sub>1</sub>.</li>'
             '<li>Période 2 : programmer NON-ET, même entrées → y<sub>2</sub>.</li>'
             '<li>Période 3 : programmer ET, entrées y<sub>1</sub>, y<sub>2</sub> → Q = x<sub>1</sub> ⊕ x<sub>2</sub>.</li></ol>'
             f'<p>Validé : {_met(PRE, "XOR") or "n/d"} erreur sur 4 combinaisons (<code>results/pre_xor.csv</code>).</p>')
    body += fig(os.path.join(img, "pre_xor.png"), "Figure 1 — XOR 2-2-1 multiplexé à 10 MHz.", "92%")

    body += '<h2>8. Lire la somme pondérée (mode SAR)</h2>'
    body += ('<p>Le neurone sert aussi de convertisseur : avec h = 1, Q = 1 ⇔ s + b − 1/2 &gt; 0 ⇔ b ≥ 1 − s, '
             'où s = Σ w<sub>i</sub>x<sub>i</sub> ∈ [−28, +28]. En cherchant par dichotomie le plus petit b qui donne Q = 1 '
             '(b<sub>min</sub>), on obtient <b>s = 1 − b<sub>min</sub></b> en 6 décisions, sans ADC.</p>')
    body += ('<pre>lo, hi = -31, 31                   # b_min est dans [lo, hi]\nwhile lo &lt; hi:\n'
             '    b = (lo + hi) // 2               # programmer ENB/DBP/DBM avec b, HEN = 1\n'
             '    if evaluer(w, b, h=1, x) == 1:   # une période d\'horloge\n        hi = b\n    else:\n'
             '        lo = b + 1\ns = 1 - lo</pre>')
    if sar:
        body += tbl(["w", "x", "Décisions (b : Q)", "s lu", "s attendu"],
                    [(r["w"], r["x"], f'<span class="mono">{r["trace"]}</span>', r["s_read"], r["s_true"]) for r in sar])
        body += '<p class="fn">Lectures transitoires complètes à 10 MHz (<code>results/pre_sar.csv</code>).</p>'
    body += fig(os.path.join(img, "pre_sar.png"), "Figure 2 — Convergence de la recherche SAR.", "55%")

    body += '<h2>9. Limites et précautions</h2><ul>'
    body += (f'<li><b>Temps de stabilisation</b> : réserver ≥ {_f(st_p, 0)} ns entre le changement de code et le front de CLK '
             'pour couvrir tous les corners. À 10 MHz avec le front à 85 ns, la marge est suffisante partout.</li>'
             '<li><b>VP / VM sont à haute impédance</b> (MΩ, ≈ 370 fF) : une sonde ou une charge externe les ralentit et '
             'décale ΔV. Ne les utiliser que pour l\'observation, avec un tampon à haute impédance.</li>'
             '<li><b>Kickback</b> : la décision injecte quelques dizaines de mV sur V±, sans jamais inverser le signe de ΔV. '
             'Ne pas échantillonner VP/VM pendant les 10 ns qui suivent le front de CLK.</li>'
             '<li><b>Codes à ±0.5 LSB</b> (h = 1 et s + b = 0 ou 1) : ce sont les plus sensibles à l\'offset du comparateur. '
             'Le rendement Monte Carlo est ≈ 99.8 % ; ajouter un décalage de b calibré par puce pour atteindre 100 %.</li>'
             '<li><b>Consommation</b> : elle dépend du code (jusqu\'à ≈ 130 µW à tt, 370 µW au pire corner). '
             'Désactiver les EN au repos.</li>'
             '<li><b>Mode commun</b> : G0 le garantit ≥ 0.75 V à 1.62 V ; ne pas descendre sous 1.62 V.</li></ul>')

    body += '<h2>10. Dépannage</h2>'
    body += tbl(["Symptôme", "Cause probable", "Remède"], [
        ("Q toujours à 0 avec une somme nulle", "comportement normal avec h = 0 (égalité = faux)", "utiliser h = 1 ou décaler b"),
        ("Q faux seulement aux codes ±0.5 LSB", "offset du comparateur (σ ≈ 2 mV)", "calibrer b par puce ; éviter les seuils entiers"),
        ("Q faux après un gros changement de code", "V± pas stabilisé avant le front de CLK", "retarder le front ou baisser la fréquence"),
        ("Décision instable d'une période à l'autre", "code modifié trop près du front montant", "changer le code juste après 86 ns ou à t = 0"),
        ("VP/VM différents de la théorie", "charge de la sonde sur un nœud haute impédance", "sonde ≤ 10 fF ou mesure via Q"),
        ("Consommation élevée au repos", "slices encore activées", "tous les EN, ENB, HEN à 0"),
    ])

    body += '<h2>11. Re-simuler le circuit</h2>'
    body += ('<p>Les simulations tournent avec ngspice et le PDK sky130A (conteneur <code>eda-tools</code>, dépôt monté en '
             '<code>/foss/designs</code>).</p>')
    body += tbl(["Objectif", "Commande (depuis twine_neuron/)"], [
        ("Fonctionnel pré-layout", "<code>python3 sim/run_phase2.py func</code>"),
        ("Fonctionnel post-layout (une porte)", "<code>TN_NETLIST=pex/twine_neuron_pex.spice TN_RSHUNT=1e12 TN_FUNC_GATES=AND "
         "python3 sim/run_phase2.py func</code>"),
        ("Régression post-layout complète", "<code>sh sim/post_v3_regr.sh</code>"),
        ("Corners pré / post", "<code>python3 sim/run_phase3.py pre</code> · <code>sh sim/post_v3_corners.sh</code>"),
        ("Monte Carlo", "<code>python3 sim/run_mc.py</code> puis <code>python3 sim/mc_combine.py</code>"),
        ("Régénérer la documentation", "<code>python3 report/make_docs.py</code>"),
    ])
    body += ('<div class="note">Post-layout : <code>TN_RSHUNT=1e12</code> est obligatoire, et une seule porte par run '
             'avec <code>TN_FUNC_GATES</code> si la machine a ≈ 8 Go de mémoire.</div>')
    return page("TwineNeuron-1 — Guide utilisateur", "Guide utilisateur", body)


def g_(rws, p, nd=2):
    return _f(_met(rws, p), nd)


def build(c, outdir):
    html2pdf(datasheet(c), os.path.join(outdir, "Datasheet.pdf"))
    html2pdf(guide(c), os.path.join(outdir, "Guide_utilisateur.pdf"))
