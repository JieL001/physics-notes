# usage: python remaining.py [UNIT_SIZE=5]
# Recomputes which pages still have no transcription file (excluding duplicate pages), prints the counts and rewrites
# _work/units_remaining.json.  Also lists page files that exist but whose figures are missing (interrupted units).
import sys, os, re, json, glob

PROJ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # tools live in PROJ/_work/tools
W = os.path.join(PROJ, "_work")
size = int(sys.argv[1]) if len(sys.argv) > 1 else 5
dups = {int(k) for k in json.load(open(os.path.join(W, "dups.json")))}
dups |= {int(k) for k in json.load(open(os.path.join(W, "dups_extra.json")))}
have = {int(os.path.basename(f)[1:4]) for f in glob.glob(os.path.join(W, "blocks", "p*.tex"))}
todo = [p for p in range(1, 301) if p not in dups and p not in have]
units = [todo[i:i + size] for i in range(0, len(todo), size)]
json.dump(units, open(os.path.join(W, "units_remaining.json"), "w"))
real = 300 - len(dups)
print(f"unique pages: {real} | transcribed: {real - len(todo)} ({(real - len(todo)) / real:.0%}) | remaining: {len(todo)} -> {len(units)} units")
if units:
    print("next unit:", units[0], "| last unit:", units[-1])
# interrupted units: page file present but a referenced figure is missing
missing = []
for f in sorted(glob.glob(os.path.join(W, "blocks", "p*.tex"))):
    txt = open(f, encoding="utf8").read()
    for fig in re.findall(r"\\notefig(?:\[[^\]]*\])?\{([^}]+)\}", txt):
        if not os.path.exists(os.path.join(PROJ, fig.replace("/", os.sep))):
            missing.append((os.path.basename(f), fig))
if missing:
    print("page files with MISSING figures (run crop_batch.py --blocks on these pages; do NOT re-crop p162, see STATE.md):")
    for m in missing[:40]:
        print("  ", m)
else:
    print("all referenced figures exist")
