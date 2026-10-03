# Coordinator helper for the TikZ redraw units listed in _work/tikz_units.json (unit numbers are 1-based).
#   python3 tikz_unit.py prompt K     -> the filled-in agent prompt for unit K (template: _work/TIKZ_PROMPT.txt)
#   python3 tikz_unit.py check K      -> tikzcheck on the unit's figures + texcheck_all on its pages, compact output
#   python3 tikz_unit.py status       -> redrawn/total per unit
#   python3 tikz_unit.py commit K     -> mark unit K checked, commit its figures_tikz files (they are git-excluded until then), push
#   python3 tikz_unit.py next         -> mark the next unlaunched unit as launched and print its number + prompt
import sys, os, json, subprocess, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import PROJ

HERE = os.path.dirname(os.path.abspath(__file__))
UNITS = json.load(open(os.path.join(PROJ, "_work", "tikz_units.json"), encoding="utf8"))


def done(f):
    return os.path.exists(os.path.join(PROJ, "figures_tikz", f + ".tex"))


PROG = os.path.join(PROJ, "_work", "tikz_progress.txt")


def progress():
    txt = open(PROG, encoding="utf8").read()
    get = lambda key: [int(x) for x in re.search(rf"^{key}:(.*)$", txt, re.M).group(1).split()]
    return txt, get("launched"), get("checked")


def set_progress(key, nums):
    txt = open(PROG, encoding="utf8").read()
    txt = re.sub(rf"^{key}:.*$", f"{key}: " + " ".join(map(str, sorted(set(nums)))), txt, flags=re.M)
    open(PROG, "w", encoding="utf8").write(txt)


cmd, k = sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 0
if cmd == "next":
    _, launched, _ = progress()
    k = next((i for i in range(1, len(UNITS) + 1) if i not in launched), 0)
    if not k:
        print("NO MORE UNITS")
        sys.exit(0)
    set_progress("launched", launched + [k])
    cmd = "prompt"
    print(f"UNIT {k} (pages {UNITS[k - 1]['pages'][0]}-{UNITS[k - 1]['pages'][-1]})")
if cmd == "commit":
    u = UNITS[k - 1]
    _, _, checked = progress()
    set_progress("checked", checked + [k])
    root = os.path.dirname(PROJ)
    files = [os.path.join(PROJ, "figures_tikz", f + ".tex") for f in u["figs"] if done(f)]
    pg = ", ".join(map(str, u["pages"]))
    msg = (f"TikZ redraws for pages {pg} (unit {k}, {len(files)}/{len(u['figs'])} figures)\n\n"
           "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n"
           "Claude-Session: https://claude.ai/code/session_01Dr8pvvUAcRjFDp5VRyuCrp\n")
    subprocess.run(["git", "add", "-f"] + files + [PROG], cwd=root, check=True)
    subprocess.run(["git", "commit", "-q", "-m", msg], cwd=root, check=True)
    r = subprocess.run(["git", "push", "-q", "origin", "claude/serene-meitner-3p3st7"], cwd=root, capture_output=True, text=True)
    print(subprocess.run(["git", "log", "--oneline", "-1"], cwd=root, capture_output=True, text=True).stdout.strip(),
          "| push", "OK" if r.returncode == 0 else "FAILED: " + r.stderr.strip()[-300:])
    sys.exit(0)
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
