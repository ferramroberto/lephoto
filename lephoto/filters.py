"""Filtri e operazioni di editing."""
from .util import *

# ---------------------------------------------------------------- filtri
def keep_alpha(fn):
    def w(im):
        if im.mode == "RGBA":
            r = fn(im.convert("RGB")).convert("RGB"); r.putalpha(im.getchannel("A")); return r
        return fn(im.convert("RGB"))
    return w

def screen_leak(im, grad, col): return ImageChops.screen(im, ImageOps.colorize(grad, "black", col))

def grain(im, a=.12): return Image.blend(im, Image.effect_noise(im.size, 60).convert("RGB"), a)

def vignette(im, k=1.5):
    m = Image.radial_gradient("L").resize(im.size).point(lambda v: int(max(0, v - 90) * k))
    return Image.composite(Image.new("RGB", im.size, "black"), im, m)

def sepia(im): return ImageOps.colorize(ImageOps.grayscale(im), "#2b1a0a", "#ffe9c4", mid="#a07850")

def miniature(im):
    m = Image.linear_gradient("L").resize(im.size).point(lambda v: int(min(255, abs(v - 128) * 2.4)))
    b = im.filter(ImageFilter.GaussianBlur(max(im.size) / 90))
    return ImageEnhance.Color(Image.composite(b, im, m)).enhance(1.5)

def flare(im, pos=(.72, .22), col="#ffd9a0"):
    w, h = im.size; r = min(w, h) // 3; f = Image.new("L", im.size, 0)
    f.paste(Image.radial_gradient("L").resize((2 * r, 2 * r)).point(lambda v: 255 - v), (int(w * pos[0]) - r, int(h * pos[1]) - r))
    return ImageChops.screen(im, ImageOps.colorize(f, "black", col))

def hdr(im):
    im = ImageOps.autocontrast(im, 1)
    return ImageEnhance.Color(im.filter(ImageFilter.UnsharpMask(max(im.size) / 90, 260, 0))).enhance(1.3)

def bloom(im):
    return Image.blend(im, ImageChops.screen(im, im.filter(ImageFilter.GaussianBlur(max(im.size) / 50))), .7)

