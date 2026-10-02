# usage: python prep.py PAGE [PAGE ...]
# For every page writes three images into VIEW (each has a ruler on the left/top edge giving PAGE FRACTIONS 0..1, used for crop coordinates):
#   pNNN.jpg    whole page (overview / layout)
#   pNNN_a.jpg  top part    (y 0.00-0.55) at ~0.75x native resolution  <- read the small handwriting here
#   pNNN_b.jpg  bottom part (y 0.45-1.00) at ~0.75x native resolution
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from common import *
import numpy as np, cv2

FONT = cv2.FONT_HERSHEY_SIMPLEX


def with_ruler(img, x0f, x1f, y0f, y1f):
    h, w = img.shape[:2]
    bl, bt = 52, 30
    cv = np.full((h + bt, w + bl, 3), 255, np.uint8)
    cv[bt:, bl:] = img
    for k in range(0, 21):
        f = k / 20
        if y0f - 1e-6 <= f <= y1f + 1e-6:
            y = bt + int(round((f - y0f) / (y1f - y0f) * (h - 1)))
            cv2.line(cv, (bl - (14 if k % 2 == 0 else 7), y), (bl, y), (200, 0, 0), 1)
            if k % 2 == 0:
                cv2.putText(cv, f"{f:.1f}", (1, min(y + 5, h + bt - 2)), FONT, 0.5, (200, 0, 0), 1)
        if x0f - 1e-6 <= f <= x1f + 1e-6:
            x = bl + int(round((f - x0f) / (x1f - x0f) * (w - 1)))
            cv2.line(cv, (x, bt - (14 if k % 2 == 0 else 7)), (x, bt), (200, 0, 0), 1)
            if k % 2 == 0:
                cv2.putText(cv, f"{f:.1f}", (max(x - 12, 0), 12), FONT, 0.45, (200, 0, 0), 1)
    return cv


def shot(page, rot, y0, y1, maxside):
    clip = norm_clip(page, 0, y0, 1, y1, rot)
    pix = render(page, rot=rot, clip=clip, maxside=maxside)
    return np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width, 3)


for a in sys.argv[1:]:
    page = int(a)
    rot = ROT_DEFAULT.get(page, 0)
    for suffix, (y0, y1, ms) in {"": (0, 1, 1400), "_a": (0, 0.55, 1568), "_b": (0.45, 1.0, 1568)}.items():
        img = with_ruler(shot(page, rot, y0, y1, ms), 0, 1, y0, y1)
        fn = os.path.join(VIEW, f"p{page:03d}{suffix}.jpg")
        cv2.imwrite(fn, cv2.cvtColor(img, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 84])
    print(f"p{page:03d}: {VIEW}/p{page:03d}.jpg  _a.jpg  _b.jpg" + (f"   (page auto-rotated rot={rot})" if rot else ""))
