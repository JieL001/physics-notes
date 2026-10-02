# usage: python crop_batch.py --blocks PAGEFILE1.tex PAGEFILE2.tex ...     (reads the '%FIG NAME x0 y0 x1 y1 [soft]' lines inside the page files)
#    or: python crop_batch.py SPECFILE
# SPECFILE: one figure per line:   PAGE NAME x0 y0 x1 y1 [soft]        (fractions of the page; '#' starts a comment)
#   e.g.   195 p195_a 0.12 0.33 0.42 0.52
# 'soft' = gentler cleaning for faint pencil / light-ink drawings that come out washed-out with the default cleaning.
# Crops every figure (cleaned) into  figures/NAME.png  and prints a CONTACT SHEET path (or several): Read that ONE image to check all crops
# (is the figure complete? labels cut off? too much unrelated text?).  Fix a bad crop by editing its line and re-running the spec.
import sys, os, re
sys.path.insert(0, os.path.dirname(__file__))
from common import *
import numpy as np, cv2

if sys.argv[1] == "--blocks":
    spec = []
    for fn_ in sys.argv[2:]:
        pg = int(re.search(r"p(\d{3})\.tex$", fn_).group(1))
        for l in open(fn_, encoding="utf8"):
            m = re.match(r"^%FIG\s+(\S+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)(.*)", l)
            if m: spec.append([str(pg), m.group(1), m.group(2), m.group(3), m.group(4), m.group(5)] + m.group(6).split()[:1])
    tag_src = sys.argv[2]
else:
    spec = [l.split("#")[0].split() for l in open(sys.argv[1], encoding="utf8")]
    spec = [s for s in spec if s]
    tag_src = sys.argv[1]
tiles = []
for s in spec:
    page, name = int(s[0]), s[1]
    x0, y0, x1, y1 = map(float, s[2:6])
    soft = "soft" in s[6:]
    fn, w, h = crop_figure(page, x0, y0, x1, y1, name, soft=soft)
    print(f"{name}: {w}x{h}" + ("  (soft)" if soft else ""))
    im = cv2.cvtColor(cv2.imread(fn), cv2.COLOR_BGR2RGB)
    sc = min(520 / im.shape[1], 400 / im.shape[0], 1.0)
    im = cv2.resize(im, (max(1, int(im.shape[1] * sc)), max(1, int(im.shape[0] * sc))), interpolation=cv2.INTER_AREA)
    t = np.full((430, 530, 3), 255, np.uint8)
    t[26:26 + im.shape[0], 4:4 + im.shape[1]] = im
    cv2.rectangle(t, (0, 0), (529, 429), (160, 160, 160), 1)
    cv2.putText(t, f"{name}  ({x0:.2f},{y0:.2f})-({x1:.2f},{y1:.2f})" + (" soft" if soft else ""), (4, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 0, 0), 1)
    tiles.append(t)
tag = os.path.splitext(os.path.basename(tag_src))[0]
per = 6
for k in range(0, len(tiles), per):
    grp = tiles[k:k + per]
    while len(grp) < per:
        grp.append(np.full((430, 530, 3), 255, np.uint8))
    sheet = np.vstack([np.hstack(grp[:3]), np.hstack(grp[3:])])
    fn = os.path.join(VIEW, f"sheet_{tag}_{k // per + 1}.jpg")
    cv2.imwrite(fn, cv2.cvtColor(sheet, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 85])
    print("CONTACT SHEET:", fn)
if not tiles:
    print("no figures in spec")
