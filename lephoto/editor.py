"""Finestra Editor."""
from .util import *
from .filters import *

# ---------------------------------------------------------------- editor
class Editor(Gtk.Window):
    def __init__(self, parent, path=None):
        super().__init__(title="LEPHOTO — Editor", transient_for=parent); self.set_default_size(1280, 820)
        self.main = parent; self.src = path; self.orig = self.cur = None
        self.ops, self.redo_s, self.selw, self.p0, self.lock = [], [], None, (0, 0), False
        hb = Gtk.HeaderBar(); self.set_titlebar(hb)
        for lab, cb in (("Apri", self.open_img), ("Salva con nome", self.save_as), ("Annulla", self.undo), ("Ripeti", self.redo),
                        ("Salva progetto", self.save_proj), ("Apri progetto", self.open_proj), ("Salva macro", self.save_macro)):
            hb.pack_start(btn(lab, cb))
        self.pic = Gtk.Picture(); self.pic.set_can_shrink(True)
        self.ov = Gtk.Overlay(child=self.pic, hexpand=True, vexpand=True)
        da = Gtk.DrawingArea(); da.set_can_target(False); da.set_draw_func(self.draw); self.da = da; self.ov.add_overlay(da)
        g = Gtk.GestureDrag(); g.connect("drag-begin", self.gbegin); g.connect("drag-update", self.gupd); g.connect("drag-end", self.gend)
        self.ov.add_controller(g)
        nb = Gtk.Notebook(); nb.set_size_request(340, -1)
        paned = Gtk.Paned(start_child=self.ov, end_child=nb, position=900); self.set_child(paned)
        self.status = Gtk.Label(label="", xalign=0)
        # Filtri
        fb = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        se = Gtk.SearchEntry(); self.lb = Gtk.ListBox()
        for n in sorted(FILTERS): self.lb.append(Gtk.Label(label=n, xalign=0, margin_top=4, margin_bottom=4, margin_start=6))
        self.lb.set_filter_func(lambda r: se.get_text().lower() in r.get_child().get_text().lower())
        se.connect("search-changed", lambda *_: self.lb.invalidate_filter())
        self.lb.connect("row-activated", lambda lb, r: self.do_filter(r.get_child().get_text()))
        self.local = Gtk.CheckButton(label="Solo nella selezione (maschera locale)")
        sw = Gtk.ScrolledWindow(vexpand=True, child=self.lb)
        for w in (se, self.local, sw): fb.append(w)
        nb.append_page(fb, Gtk.Label(label="Filtri"))
        # Regolazioni
        ab = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6, margin_top=8, margin_start=8, margin_end=8)
        self.sc = []
        for lab in ("Luminosità", "Contrasto", "Saturazione", "Nitidezza"):
            ab.append(Gtk.Label(label=lab, xalign=0)); s = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 2.5, .05)
            s.set_value(1); s.connect("value-changed", self.adj_prev); ab.append(s); self.sc.append(s)
        ab.append(btn("Applica", self.adj_apply)); nb.append_page(ab, Gtk.Label(label="Regola"))
        # Trasforma
        tb = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6, margin_top=8, margin_start=8, margin_end=8)
        tools = Gtk.DropDown.new_from_strings(["Selezione (ritaglio/maschera)", "Contagocce colore", "Gomma magica (Cut out)"])
        self.tool = tools; tb.append(Gtk.Label(label="Strumento mouse", xalign=0)); tb.append(tools)
        for lab, op in (("Ruota 90° ↻", ["rot", 90]), ("Ruota 90° ↺", ["rot", -90]), ("Rifletti orizz.", ["flip", "h"]), ("Rifletti vert.", ["flip", "v"])):
            tb.append(btn(lab, lambda op=op: self.push(op)))
        self.str = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, -15, 15, .5); self.str.set_value(0)
        tb.append(Gtk.Label(label="Raddrizza (°)", xalign=0)); tb.append(self.str)
        tb.append(btn("Applica raddrizzamento", lambda: self.push(["straighten", self.str.get_value()])))
        tb.append(btn("Ritaglia selezione", self.crop)); tb.append(btn("Ritaglio circolare", lambda: self.crop(True)))
        self.rw, self.rh = Gtk.Entry(placeholder_text="Larghezza px"), Gtk.Entry(placeholder_text="Altezza px")
        tb.append(self.rw); tb.append(self.rh); tb.append(btn("Ridimensiona", self.resize))
        self.magic = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 120, 1); self.magic.set_value(30)
        tb.append(Gtk.Label(label="Tolleranza gomma magica", xalign=0)); tb.append(self.magic)
        nb.append_page(tb, Gtk.Label(label="Trasforma"))
        # Oggetti
        ob = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6, margin_top=8, margin_start=8, margin_end=8)
        self.txt = Gtk.Entry(text="LEPHOTO"); self.tsz = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 2, 30, 1); self.tsz.set_value(8)
        self.tcol = colorbtn("#ffffff"); self.fw = Gtk.Entry(text="30"); self.fcol = colorbtn("#ffffff")
        for w in (Gtk.Label(label="Testo", xalign=0), self.txt, Gtk.Label(label="Dimensione (% altezza)", xalign=0), self.tsz, self.tcol,
                  btn("Aggiungi testo (nella selezione)", self.add_text), Gtk.Label(label="Cornice/bordo (px)", xalign=0), self.fw, self.fcol,
                  btn("Aggiungi cornice", lambda: self.push(["frame", int(self.fw.get_text() or 0), self.fcol.get_rgba().to_string()]))):
            ob.append(w)
        nb.append_page(ob, Gtk.Label(label="Oggetti"))
        # Colore
        cb = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6, margin_top=8, margin_start=8, margin_end=8)
        self.zoom = Gtk.Picture(); self.zoom.set_size_request(140, 140); self.zoom.set_can_shrink(False)
        self.hexl = Gtk.Label(label="#------", selectable=True)
        cb.append(self.zoom); cb.append(self.hexl); cb.append(self.status); nb.append_page(cb, Gtk.Label(label="Colore"))
        if path: self.set_image(path)

    # --- stato
    def set_image(self, p):
        self.src = p; self.orig = self.cur = load(p).convert("RGBA"); self.ops, self.redo_s, self.selw = [], [], None
        self.set_title("LEPHOTO — " + os.path.basename(p)); self.refresh()

    def refresh(self): self.pic.set_paintable(tex(self.cur)); self.da.queue_draw(); self.status.set_text(f"{self.cur.width}×{self.cur.height}px — {len(self.ops)} operazioni")

    def push(self, op, keep=False):
        if not self.cur: return
        self.ops.append(op)
        if not keep: self.redo_s.clear()
        self.cur = apply_op(self.cur, op); self.selw = None; self.refresh()

    def rebuild(self):
        self.cur = self.orig
        for o in self.ops: self.cur = apply_op(self.cur, o)
        self.refresh()

    def undo(self):
        if self.ops: self.redo_s.append(self.ops.pop()); self.rebuild()

    def redo(self):
        if self.redo_s: self.push(self.redo_s.pop(), keep=True)

    # --- file / progetto / macro
    def open_img(self): choose(self, "Apri immagine", Gtk.FileChooserAction.OPEN, self.set_image)
    def save_as(self):
        if self.cur: choose(self, "Salva", Gtk.FileChooserAction.SAVE, lambda p: save_img(self.cur, p), os.path.basename(self.src or "foto.png"))
    def save_proj(self):
        if self.src: choose(self, "Salva progetto", Gtk.FileChooserAction.SAVE, lambda p: json.dump({"src": self.src, "ops": self.ops}, open(p, "w")), "progetto.lephoto")
    def open_proj(self):
        def go(p):
            d = json.load(open(p)); self.set_image(d["src"]); self.ops = d["ops"]; self.rebuild()
        choose(self, "Apri progetto", Gtk.FileChooserAction.OPEN, go)
    def save_macro(self):
        ask(self, "Salva macro", [("n", "Nome macro", "text", "macro1")],
            lambda v: json.dump(self.ops, open(f"{CFG}/macros/{v['n']}.json", "w")))

    # --- mouse
    def frac(self, x, y):
        W, H = self.ov.get_width(), self.ov.get_height(); iw, ih = self.cur.size; s = min(W / iw, H / ih)
        ox, oy = (W - iw * s) / 2, (H - ih * s) / 2
        return min(1, max(0, (x - ox) / (iw * s))), min(1, max(0, (y - oy) / (ih * s)))

    def sel(self):
        if not self.selw: return None
        (a, b), (c, d) = self.frac(*self.selw[:2]), self.frac(*self.selw[2:])
        return min(a, c), min(b, d), max(a, c), max(b, d)

    def draw(self, area, cr, w, h):
        if self.selw:
            x0, y0, x1, y1 = self.selw; cr.set_source_rgba(1, 1, 1, .95); cr.set_dash([6, 4]); cr.set_line_width(1.5)
            cr.rectangle(min(x0, x1), min(y0, y1), abs(x1 - x0), abs(y1 - y0)); cr.stroke()

    def gbegin(self, g, x, y): self.p0 = (x, y)

    def gupd(self, g, dx, dy):
        if not self.cur: return
        t = self.tool.get_selected(); x, y = self.p0[0] + dx, self.p0[1] + dy
        if t == 0: self.selw = (*self.p0, x, y); self.da.queue_draw()
        elif t == 1: self.pick(*self.frac(x, y))

    def gend(self, g, dx, dy):
        if not self.cur: return
        t = self.tool.get_selected(); x, y = self.p0[0] + dx, self.p0[1] + dy
        if t == 0 and abs(dx) < 4 and abs(dy) < 4: self.selw = None; self.da.queue_draw()
        elif t == 1: self.pick(*self.frac(x, y))
        elif t == 2: fx, fy = self.frac(x, y); self.push(["magic", fx, fy, int(self.magic.get_value())])

    def pick(self, fx, fy):
        w, h = self.cur.size; px, py = int(fx * (w - 1)), int(fy * (h - 1)); r, g, b, _ = self.cur.getpixel((px, py))
        self.hexl.set_markup(f"<b>#{r:02x}{g:02x}{b:02x}</b>  rgb({r},{g},{b})")
        box = self.cur.crop((px - 5, py - 5, px + 6, py + 6)).resize((165, 165), Image.NEAREST)
        self.zoom.set_paintable(tex(box)); self.get_clipboard().set(f"#{r:02x}{g:02x}{b:02x}")

    # --- azioni
    def do_filter(self, name):
        s = self.sel()
        self.push(["local", name, *s] if (self.local.get_active() and s) else ["filter", name])

    def adj_prev(self, *_):
        if self.cur and not self.lock: self.pic.set_paintable(tex(apply_op(self.cur, ["adjust", [s.get_value() for s in self.sc]])))

    def adj_apply(self):
        v = [s.get_value() for s in self.sc]; self.lock = True
        for s in self.sc: s.set_value(1)
        self.lock = False; self.push(["adjust", v])

    def crop(self, circle=False):
        s = self.sel()
        if s: self.push(["crop", *s])
        if s and circle: self.push(["circle"])

    def resize(self):
        if not self.cur: return
        w, h = self.rw.get_text(), self.rh.get_text(); iw, ih = self.cur.size
        if w and not h: h = int(int(w) * ih / iw)
        if h and not w: w = int(int(h) * iw / ih)
        if w and h: self.push(["resize", int(w), int(h)])

    def add_text(self):
        s = self.sel() or (.1, .4, 1, 1)
        self.push(["text", self.txt.get_text(), s[0], s[1], self.tsz.get_value() / 100, self.tcol.get_rgba().to_string()])

