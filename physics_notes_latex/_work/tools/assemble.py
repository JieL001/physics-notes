# usage: python assemble.py NN [NN ...] [--append-missing]
# Assembles chapters/chNN.tex VERBATIM from _work/blocks.json following _work/plans/chNN.json:
#   {"ch":"11","title":"磁场","sections":[{"title":"..","blocks":["010-02",..]},
#                                         {"title":"..","subsections":[{"title":"..","blocks":[..]}]}]}
# Every block id of the chapter must be placed exactly once (coverage check). --append-missing puts forgotten ids into a last section.
import sys, os, re, json
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
PROJ = r"C:\Users\PC\Desktop\zuoye\intern\physics_notes_latex"
W = os.path.join(PROJ, "_work")
blocks = {b["id"]: b for b in json.load(open(os.path.join(W, "blocks.json"), encoding="utf8"))}
args = [a for a in sys.argv[1:] if not a.startswith("--")]
append_missing = "--append-missing" in sys.argv
rc = 0


def body_of(b):
    lines = [l for l in b["body"].split("\n") if not l.startswith("%FIG")]
    s = "\n".join(lines).strip("\n")
    return f"% ---- block {b['id']} (原稿第{b['page']}页) kind={b['kind']} ----\n{s}\n"


for ch in args:
    plan = json.load(open(os.path.join(W, "plans", f"ch{ch}.json"), encoding="utf8"))
    want = [i for i, b in blocks.items() if b["ch"] == ch]
    placed = []

    def walk(sec):
        for key in ("blocks",):
            for i in sec.get(key, []):
                placed.append(i)
        for sub in sec.get("subsections", []):
            for i in sub.get("blocks", []):
                placed.append(i)

    for sec in plan["sections"]:
        walk(sec)
    missing = [i for i in want if i not in placed]
    extra = [i for i in placed if i not in want]
    dup = sorted({i for i in placed if placed.count(i) > 1})
    unknown = [i for i in extra if i not in blocks]
    other_ch = [i for i in extra if i in blocks]
    if unknown or other_ch or dup:
        print(f"ch{ch}: PLAN ERROR  unknown ids={unknown}  ids from other chapters={other_ch}  placed twice={dup}")
        rc = 1
        continue
    if missing:
        if append_missing:
            plan["sections"].append({"title": "补充内容", "blocks": missing})
            print(f"ch{ch}: appended {len(missing)} unplaced blocks to a last section: {missing}")
        else:
            print(f"ch{ch}: COVERAGE ERROR  {len(missing)} blocks not placed: {missing}")
            rc = 1
            continue
    out = [f"% 本文件由 assemble.py 按 _work/plans/ch{ch}.json 逐字组装，请勿手改（改 plan 或 blocks 后重新生成）。", f"\\chapter{{{plan['title']}}}", f"\\label{{ch:{ch}}}", ""]
    n = 0
    for sec in plan["sections"]:
        out.append(f"\\section{{{sec['title']}}}")
        for i in sec.get("blocks", []):
            out.append(body_of(blocks[i])); n += 1
        for sub in sec.get("subsections", []):
            out.append(f"\\subsection{{{sub['title']}}}")
            for i in sub.get("blocks", []):
                out.append(body_of(blocks[i])); n += 1
        out.append("")
    os.makedirs(os.path.join(PROJ, "chapters"), exist_ok=True)
    open(os.path.join(PROJ, "chapters", f"ch{ch}.tex"), "w", encoding="utf8").write("\n".join(out))
    print(f"ch{ch}: OK  {n}/{len(want)} blocks placed, {len(plan['sections'])} sections -> chapters/ch{ch}.tex")
sys.exit(rc)
