# usage: python neardup.py [WINDOW=4]
# Finds pages that are re-photographs of the same notebook page (not byte-identical): SIFT matching + homography between each page and the
# next WINDOW pages, then compares the INK of the aligned pair.  Output: _work/neardup.json and a printed table.
#   relation 'same'      : ink of A is covered by B and vice versa (re-shot, nothing new)
#   relation 'A<B'       : B contains (almost) all ink of A plus extra writing  (A is a subset of B -> A can be skipped)
#   relation 'A>B'       : the reverse
import sys, os, json
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
sys.path.insert(0, os.path.dirname(__file__))
from common import *
import numpy as np, cv2

WIN = int(sys.argv[1]) if len(sys.argv) > 1 else 4
SIDE = 900


def load(page):
    pix = render(page, rot=ROT_DEFAULT.get(page, 0), maxside=SIDE)
    img = np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width, 3)
    g = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY).astype(np.float32)
    bg = cv2.GaussianBlur(cv2.dilate(g, np.ones((15, 15), np.uint8)), (41, 41), 0)
    n = np.clip(g / np.maximum(bg, 1), 0, 1)
    gray = (n * 255).astype(np.uint8)
    return gray


sift = cv2.SIFT_create(nfeatures=3000)
cache = {}
for p in range(1, 301):
    g = load(p)
    kp, des = sift.detectAndCompute(g, None)
    cache[p] = (g, kp, des)
print("features done")
bf = cv2.BFMatcher(cv2.NORM_L2)
survey = json.load(open(os.path.join(PROJ, "_work", "survey.json")))
res = []
for a in range(1, 301):
    for b in range(a + 1, min(300, a + WIN) + 1):
        if survey[str(a)]["md5"] == survey[str(b)]["md5"]:
            continue
        ga, ka, da = cache[a]
        gb, kb, db = cache[b]
        if da is None or db is None or len(ka) < 30 or len(kb) < 30:
            continue
        m = bf.knnMatch(da, db, k=2)
        good = [x[0] for x in m if len(x) == 2 and x[0].distance < 0.75 * x[1].distance]
        if len(good) < 40:
            continue
        src = np.float32([kb[g.trainIdx].pt for g in good]).reshape(-1, 1, 2)
        dst = np.float32([ka[g.queryIdx].pt for g in good]).reshape(-1, 1, 2)
        H, mask = cv2.findHomography(src, dst, cv2.RANSAC, 4.0)
        if H is None:
            continue
        inl = int(mask.sum())
        if inl < 40:
            continue
        # warp b onto a, compare ink
        wb = cv2.warpPerspective(gb, H, (ga.shape[1], ga.shape[0]), flags=cv2.INTER_LINEAR, borderValue=255)
        valid = cv2.warpPerspective(np.full(gb.shape, 255, np.uint8), H, (ga.shape[1], ga.shape[0])) > 0
        ia = (ga < 150) & valid
        ib = (wb < 150) & valid
        da_ = cv2.dilate(ia.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0
        db_ = cv2.dilate(ib.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0
        only_a = float((ia & ~db_).sum()) / max(1, ia.sum())   # fraction of A's ink absent in B
        only_b = float((ib & ~da_).sum()) / max(1, ib.sum())
        cover = float(valid.mean())
        rel = "same" if only_a < 0.12 and only_b < 0.12 else ("A<B" if only_a < 0.12 else ("A>B" if only_b < 0.12 else "overlap"))
        res.append(dict(a=a, b=b, inliers=inl, cover=round(cover, 2), only_a=round(only_a, 3), only_b=round(only_b, 3), rel=rel))
json.dump(res, open(os.path.join(PROJ, "_work", "neardup.json"), "w"), indent=0)
print(f"{'A':>4} {'B':>4} {'inl':>5} {'cover':>5} {'onlyA':>6} {'onlyB':>6}  relation")
for r in sorted(res, key=lambda r: -r["inliers"]):
    if r["inliers"] >= 80 and r["cover"] > 0.5:
        print(f"{r['a']:>4} {r['b']:>4} {r['inliers']:>5} {r['cover']:>5} {r['only_a']:>6} {r['only_b']:>6}  {r['rel']}")
