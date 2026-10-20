"""Utilità condivise, costanti e dialoghi."""
import gi, os, sys, json, math, shutil, subprocess, threading, webbrowser, urllib.parse
gi.require_version("Gtk", "4.0"); gi.require_version("Gdk", "4.0")
from gi.repository import Gtk, Gdk, GdkPixbuf, GLib, Gio
from PIL import (Image, ImageOps, ImageFilter, ImageEnhance, ImageDraw, ImageFont,
                 ImageChops, ExifTags, IptcImagePlugin)

CFG = os.path.expanduser("~/.config/lephoto"); os.makedirs(CFG + "/macros", exist_ok=True)
EXT = {"photo": {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff", ".gif"},
       "video": {".mp4", ".mkv", ".webm", ".avi", ".mov", ".m4v"},
       "audio": {".mp3", ".flac", ".ogg", ".wav", ".m4a", ".opus"}}

# ---------------------------------------------------------------- utilità
def tex(im):
    im = im.convert("RGBA")
    return Gdk.MemoryTexture.new(im.width, im.height, Gdk.MemoryFormat.R8G8B8A8,
                                 GLib.Bytes.new(im.tobytes()), im.width * 4)

def load(p):
    return ImageOps.exif_transpose(Image.open(p))

def save_img(im, path, q=92):
    if path.lower().endswith((".jpg", ".jpeg", ".bmp")) and im.mode != "RGB":
        bg = Image.new("RGB", im.size, "white")
        bg.paste(im.convert("RGBA"), mask=im.convert("RGBA").getchannel("A")); im = bg
    im.save(path, quality=q)

def load_meta():
    try: return json.load(open(CFG + "/meta.json"))
    except Exception: return {}

def hexc(r): return "#%02x%02x%02x" % tuple(int(c * 255) for c in (r.red, r.green, r.blue))

def colorbtn(h):
    b = Gtk.ColorButton(); c = Gdk.RGBA(); c.parse(h); b.set_rgba(c); return b

def btn(label, cb):
    b = Gtk.Button(label=label); b.connect("clicked", lambda *_: cb()); return b

def choose(parent, title, action, cb, name=None):
    n = Gtk.FileChooserNative.new(title, parent, action, "_OK", "_Annulla")
    if name: n.set_current_name(name)
    def resp(d, r):
        if r == Gtk.ResponseType.ACCEPT: cb(d.get_file().get_path())
    n.connect("response", resp); parent._native = n; n.show()

def ask(parent, title, fields, ok):
    """fields: (chiave, etichetta, tipo[text|combo|check|color], default)"""
    w = Gtk.Window(title=title, transient_for=parent, modal=True)
    g = Gtk.Grid(row_spacing=8, column_spacing=10, margin_top=14, margin_bottom=14, margin_start=14, margin_end=14)
    w.set_child(g); wid = {}
    for i, (k, lab, kind, d) in enumerate(fields):
        g.attach(Gtk.Label(label=lab, xalign=0), 0, i, 1, 1)
        c = (Gtk.DropDown.new_from_strings(d) if kind == "combo" else Gtk.CheckButton(active=d) if kind == "check"
             else colorbtn(d) if kind == "color" else Gtk.Entry(text=str(d)))
        g.attach(c, 1, i, 1, 1); wid[k] = (kind, c, d)
    def go():
        v = {k: (d[c.get_selected()] if t == "combo" else c.get_active() if t == "check"
                 else c.get_rgba().to_string() if t == "color" else c.get_text()) for k, (t, c, d) in wid.items()}
        w.close(); ok(v)
    g.attach(btn("OK", go), 1, len(fields), 1, 1); w.present()

