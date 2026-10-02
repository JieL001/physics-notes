# usage: python crop.py PAGE x0 y0 x1 y1 NAME [--zoom] [--rot R] [--raw] [--soft]
#   x0 y0 x1 y1 are FRACTIONS (0..1) of the page as shown by prep.py / render.py (x to the right, y downward; the ruler on the images shows them).
#   --zoom : saves a high-resolution JPEG for YOU to read small handwriting:  view/zoom_NAME.jpg  (not for the document)
#   default: saves a cleaned figure to  figures/NAME.png   (prefer crop_batch.py when you have several figures)
#   --soft : gentler cleaning for faint pencil / light-ink drawings
import sys, os, argparse
sys.path.insert(0, os.path.dirname(__file__))
from common import *

ap = argparse.ArgumentParser()
ap.add_argument("page", type=int)
for n in ("x0", "y0", "x1", "y1"):
    ap.add_argument(n, type=float)
ap.add_argument("name")
ap.add_argument("--zoom", action="store_true")
ap.add_argument("--rot", type=int, default=None)
ap.add_argument("--raw", action="store_true")
ap.add_argument("--soft", action="store_true")
a = ap.parse_args()
assert 0 <= a.x0 < a.x1 <= 1 and 0 <= a.y0 < a.y1 <= 1, "coords must be fractions with x0<x1,y0<y1"
rot = ROT_DEFAULT.get(a.page, 0) if a.rot is None else a.rot
if a.zoom:
    clip = norm_clip(a.page, a.x0, a.y0, a.x1, a.y1, rot)
    pix = render(a.page, rot=rot, clip=clip, maxside=1800)
    fn = os.path.join(VIEW, f"zoom_{a.name}.jpg")
    pix.save(fn, jpg_quality=88)
    print(fn, pix.width, "x", pix.height)
    sys.exit()
fn, w, h = crop_figure(a.page, a.x0, a.y0, a.x1, a.y1, a.name, rot=rot, clean=not a.raw, soft=a.soft)
print(fn, w, "x", h)
