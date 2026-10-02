# usage: python collect.py [--pages 1-300]
# Parses PROJ/_work/blocks/pNNN.tex, validates the format, writes
#   PROJ/_work/blocks.json            all blocks (id, page, ch, sec, kind, flags, body)
#   PROJ/_work/chapters_in/chNN.tex   all blocks of chapter NN in page order (what the chapter composers read)
# and prints statistics + every format problem it finds.
import sys, os, re, glob, json, collections
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
PROJ = r"C:\Users\PC\Desktop\zuoye\intern\physics_notes_latex"
BL = os.path.join(PROJ, "_work", "blocks")
OUT = os.path.join(PROJ, "_work", "chapters_in")
os.makedirs(OUT, exist_ok=True)
CH = {"01": "运动的描述与匀变速直线运动", "02": "相互作用——力", "03": "牛顿运动定律", "04": "曲线运动",
      "05": "万有引力与航天", "06": "机械能", "07": "动量", "08": "机械振动与机械波", "09": "静电场",
      "10": "恒定电流", "11": "磁场", "12": "电磁感应", "13": "交变电流与传感器", "14": "电磁振荡与电磁波",
      "15": "光学", "16": "热学", "17": "原子物理", "18": "测量仪器与实验基础", "90": "数学与物理方法（通用）", "99": "无法归类"}
KINDS = {"knowledge", "formula", "method", "problem", "derivation", "diagram", "summary", "note", "misc"}
lo, hi = 1, 300
if "--pages" in sys.argv:
    a, b = sys.argv[sys.argv.index("--pages") + 1].split("-"); lo, hi = int(a), int(b)

problems, blocks, seen_ids, pages_ok = [], [], set(), []
_sv = json.load(open(os.path.join(PROJ, "_work", "survey.json")))
_first = {}
dup_of = {}
for _p in sorted(_sv, key=int):
    _m = _sv[_p]["md5"]
    if _m in _first: dup_of[int(_p)] = _first[_m]
    else: _first[_m] = int(_p)
for _k, _v in json.load(open(os.path.join(PROJ, "_work", "dups_extra.json"))).items(): dup_of[int(_k)] = _v
json.dump({str(k): v for k, v in dup_of.items()}, open(os.path.join(PROJ, "_work", "dups.json"), "w"), indent=0)
for page in range(lo, hi + 1):
    if page in dup_of: continue
    fn = os.path.join(BL, f"p{page:03d}.tex")
    if not os.path.exists(fn):
        problems.append((page, "页文件不存在")); continue
    txt = open(fn, encoding="utf8").read()
    if not re.search(rf"^%%%PAGE\s+0*{page}\b", txt, flags=re.M): problems.append((page, "缺少 %%%PAGE 行或页码不符"))
    if not re.search(rf"^%%%PAGEEND\s+0*{page}\b", txt, flags=re.M): problems.append((page, "缺少 %%%PAGEEND 行"))
    pages_ok.append(page)
    n_start = len(re.findall(r"^%%%BLOCK ", txt, flags=re.M)); n_end = len(re.findall(r"^%%%END\s*$", txt, flags=re.M))
    if n_start != n_end: problems.append((page, f"BLOCK/END 数量不一致 {n_start}/{n_end}"))
    for m in re.finditer(r"^%%%BLOCK ([^\n]*)\n(.*?)^%%%END[ \t]*$", txt, flags=re.M | re.S):
        try:
            hdr = {k_: v_.strip() for k_, v_ in re.findall(r"(\w+)=(.*?)(?=\s+\w+=|\s*$)", m.group(1))}
            if not hdr: raise ValueError
        except ValueError:
            problems.append((page, "块头格式错误: " + m.group(1)[:80])); continue
        bid = hdr.get("id", "?")
        if bid in seen_ids: problems.append((page, f"重复的块 id {bid}"))
        seen_ids.add(bid)
        if not bid.startswith(f"{page:03d}-"): problems.append((page, f"块 id {bid} 与页码不符"))
        ch = hdr.get("ch", "")
        if ch not in CH: problems.append((page, f"块 {bid} 的 ch={ch!r} 不在分类表中"))
        if "sec" not in hdr: problems.append((page, f"块 {bid} 缺少 sec"))
        if hdr.get("kind") not in KINDS: problems.append((page, f"块 {bid} 的 kind={hdr.get('kind')!r} 不合法"))
        body = m.group(2).rstrip() + "\n"
        for f in re.findall(r"\\notefig(?:\[[^\]]*\])?\{([^}]+)\}", body):
            if not os.path.exists(os.path.join(PROJ, f.replace("/", os.sep))): problems.append((page, f"块 {bid} 引用的图不存在: {f}"))
        if re.search(r"\\(?:chapter|section|subsection|subsubsection)\b", body): problems.append((page, f"块 {bid} 含分节命令"))
        blocks.append(dict(id=bid, page=page, ch=ch, sec=hdr.get("sec", ""), kind=hdr.get("kind", ""), exp=hdr.get("exp", "0"),
                           alt=hdr.get("alt", "none"), cont=hdr.get("cont", "none"), y=hdr.get("y", ""), body=body, raw_header=m.group(1)))
json.dump(blocks, open(os.path.join(PROJ, "_work", "blocks.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)

by = collections.defaultdict(list)
for b in blocks: by[b["ch"]].append(b)
for old in glob.glob(os.path.join(OUT, "ch*.tex")): os.remove(old)
print(f"pages parsed: {len(pages_ok)}   blocks: {len(blocks)}")
print(f"{'ch':<3} {'章':<22} {'blocks':>6} {'chars':>8} {'pages':>5}  top sections")
for ch in sorted(by):
    bl = by[ch]
    chars = sum(len(b["body"]) for b in bl)
    secs = collections.Counter(b["sec"] for b in bl).most_common(5)
    print(f"{ch:<3} {CH.get(ch, '?'):<20} {len(bl):>6} {chars:>8} {len(set(b['page'] for b in bl)):>5}  " + "; ".join(f"{s}×{n}" for s, n in secs))
    with open(os.path.join(OUT, f"ch{ch}.tex"), "w", encoding="utf8") as f:
        for b in bl:
            f.write(f"%%%BLOCK {b['raw_header']}\n{b['body']}%%%END\n")
if problems:
    print(f"\n!! {len(problems)} format problems:")
    for p, msg in problems[:80]: print(f"  p{p:03d}: {msg}")
else:
    print("\nno format problems")
