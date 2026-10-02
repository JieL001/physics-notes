import glob, os, sys, json
try:
    import pymupdf as fitz  # PyMuPDF >= 1.24 (plain `import fitz` prints a deprecation notice there)
except ImportError:
    import fitz

# The tools live in PROJ/_work/tools, so PROJ is found from this file's location (same code on Windows and Linux).
PROJ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# SCR: scratch folder for page views, contact sheets and compile checks (not part of the project).
if os.name == "nt":
    SCR = r"C:\Users\PC\AppData\Local\Temp\claude\C--Users-PC-Desktop-zuoye-intern\4ab7915c-80d6-4141-b5c1-42a845c952d7\scratchpad"
else:
    SCR = os.environ.get("PN_SCR", "/tmp/claude-0/-home-user-pp2masdetc/7a27f1ad-3fba-50b0-accf-4a54517bd549/scratchpad/pn")
# source photos: GitHub repo layout <repo>/source/p001-010.pdf … p291-300.pdf; fallback: the old split chunks in SCR/split
SRC = os.path.join(os.path.dirname(PROJ), "source")
VIEW = os.path.join(SCR, "view")
os.makedirs(VIEW, exist_ok=True)
FIGS = os.path.join(PROJ, "figures")
LOG = os.path.join(PROJ, "_work", "crops.jsonl")

# pages whose photo / writing is sideways: rotated by default (clockwise degrees; verified visually). Other pages: 0.
ROT_DEFAULT = {72: 270, 209: 270, 239: 270}


def open_page(page):
    k = (page - 1) // 10 + 1
    f = (glob.glob(os.path.join(SRC, f"p{k * 10 - 9:03d}-*.pdf")) or glob.glob(os.path.join(SCR, "split", f"chunk_{k:02d}_p*.pdf")))[0]
    d = fitz.open(f)
    return d[(page - 1) % 10]


def render(page, rot=0, clip=None, maxside=1900, native=False):
    p = open_page(page)
    r = p.rect
    if native:  # native photo resolution (page rect 1 pt == ~2.3 px)
        img = p.get_images(full=True)[0]
        z = img[2] / r.width
    else:
        z = maxside / max(r.width, r.height) if clip is None else maxside / max(clip.width, clip.height)
    m = fitz.Matrix(z, z).prerotate(rot)
    return p.get_pixmap(matrix=m, clip=clip, alpha=False)


def norm_clip(page, x0, y0, x1, y1, rot=0):
    """fractions are relative to the ROTATED (upright) page as shown by prep.py / render.py; returns the clip rect in page space"""
    p = open_page(page)
    r = p.rect
    W, H = (r.width, r.height) if rot % 180 == 0 else (r.height, r.width)  # visual frame size
    vis = fitz.Rect(x0 * W, y0 * H, x1 * W, y1 * H)
    if rot % 360 == 0:
        return vis

    def inv(pt):
        x, y = pt
        if rot % 360 == 90:
            return (y, r.height - x)
        if rot % 360 == 180:
            return (r.width - x, r.height - y)
        if rot % 360 == 270:
            return (r.width - y, x)

    a = inv((vis.x0, vis.y0))
    b = inv((vis.x1, vis.y1))
    return fitz.Rect(min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1]))


def crop_figure(page, x0, y0, x1, y1, name, rot=None, clean=True, maxw=1500, soft=False):
    """crop a (cleaned) figure from the native-resolution photo -> PROJ/figures/name.png ; returns (path, w, h)
    soft=True: gentler cleaning for faint pencil / light-ink drawings that the default washes out"""
    import numpy as np, cv2
    rot = ROT_DEFAULT.get(page, 0) if rot is None else rot
    clip = norm_clip(page, x0, y0, x1, y1, rot)
    pix = render(page, rot=rot, clip=clip, native=True)
    img = np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width, 3).astype(np.float32)
    if clean:
        h, w = img.shape[:2]
        small = cv2.resize(img, (max(8, w // 4), max(8, h // 4)), interpolation=cv2.INTER_AREA)
        k = max(31, (min(h, w) // 6) | 1)
        ks = max(3, k // 4) | 1
        bg = cv2.dilate(small, np.ones((ks, ks), np.uint8))
        bg = cv2.GaussianBlur(bg, (ks | 1, ks | 1), 0)
        bg = cv2.resize(bg, (w, h), interpolation=cv2.INTER_LINEAR)
        n = np.clip(img / np.maximum(bg, 1), 0, 1)
        lo, hi = (0.70, 0.95) if soft else (0.55, 0.84)
        img = np.clip((n - lo) / (hi - lo), 0, 1) * 255  # paper + faint ruled lines -> white, ink -> black, red stays red
    img = img.astype(np.uint8)
    if img.shape[1] > maxw:
        sc = maxw / img.shape[1]
        img = cv2.resize(img, (maxw, int(img.shape[0] * sc)), interpolation=cv2.INTER_AREA)
    os.makedirs(FIGS, exist_ok=True)
    fn = os.path.join(FIGS, f"{name}.png")
    cv2.imwrite(fn, cv2.cvtColor(img, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_PNG_COMPRESSION, 9])
    with open(LOG, "a", encoding="utf8") as f:
        f.write(json.dumps(dict(page=page, name=name, bbox=[x0, y0, x1, y1], rot=rot, **({"soft": True} if soft else {}))) + chr(10))
    return fn, img.shape[1], img.shape[0]
