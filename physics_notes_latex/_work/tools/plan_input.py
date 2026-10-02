# usage: python plan_input.py NN        (NN = chapter code, e.g. 11)
# Prints (and saves to _work/plan_in/chNN.txt) a compact listing of every block of the chapter, for the outline planner.
# Needs _work/blocks.json (run collect.py first).
import sys, os, re, json, difflib
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
PROJ = r"C:\Users\PC\Desktop\zuoye\intern\physics_notes_latex"
ch = sys.argv[1]
blocks = [b for b in json.load(open(os.path.join(PROJ, "_work", "blocks.json"), encoding="utf8")) if b["ch"] == ch]


def plain(s, n):
    s = re.sub(r"%[^\n]*", " ", s)
    s = re.sub(r"\\(?:begin|end)\{[^}]*\}(?:\[[^\]]*\])?", " ", s)
    s = re.sub(r"\\notefig(?:\[[^\]]*\])?\{[^}]*\}", "[图]", s)
    s = re.sub(r"\\[a-zA-Z]+\*?", " ", s)
    s = re.sub(r"[{}$\\]", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s[:n]


lines = [f"# chapter {ch}: {len(blocks)} blocks, pages {sorted(set(b['page'] for b in blocks))[:3]}..{sorted(set(b['page'] for b in blocks))[-3:]}"]
for b in blocks:
    lines.append(f"[{b['id']}] kind={b['kind']} sec={b['sec']} cont={b['cont']} exp={b['exp']} alt={b['alt']} len={len(b['body'])} | {plain(b['body'], 110)}")
# near-duplicate hints
norm = {b["id"]: re.sub(r"\s+", "", re.sub(r"%[^\n]*", "", b["body"])) for b in blocks}
dups = []
ids = list(norm)
for i, a in enumerate(ids):
    for c in ids[i + 1:]:
        if min(len(norm[a]), len(norm[c])) < 60:
            continue
        r = difflib.SequenceMatcher(None, norm[a], norm[c]).quick_ratio()
        if r > 0.9 and difflib.SequenceMatcher(None, norm[a], norm[c]).ratio() > 0.9:
            dups.append((a, c))
if dups:
    lines.append("# near-duplicate pairs (ratio>0.9): " + ", ".join(f"{a}~{c}" for a, c in dups))
out = "\n".join(lines)
os.makedirs(os.path.join(PROJ, "_work", "plan_in"), exist_ok=True)
open(os.path.join(PROJ, "_work", "plan_in", f"ch{ch}.txt"), "w", encoding="utf8").write(out)
print(out)