FILTERS = {
    "Grayscale": lambda im: ImageOps.grayscale(im).convert("RGB"), "Sepia": sepia,
    "Negative": ImageOps.invert, "Auto Levels": lambda im: ImageOps.autocontrast(im, 1),
    "Auto Contrast": ImageOps.autocontrast, "Equalize": ImageOps.equalize,
    "Sharpen": lambda im: im.filter(ImageFilter.UnsharpMask(2, 150, 3)),
    "Blur": lambda im: im.filter(ImageFilter.GaussianBlur(max(im.size) / 200)),
    "Black & White": lambda im: ImageOps.autocontrast(ImageOps.grayscale(im)).convert("1").convert("RGB"),
    "Magic Color": lambda im: ImageEnhance.Contrast(ImageEnhance.Color(im).enhance(1.7)).enhance(1.1),
    "Miniature": miniature, "Bloom": bloom, "HDR": hdr, "Vignette": vignette,
    "Surrealistic": lambda im: ImageEnhance.Color(ImageOps.solarize(im, 110)).enhance(1.8),
    "Posterize": lambda im: ImageOps.posterize(im, 3), "Solarize": lambda im: ImageOps.solarize(im, 128),
    "Emboss": lambda im: im.filter(ImageFilter.EMBOSS), "Contour": lambda im: im.filter(ImageFilter.CONTOUR),
    "Edge Enhance": lambda im: im.filter(ImageFilter.EDGE_ENHANCE_MORE),
    "Mosaic": lambda im: im.resize((max(1, im.width // 24), max(1, im.height // 24)), Image.NEAREST).resize(im.size, Image.NEAREST),
    "Warm": lambda im: ImageChops.multiply(im, Image.new("RGB", im.size, "#ffe2c0")),
    "Cool": lambda im: ImageChops.multiply(im, Image.new("RGB", im.size, "#c8e0ff")),
    "Film Grain": grain,
    "Light Leak Orange": lambda im: screen_leak(im, Image.linear_gradient("L").rotate(90).resize(im.size), "#ff6a2a"),
    "Light Leak Magenta": lambda im: screen_leak(im, Image.linear_gradient("L").rotate(-90).resize(im.size), "#d03a9a"),
    "Lens Flare": flare, "Lens Flare Blue": lambda im: flare(im, (.3, .3), "#a0c8ff"),
    "Old Photo": lambda im: vignette(grain(ImageEnhance.Contrast(sepia(im)).enhance(.8), .18), 1.1),
}
DUOS = {"Sunset": ("#2b1055", "#ff9a5a"), "Ocean": ("#03243f", "#7fe0ff"), "Forest": ("#06210f", "#c9f5a0"),
        "Rose": ("#3a0a1f", "#ffc2d6"), "Gold": ("#1c1303", "#ffd86b"), "Mint": ("#06312b", "#d6fff0"),
        "Violet": ("#1a0a3a", "#d8b4ff"), "Fire": ("#2a0000", "#ffb347")}
for n, (d, l) in DUOS.items():
    FILTERS["Duotone " + n] = (lambda d, l: lambda im: ImageOps.colorize(ImageOps.grayscale(im), d, l))(d, l)
FILTERS = {k: keep_alpha(f) for k, f in FILTERS.items()}

# ---------------------------------------------------------------- operazioni (usate da editor, batch e macro)
def apply_op(im, op):
    k, a = op[0], op[1:]
    w, h = im.size
    if k == "filter": return FILTERS[a[0]](im)
    if k == "adjust":
        b, c, s, sh = a[0]
        for E, f in ((ImageEnhance.Brightness, b), (ImageEnhance.Contrast, c), (ImageEnhance.Color, s), (ImageEnhance.Sharpness, sh)):
            im = E(im).enhance(f)
        return im
    if k == "rot": return im.rotate(-a[0], expand=True, resample=Image.BICUBIC)
    if k == "flip": return ImageOps.mirror(im) if a[0] == "h" else ImageOps.flip(im)
    if k == "straighten":
        r = math.radians(abs(a[0])); asp = max(w, h) / min(w, h)
        sc = 1 / (math.cos(r) + asp * math.sin(r)); im = im.rotate(a[0], resample=Image.BICUBIC)
        cw, ch = w * sc, h * sc
        return im.crop((int((w - cw) / 2), int((h - ch) / 2), int((w + cw) / 2), int((h + ch) / 2)))
    if k == "resize": return im.resize((max(1, a[0]), max(1, a[1])), Image.LANCZOS)
    if k == "crop":
        l, t, r, b = a; return im.crop((int(l * w), int(t * h), max(int(l * w) + 1, int(r * w)), max(int(t * h) + 1, int(b * h))))
    if k == "circle":
        m = Image.new("L", im.size, 0); ImageDraw.Draw(m).ellipse([0, 0, w - 1, h - 1], fill=255)
        im = im.convert("RGBA"); im.putalpha(m); return im
    if k == "frame": return ImageOps.expand(im, border=a[0], fill=a[1])
    if k == "text":
        txt, x, y, sz, col = a; im = im.convert("RGBA"); d = ImageDraw.Draw(im); px = max(8, int(h * sz))
        try: f = ImageFont.truetype("DejaVuSans-Bold.ttf", px)
        except Exception: f = ImageFont.load_default()
        d.text((int(x * w), int(y * h)), txt, fill=col, font=f); return im
    if k == "local":
        name, l, t, r, b = a; m = Image.new("L", im.size, 0)
        ImageDraw.Draw(m).ellipse([l * w, t * h, r * w, b * h], fill=255)
        m = m.filter(ImageFilter.GaussianBlur(min(w, h) / 25)); im = im.convert("RGBA")
        return Image.composite(FILTERS[name](im).convert("RGBA"), im, m)
    if k == "magic":
        im = im.convert("RGBA"); ImageDraw.floodfill(im, (int(a[0] * (w - 1)), int(a[1] * (h - 1))), (0, 0, 0, 0), thresh=a[2]); return im
    return im

