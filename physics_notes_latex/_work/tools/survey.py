# usage: python survey.py   -> PROJ/_work/survey.json  (+ prints duplicate / blank / rotated candidates)
# Local, no model calls: per page md5 of the embedded photo, ink fraction, text-line orientation score, 64-bit dHash.
import sys, os, json, hashlib, glob
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
sys.path.insert(0, os.path.dirname(__file__))
from common import *
import numpy as np, cv2

res = {}
for k in range(1, 31):
    f = glob.glob(os.path.join(SCR, "split", f"chunk_{k:02d}_p*.pdf"))[0]
    d = fitz.open(f)
    for i in range(d.page_count):
        page = (k - 1) * 10 + i + 1
        p = d[i]
        info = d.extract_image(p.get_images(full=True)[0][0])
        md5 = hashlib.md5(info["image"]).hexdigest()
        arr = cv2.imdecode(np.frombuffer(info["image"], np.uint8), cv2.IMREAD_COLOR)
        h, w = arr.shape[:2]
        s = 600 / max(h, w)
        sm = cv2.resize(arr, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA).astype(np.float32)
        g = sm.mean(axis=2)
        bg = cv2.GaussianBlur(cv2.dilate(g, np.ones((15, 15), np.uint8)), (31, 31), 0)
        n = np.clip(g / np.maximum(bg, 1), 0, 1)
        ink = n < 0.62
        # trim a 4% margin (desk / page edge)
        mh, mw = int(ink.shape[0] * 0.04), int(ink.shape[1] * 0.04)
        core = ink[mh:-mh, mw:-mw]
        frac = float(core.mean())
        rowp = core.mean(axis=1); colp = core.mean(axis=0)
        orient = float(rowp.var() / (colp.var() + 1e-9))        # >1 : horizontal text lines (upright or upside-down)
        dh = cv2.resize(cv2.cvtColor(sm.astype(np.uint8), cv2.COLOR_BGR2GRAY), (9, 8), interpolation=cv2.INTER_AREA).astype(np.int32)
        bits = (dh[:, 1:] > dh[:, :-1]).flatten()
        res[page] = dict(md5=md5, ink=round(frac, 4), orient=round(orient, 2), dhash="".join("1" if b else "0" for b in bits), w=w, h=h)
json.dump(res, open(os.path.join(PROJ, "_work", "survey.json"), "w"), indent=0)

import collections
byhash = collections.defaultdict(list)
for p, r in res.items(): byhash[r["md5"]].append(p)
print("byte-identical page groups:", [v for v in byhash.values() if len(v) > 1] or "none")
pages = sorted(res)
near = []
for i, a in enumerate(pages):
    for b in pages[i + 1:]:
        hd = sum(x != y for x, y in zip(res[a]["dhash"], res[b]["dhash"]))
        if hd <= 4 and res[a]["md5"] != res[b]["md5"]: near.append((a, b, hd))
print("near-duplicate candidates (dHash dist<=4):", near or "none")
print("blank-ish pages (ink<0.004):", [p for p in pages if res[p]["ink"] < 0.004])
print("low-ink pages (0.004-0.012):", [(p, res[p]["ink"]) for p in pages if 0.004 <= res[p]["ink"] < 0.012])
print("orientation suspects (orient<1.0):", [(p, res[p]["orient"]) for p in pages if res[p]["orient"] < 1.0])
print("ink stats  min/median/max:", min(r["ink"] for r in res.values()), float(np.median([r["ink"] for r in res.values()])), max(r["ink"] for r in res.values()))
print("pilot pages ink:", {p: res[p]["ink"] for p in (195, 196, 197, 198, 199, 1, 2, 3, 4, 5)})
