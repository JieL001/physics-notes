# usage: python render.py PAGE [--side 1900] [--rot 0|90|180|270]
# renders ONE page to  view/pPAGE.jpg  (sideways pages known to the tool are rotated automatically; override with --rot, clockwise degrees)
import sys, os, argparse
sys.path.insert(0, os.path.dirname(__file__))
from common import *

ap = argparse.ArgumentParser()
ap.add_argument("page", type=int)
ap.add_argument("--side", type=int, default=1900)
ap.add_argument("--rot", type=int, default=None)
a = ap.parse_args()
rot = ROT_DEFAULT.get(a.page, 0) if a.rot is None else a.rot
pix = render(a.page, rot=rot, maxside=a.side)
fn = os.path.join(VIEW, f"p{a.page:03d}.jpg")
pix.save(fn, jpg_quality=85)
print(fn, pix.width, "x", pix.height, f"(rot={rot})")
