"""Finestra principale."""
from .util import *
from .filters import *
from .editor import *

# ---------------------------------------------------------------- finestra principale
class Main(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="LEPHOTO"); self.set_default_size(1250, 800)
        self.meta = load_meta(); self.folder = None; self.items = []; self.kind = "photo"; self.idx = 0; self.tok = 0; self.badges = {}
        hb = Gtk.HeaderBar(); self.hb = hb; self.set_titlebar(hb)
        hb.pack_start(btn("Apri cartella", lambda: choose(self, "Cartella", Gtk.FileChooserAction.SELECT_FOLDER, self.scan)))
        self.kdd = Gtk.DropDown.new_from_strings(["Foto", "Video", "Audio"]); self.kdd.connect("notify::selected", self.on_kind); hb.pack_start(self.kdd)
        hb.pack_end(btn("Editor", self.open_editor))
        mb = Gtk.MenuButton(label="Strumenti"); pop = Gtk.Popover(); bx = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        for lab, cb in (("Batch Edit…", self.t_batch), ("Batch Formato…", self.t_conv), ("Batch Ridimensiona…", self.t_resize),
                        ("Batch Rinomina…", self.t_rename), ("Collage…", self.t_collage), ("Combina…", self.t_combine),
                        ("Crea GIF animata…", self.t_gif), ("Dividi (Split)…", self.t_split), ("Stampa…", self.t_print),
                        ("Cattura schermo", self.t_capture)):
            b = btn(lab, lambda cb=cb: (pop.popdown(), cb())); b.set_has_frame(False); bx.append(b)
        pop.set_child(bx); mb.set_popover(pop); hb.pack_end(mb)
        # griglia
        self.fb = Gtk.FlowBox(selection_mode=Gtk.SelectionMode.MULTIPLE, homogeneous=True, max_children_per_line=40,
                              activate_on_single_click=False, valign=Gtk.Align.START)
        self.fb.connect("child-activated", lambda fb, c: self.open_loupe(c.get_index()))
        # loupe
        self.lp = Gtk.Picture(); self.lp.set_can_shrink(True)
        self.lsw = Gtk.ScrolledWindow(child=self.lp, hexpand=True, vexpand=True)
        self.flagb = Gtk.ToggleButton(label="⚑ Flag"); self.flagb.connect("toggled", lambda *_: self.flag(self.flagb.get_active()))
        self.starb = [btn("★", lambda n=n: self.rate(n)) for n in range(1, 6)]
        self.zb = Gtk.ToggleButton(label="1:1"); self.zb.connect("toggled", lambda b: self.lp.set_can_shrink(not b.get_active()))
        sh = Gtk.MenuButton(label="Condividi"); sp = Gtk.Popover(); sbx = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        for lab, cb in (("Email", self.share_mail), ("Twitter / X", self.share_tw), ("Facebook", self.share_fb)): sbx.append(btn(lab, cb))
        sp.set_child(sbx); sh.set_popover(sp)
        tools = [btn("← Griglia", lambda: self.stack.set_visible_child_name("grid")), btn("◀", lambda: self.step(-1)), btn("▶", lambda: self.step(1)),
                 self.flagb, *self.starb, btn("↺", lambda: self.rot(270)), btn("↻", lambda: self.rot(90)), self.zb, sh,
                 btn("Metadati", self.show_meta), btn("Schermo intero", self.toggle_fs), btn("Modifica", self.open_editor)]
        self.lbar = Gtk.Box(spacing=4, margin_top=4, margin_bottom=4, margin_start=6)
        for t in tools: self.lbar.append(t)
        self.lname = Gtk.Label(hexpand=True, xalign=1, margin_end=10); self.lbar.append(self.lname)
        lpage = Gtk.Box(orientation=Gtk.Orientation.VERTICAL); lpage.append(self.lsw); lpage.append(self.lbar)
        self.stack = Gtk.Stack(); self.stack.add_named(Gtk.ScrolledWindow(child=self.fb), "grid"); self.stack.add_named(lpage, "loupe")
        self.status = Gtk.Label(label="Apri una cartella per iniziare", xalign=0, margin_start=8, margin_top=3, margin_bottom=3)
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL); self.stack.set_vexpand(True); root.append(self.stack); root.append(self.status); self.set_child(root)
        kc = Gtk.EventControllerKey(); kc.connect("key-pressed", self.on_key); self.add_controller(kc)
        self.scan(os.path.expanduser("~/Pictures") if os.path.isdir(os.path.expanduser("~/Pictures")) else os.path.expanduser("~"))

    def say(self, m): self.status.set_text(m); return False
    def bg(self, fn):
        def run():
            try: m = fn()
            except Exception as e: m = f"Errore: {e}"
            GLib.idle_add(self.say, m)
        threading.Thread(target=run, daemon=True).start()

    # --- browser
    def on_kind(self, *_): self.kind = ("photo", "video", "audio")[self.kdd.get_selected()]; self.scan(self.folder)

    def scan(self, folder):
        if not folder: return
        self.folder = folder; self.tok += 1; tok = self.tok
        while (c := self.fb.get_first_child()): self.fb.remove(c)
        self.items = sorted(os.path.join(folder, f) for f in os.listdir(folder) if os.path.splitext(f)[1].lower() in EXT[self.kind])
        pend = []; self.badges = {}
        for p in self.items:
            b = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3, margin_top=6, margin_bottom=6, margin_start=6, margin_end=6)
            if self.kind == "photo":
                pic = Gtk.Picture(); pic.set_size_request(180, 140); pic.set_can_shrink(True); b.append(pic); pend.append((p, pic))
            else:
                b.append(Gtk.Image.new_from_icon_name("video-x-generic" if self.kind == "video" else "audio-x-generic")); b.get_first_child().set_pixel_size(96)
            n = Gtk.Label(label=os.path.basename(p), ellipsize=3, max_width_chars=22); bl = Gtk.Label(); self.badges[p] = bl
            b.append(n); b.append(bl); self.fb.append(b); self.update_badge(p)
        self.set_title(f"LEPHOTO — {folder}"); self.say(f"{len(self.items)} file")
        it = iter(pend)
        def step():
            if tok != self.tok: return False
            try: p, pic = next(it)
            except StopIteration: return False
            try: im = load(p); im.thumbnail((220, 180)); pic.set_paintable(tex(im))
            except Exception: pass
            return True
        GLib.idle_add(step)

    def selection(self):
        s = [self.items[c.get_index()] for c in self.fb.get_selected_children()]
        return s or list(self.items)

    def update_badge(self, p):
        m = self.meta.get(p, {}); self.badges[p].set_text(("⚑ " if m.get("flag") else "") + "★" * m.get("stars", 0))

    def cur(self): return self.items[self.idx] if self.items else None
    def commit(self):
        json.dump(self.meta, open(CFG + "/meta.json", "w"))
        if self.cur(): self.update_badge(self.cur())

    # --- loupe
    def open_loupe(self, i):
        if self.kind != "photo": Gio.AppInfo.launch_default_for_uri(Gio.File.new_for_path(self.items[i]).get_uri(), None); return
        self.idx = i; self.show(); self.stack.set_visible_child_name("loupe")

    def show(self):
        p = self.cur()
        if not p: return
        self.lp.set_paintable(tex(load(p))); m = self.meta.get(p, {}); self.lname.set_text(f"{os.path.basename(p)}  ({self.idx + 1}/{len(self.items)})")
        self.flagb.set_active(bool(m.get("flag")))
        for n, b in enumerate(self.starb, 1): b.set_label("★" if n <= m.get("stars", 0) else "☆")

    def step(self, d):
        if self.items: self.idx = (self.idx + d) % len(self.items); self.show()

    def flag(self, v=None):
        p = self.cur(); m = self.meta.setdefault(p, {}); m["flag"] = (not m.get("flag")) if v is None else v; self.commit(); self.show()

    def rate(self, n):
        m = self.meta.setdefault(self.cur(), {}); m["stars"] = 0 if m.get("stars") == n else n; self.commit(); self.show()

    def toggle_fs(self):
        fs = not self.is_fullscreen(); self.fullscreen() if fs else self.unfullscreen()
        self.hb.set_visible(not fs); self.status.set_visible(not fs); self.stack.set_visible_child_name("loupe") if fs and self.cur() else None

    def on_key(self, c, kv, kc, st):
        k = Gdk.keyval_name(kv); lo = self.stack.get_visible_child_name() == "loupe"
        if k == "F11": self.toggle_fs()
        elif k == "Escape":
            if self.is_fullscreen(): self.toggle_fs()
            elif lo: self.stack.set_visible_child_name("grid")
        elif lo and k in ("Right", "space"): self.step(1)
        elif lo and k == "Left": self.step(-1)
        elif lo and k == "f": self.flag()
        elif lo and k and len(k) == 1 and k in "012345": self.rate(int(k))
        elif lo and k == "e": self.open_editor()
        else: return False
        return True

    def rot(self, deg):
        p = self.cur()
        try:
            if p.lower().endswith((".jpg", ".jpeg")) and shutil.which("jpegtran") and Image.open(p).getexif().get(0x112, 1) == 1:
                subprocess.run(["jpegtran", "-rotate", str(deg), "-copy", "all", "-outfile", p + ".tmp", p], check=True); os.replace(p + ".tmp", p)
                self.say("Rotazione lossless (jpegtran)")
            else:
                load(p).rotate(-deg, expand=True).save(p, quality=95); self.say("Ruotata (ricodificata: jpegtran non applicabile)")
            self.show()
        except Exception as e: self.say(f"Errore rotazione: {e}")

    # --- metadati
    def show_meta(self):
        p = self.cur()
        if not p: return
        im = Image.open(p); ex = im.getexif(); L = [f"{im.format}  {im.width}×{im.height}  {os.path.getsize(p) // 1024} KB", "", "— EXIF —"]
        for k, v in list(ex.items()) + list(ex.get_ifd(0x8769).items()):
            if not isinstance(v, bytes): L.append(f"{ExifTags.TAGS.get(k, k)}: {v}")
        gps = ex.get_ifd(0x8825); url = None
        if gps.get(2) and gps.get(4):
            dec = lambda t, r: (sum(float(x) / 60 ** i for i, x in enumerate(t))) * (-1 if r in ("S", "W") else 1)
            la, lo = dec(gps[2], gps.get(1)), dec(gps[4], gps.get(3)); L += ["", "— GPS —", f"{la:.6f}, {lo:.6f}"]
            url = f"https://www.openstreetmap.org/?mlat={la}&mlon={lo}&zoom=15"
        try:
            ip = IptcImagePlugin.getiptcinfo(im) or {}
            if ip: L += ["", "— IPTC —"] + [f"{k}: {v.decode('utf8', 'replace') if isinstance(v, bytes) else v}" for k, v in ip.items()]
        except Exception: pass
        w = Gtk.Window(title="Metadati", transient_for=self, default_width=520, default_height=560); bx = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        tv = Gtk.TextView(editable=False, monospace=True, wrap_mode=Gtk.WrapMode.WORD); tv.get_buffer().set_text("\n".join(L))
        bx.append(Gtk.ScrolledWindow(child=tv, vexpand=True))
        if url: bx.append(btn("Apri posizione su OpenStreetMap", lambda: webbrowser.open(url)))
        w.set_child(bx); w.present()

    # --- condivisione
    def share_mail(self):
        p = self.cur()
        if shutil.which("xdg-email"): subprocess.Popen(["xdg-email", "--subject", os.path.basename(p), "--attach", p])
        else: webbrowser.open("mailto:?subject=" + urllib.parse.quote(os.path.basename(p)))
    def share_tw(self): webbrowser.open("https://twitter.com/intent/tweet?text=" + urllib.parse.quote(os.path.basename(self.cur()) + " #LEPHOTO")); self.say("Allega manualmente il file nel post")
    def share_fb(self): webbrowser.open("https://www.facebook.com/"); self.say("Carica manualmente il file su Facebook")

    def open_editor(self):
        p = self.cur() if self.stack.get_visible_child_name() == "loupe" else (self.selection()[0] if self.items else None)
        Editor(self, p).present()

    # --- strumenti batch
    def outdir(self, ps):
        d = os.path.join(os.path.dirname(ps[0]), "lephoto_out"); os.makedirs(d, exist_ok=True); return d

    def t_conv(self):
        ps = self.selection()
        def go(v):
            def job():
                d = self.outdir(ps)
                for p in ps: save_img(load(p), os.path.join(d, os.path.splitext(os.path.basename(p))[0] + "." + v["f"]), int(v["q"]))
                return f"Convertiti {len(ps)} file in {d}"
            self.bg(job)
        ask(self, "Batch formato", [("f", "Formato", "combo", ["jpg", "png", "webp", "bmp", "tiff"]), ("q", "Qualità", "text", 92)], go)

    def t_resize(self):
        ps = self.selection()
        def go(v):
            def job():
                d = self.outdir(ps)
                for p in ps:
                    im = load(p)
                    im = im.resize((int(v["w"]), int(v["h"])), Image.LANCZOS) if v["x"] else ImageOps.contain(im, (int(v["w"]), int(v["h"])), Image.LANCZOS)
                    save_img(im, os.path.join(d, os.path.basename(p)))
                return f"Ridimensionati {len(ps)} file in {d}"
            self.bg(job)
        ask(self, "Batch ridimensiona", [("w", "Larghezza max", "text", 1920), ("h", "Altezza max", "text", 1080), ("x", "Dimensioni esatte", "check", False)], go)

    def t_rename(self):
        ps = self.selection()
        def go(v):
            for i, p in enumerate(ps, int(v["s"])):
                os.rename(p, os.path.join(os.path.dirname(p), f"{v['p']}{i:03d}" + os.path.splitext(p)[1]))
            self.scan(self.folder); self.say(f"Rinominati {len(ps)} file")
        ask(self, "Batch rinomina", [("p", "Prefisso", "text", "foto_"), ("s", "Numero iniziale", "text", 1)], go)

    def t_batch(self):
        ps = self.selection(); macros = sorted(f[:-5] for f in os.listdir(CFG + "/macros"))
        choices = ["Filtro: " + n for n in sorted(FILTERS)] + ["Macro: " + m for m in macros]
        def go(v):
            def job():
                ops = [["filter", v["c"][8:]]] if v["c"].startswith("Filtro") else json.load(open(f"{CFG}/macros/{v['c'][7:]}.json"))
                d = self.outdir(ps)
                for p in ps:
                    im = load(p).convert("RGBA")
                    for o in ops: im = apply_op(im, o)
                    save_img(im, os.path.join(d, os.path.basename(p)))
                return f"Elaborati {len(ps)} file in {d}"
            self.bg(job)
        ask(self, "Batch edit / Macro", [("c", "Effetto o macro", "combo", choices)], go)

    def t_collage(self):
        ps = self.selection()
        def go(v):
            def job():
                n, c, cell, gap = len(ps), int(v["c"]), int(v["s"]), int(v["g"]); r = math.ceil(n / c)
                out = Image.new("RGB", (c * cell + gap * (c + 1), r * cell + gap * (r + 1)), v["bg"])
                for i, p in enumerate(ps): out.paste(ImageOps.fit(load(p).convert("RGB"), (cell, cell)), (gap + (i % c) * (cell + gap), gap + (i // c) * (cell + gap)))
                o = os.path.join(self.outdir(ps), "collage.jpg"); out.save(o, quality=92); return "Collage salvato: " + o
            self.bg(job)
        ask(self, "Collage", [("c", "Colonne", "text", 3), ("s", "Lato cella px", "text", 600), ("g", "Spaziatura px", "text", 12), ("bg", "Sfondo", "color", "#ffffff")], go)

    def t_combine(self):
        ps = self.selection()
        def go(v):
            def job():
                hz = v["d"] == "Orizzontale"; ims = [load(p).convert("RGB") for p in ps]
                if hz: t = min(i.height for i in ims); ims = [i.resize((int(i.width * t / i.height), t)) for i in ims]; out = Image.new("RGB", (sum(i.width for i in ims), t))
                else: t = min(i.width for i in ims); ims = [i.resize((t, int(i.height * t / i.width))) for i in ims]; out = Image.new("RGB", (t, sum(i.height for i in ims)))
                o = 0
                for i in ims: out.paste(i, (o, 0) if hz else (0, o)); o += i.width if hz else i.height
                f = os.path.join(self.outdir(ps), "combine.jpg"); out.save(f, quality=92); return "Salvato: " + f
            self.bg(job)
        ask(self, "Combina", [("d", "Direzione", "combo", ["Orizzontale", "Verticale"])], go)

    def t_gif(self):
        ps = self.selection()
        def go(v):
            def job():
                fr = [ImageOps.contain(load(p).convert("RGB"), (int(v["w"]), 4000)) for p in ps]; w, h = fr[0].size
                fr = [ImageOps.fit(f, (w, h)) for f in fr]; o = os.path.join(self.outdir(ps), "animazione.gif")
                fr[0].save(o, save_all=True, append_images=fr[1:], duration=int(v["ms"]), loop=0); return "GIF salvata: " + o
            self.bg(job)
        ask(self, "GIF animata", [("ms", "Durata fotogramma ms", "text", 500), ("w", "Larghezza px", "text", 640)], go)

    def t_split(self):
        p = self.selection()[0]
        def go(v):
            def job():
                im = load(p); r, c = int(v["r"]), int(v["c"]); d = self.outdir([p]); w, h = im.width // c, im.height // r
                for i in range(r):
                    for j in range(c): save_img(im.crop((j * w, i * h, (j + 1) * w, (i + 1) * h)), os.path.join(d, f"{os.path.splitext(os.path.basename(p))[0]}_{i + 1}_{j + 1}.png"))
                return f"{r * c} parti salvate in {d}"
            self.bg(job)
        ask(self, "Split", [("r", "Righe", "text", 2), ("c", "Colonne", "text", 2)], go)

    def t_print(self):
        p = self.cur() if self.stack.get_visible_child_name() == "loupe" else self.selection()[0]
        pb = GdkPixbuf.Pixbuf.new_from_file(p); op = Gtk.PrintOperation(); op.set_n_pages(1)
        def draw(o, ctx, n):
            cr = ctx.get_cairo_context(); s = min(ctx.get_width() / pb.get_width(), ctx.get_height() / pb.get_height())
            cr.scale(s, s); Gdk.cairo_set_source_pixbuf(cr, pb, 0, 0); cr.paint()
        op.connect("draw-page", draw); op.run(Gtk.PrintOperationAction.PRINT_DIALOG, self)

    def t_capture(self):
        d = os.path.expanduser("~/Pictures/LEPHOTO"); os.makedirs(d, exist_ok=True); out = os.path.join(d, GLib.DateTime.new_now_local().format("shot_%Y%m%d_%H%M%S.png"))
        cmds = [["gnome-screenshot", "-f", out], ["grim", out], ["spectacle", "-b", "-n", "-f", "-o", out], ["scrot", out], ["import", "-window", "root", out]]
        cmd = next((c for c in cmds if shutil.which(c[0])), None)
        if not cmd: return self.say("Installa gnome-screenshot, grim, spectacle o scrot")
        self.minimize()
        def job():
            subprocess.run(cmd); GLib.idle_add(lambda: (self.unminimize(), self.say("Screenshot: " + out), self.scan(d)) and False)
        GLib.timeout_add(900, lambda: threading.Thread(target=job, daemon=True).start() or False)

