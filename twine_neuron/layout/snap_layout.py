# Capture PNG du layout (KLayout, rendu hors écran) : klayout -z -nc -rx -r snap_layout.py
import pya
lv = pya.LayoutView()
lv.load_layout("/foss/designs/twine_neuron/layout/twine_neuron.gds", True)
lv.max_hier()
lp = "/foss/pdks/sky130A/libs.tech/klayout/tech/sky130A.lyp"
try:
    lv.load_layer_props(lp)
except Exception:
    pass
lv.set_config("background-color", "#ffffff")
lv.zoom_fit()
lv.save_image("/foss/designs/twine_neuron/plots/layout_full.png", 3000, 700)
bb = lv.active_cellview().cell.dbbox()
# zoom : G0 + premières slices ; comparateur
for name, box in (("layout_zoom_slices.png", pya.DBox(-4, -25, 80, 70)),
                  ("layout_zoom_comparator.png", pya.DBox(bb.right - 60, -25, bb.right + 2, 25))):
    lv.zoom_box(box)
    lv.save_image("/foss/designs/twine_neuron/plots/" + name, 1800, 1400)
print("ok", bb)
