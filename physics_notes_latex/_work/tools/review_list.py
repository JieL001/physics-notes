# usage: python review_list.py        (run collect.py first; reads _work/blocks.json)
# Writes PROJ/待核对清单.md: every "% … CHECK …" comment and every \unclear{…} in the transcription, page by page,
# with block id / chapter / section, so the owner can check them against the original photos.
import sys, os, re, json, collections
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
PROJ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # tools live in PROJ/_work/tools
W = os.path.join(PROJ, "_work")
CH = {"01": "运动的描述与匀变速直线运动", "02": "相互作用——力", "03": "牛顿运动定律", "04": "曲线运动",
      "05": "万有引力与航天", "06": "机械能", "07": "动量", "08": "机械振动与机械波", "09": "静电场",
      "10": "恒定电流", "11": "磁场", "12": "电磁感应", "13": "交变电流与传感器", "14": "电磁振荡与电磁波",
      "15": "光学", "16": "热学", "17": "原子物理", "18": "测量仪器与实验基础", "90": "数学与物理方法", "99": "其他学科与未归类"}


def comment_of(line):
    """text after the first unescaped % (None if the line has no comment)"""
    m = re.search(r"(?<!\\)%", line)
    return (line[:m.start()], line[m.end():]) if m else (line, None)


def unclear_args(s):
    out, i = [], 0
    while True:
        i = s.find("\\unclear{", i)
        if i < 0:
            return out
        j, depth = i + len("\\unclear{"), 1
        while j < len(s) and depth:
            depth += {"{": 1, "}": -1}.get(s[j], 0)
            j += 1
        out.append(s[i + len("\\unclear{"):j - 1])
        i = j


def short(s, n):
    s = re.sub(r"\s+", " ", s).strip()
    return s if len(s) <= n else s[:n - 1] + "…"


blocks = json.load(open(os.path.join(W, "blocks.json"), encoding="utf8"))
by_page = collections.OrderedDict()
n_check = n_unclear = 0
for b in sorted(blocks, key=lambda b: (b["page"], b["id"])):
    items = []
    for line in b["body"].split("\n"):
        if line.startswith("%FIG"):
            continue
        code, com = comment_of(line)
        if com and "CHECK" in com:
            items.append("CHECK：" + short(com.split("CHECK", 1)[1].lstrip(":：　 "), 160)
                         + (f"　← `{short(code, 60)}`" if code.strip() else ""))
            n_check += 1
        for u in unclear_args(code):
            items.append(f"看不清：`{short(u, 40) or '…'}`　← `{short(code, 60)}`")
            n_unclear += 1
    if items:
        by_page.setdefault(b["page"], []).append((b, items))

L = ["# 待核对清单", "",
     f"自动生成（`python3 _work/tools/review_list.py`，数据来自 `_work/blocks.json`）。共 **{n_check}** 处 CHECK、**{n_unclear}** 处“看不清”，分布在 **{len(by_page)}** 页。",
     "",
     "- **CHECK**：转录员认为原稿疑似笔误、前后矛盾或字形拿不准，已**照原样**转录并加注的地方。",
     "- **看不清**：手写字迹辨认不清，反引号里是最佳猜测；PDF 里排成橙色的 `[… ?]`。",
     "- 每条后面的 `← …` 是该处所在的 LaTeX 源码片段，方便在 `_work/blocks/pNNN.tex` 里搜索修改；改完重新运行 collect.py → assemble.py → 编译。",
     "- 转录员自报的“最需二次核对”重点（p165 以后）另见 `_work/agent_reports.md`。", ""]
for page, lst in by_page.items():
    L.append(f"## 第 {page} 页")
    for b, items in lst:
        L.append(f"- **{b['id']}**（{b['ch']} {CH.get(b['ch'], '')} · {b['sec']}）")
        L.extend(f"  - {it}" for it in items)
    L.append("")
open(os.path.join(PROJ, "待核对清单.md"), "w", encoding="utf8").write("\n".join(L))
print(f"待核对清单.md: {n_check} CHECK, {n_unclear} unclear, {len(by_page)} pages")
