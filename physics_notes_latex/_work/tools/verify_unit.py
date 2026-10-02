# usage: python verify_unit.py PAGE [PAGE ...]
# Acceptance check for finished transcription units (run by the coordinator, not by the transcription agents):
#   page file exists, has matching %%%PAGE / %%%PAGEEND lines, every %FIG is on its own line, every \notefig has a %FIG line
#   and an existing PNG, then texcheck on all pages.  Prints one line per page and "UNIT OK" / "UNIT FAIL".
import sys, os, re, subprocess
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(HERE))
BL = os.path.join(PROJ, "_work", "blocks")
bad = 0
files = []
for a in sys.argv[1:]:
    p = int(a)
    fn = os.path.join(BL, f"p{p:03d}.tex")
    if not os.path.exists(fn):
        print(f"p{p:03d}: MISSING page file")
        bad += 1
        continue
    txt = open(fn, encoding="utf8").read()
    probs = []
    if not re.search(rf"^%%%PAGE\s+0*{p}\b", txt, flags=re.M): probs.append("no %%%PAGE line")
    if not re.search(rf"^%%%PAGEEND\s+0*{p}\b", txt, flags=re.M): probs.append("no %%%PAGEEND line")
    dup = re.search(rf"^%%%PAGE\s+0*{p}\b.*\bdup=(\d+)", txt, flags=re.M)
    mid = [l for l in txt.splitlines() if "%FIG" in l and not l.startswith("%FIG")]
    if mid: probs.append(f"{len(mid)} %FIG not at line start")
    figs = set(re.findall(r"^%FIG\s+(\S+)", txt, flags=re.M))
    used = re.findall(r"\\notefig(?:\[[^\]]*\])?\{figures/([^}]+)\.png\}", txt)
    nofig = [u for u in used if u not in figs]
    if nofig: probs.append("notefig without %FIG: " + ",".join(nofig))
    miss = [u for u in used if not os.path.exists(os.path.join(PROJ, "figures", u + ".png"))]
    if miss: probs.append("missing PNG: " + ",".join(miss))
    nblk = len(re.findall(r"^%%%BLOCK", txt, flags=re.M))
    soft = len(re.findall(r"^%FIG\s+\S+(?:\s+[\d.]+){4}\s+soft", txt, flags=re.M))
    info = f"blocks={nblk} figs={len(used)}" + (f" soft={soft}" if soft else "") + (f" DUP of p{int(dup.group(1)):03d}" if dup else "")
    print(f"p{p:03d}: {'OK  ' if not probs else 'FAIL'} {info}" + ("" if not probs else "  <- " + "; ".join(probs)))
    bad += bool(probs)
    files.append(fn)
if files:
    r = subprocess.run([sys.executable, os.path.join(HERE, "texcheck_all.py")] + files, capture_output=True)
    out = r.stdout.decode("utf8", "replace").strip()
    print(out.splitlines()[-1] if r.returncode == 0 else out)
    bad += r.returncode != 0
print("UNIT OK" if not bad else "UNIT FAIL")
sys.exit(1 if bad else 0)
