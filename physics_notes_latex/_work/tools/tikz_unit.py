# Coordinator helper for the TikZ redraw units listed in _work/tikz_units.json (unit numbers are 1-based).
#   python3 tikz_unit.py prompt K     -> the filled-in agent prompt for unit K (template: _work/TIKZ_PROMPT.txt)
#   python3 tikz_unit.py check K      -> tikzcheck on the unit's figures + texcheck_all on its pages, compact output
#   python3 tikz_unit.py status       -> redrawn/total per unit
import sys, os, json, subprocess, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import PROJ

HERE = os.path.dirname(os.path.abspath(__file__))
UNITS = json.load(open(os.path.join(PROJ, "_work", "tikz_units.json"), encoding="utf8"))


def done(f):
    return os.path.exists(os.path.join(PROJ, "figures_tikz", f + ".tex"))


cmd, k = sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 0
if cmd == "status":
    tot = red = 0
    for i, u in enumerate(UNITS, 1):
        n = sum(done(f) for f in u["figs"])
        tot += len(u["figs"]); red += n
        if n:
            print(f"unit {i:2d} pages {u['pages'][0]}-{u['pages'][-1]}: {n}/{len(u['figs'])}")
    print(f"TOTAL {red}/{tot}")
    sys.exit(0)
u = UNITS[k - 1]
if cmd == "prompt":
    t = open(os.path.join(PROJ, "_work", "TIKZ_PROMPT.txt"), encoding="utf8").read().split("\n", 2)[2]
    print(t.replace("{PAGES}", "、".join(map(str, u["pages"]))).replace("{PAGE_ARGS}", " ".join(map(str, u["pages"])))
           .replace("{N}", str(len(u["figs"]))).replace("{FIGS}", " ".join(u["figs"])).strip())
elif cmd == "check":
    r = subprocess.run([sys.executable, os.path.join(HERE, "tikzcheck.py")] + u["figs"], capture_output=True, text=True)
    lines = r.stdout.splitlines()
    print(f"unit {k} pages {u['pages']}: redrawn {sum(done(f) for f in u['figs'])}/{len(u['figs'])}")
    for ln in lines:
        if not ln.startswith("OK  ") or "rescale" in ln:
            print(ln)
    pages = [os.path.join(PROJ, "_work", "blocks", f"p{p:03d}.tex") for p in u["pages"]]
    r2 = subprocess.run([sys.executable, os.path.join(HERE, "texcheck_all.py")] + pages, capture_output=True, text=True)
    print("texcheck:", r2.stdout.strip().splitlines()[-1] if r2.returncode == 0 else r2.stdout.strip())
