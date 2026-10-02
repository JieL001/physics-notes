# usage: python autoplan.py [NN ...]      (default: every chapter present in blocks.json)
# Zero-cost fallback outline: sections = distinct `sec` names in order of first appearance, blocks inside a section in page order.
# Writes _work/plans/chNN.json  (only if no hand/agent-made plan exists, unless --force).
import sys, os, json, collections
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
PROJ = r"C:\Users\PC\Desktop\zuoye\intern\physics_notes_latex"
W = os.path.join(PROJ, "_work")
CH = {"01": "运动的描述与匀变速直线运动", "02": "相互作用——力", "03": "牛顿运动定律", "04": "曲线运动",
      "05": "万有引力与航天", "06": "机械能", "07": "动量", "08": "机械振动与机械波", "09": "静电场",
      "10": "恒定电流", "11": "磁场", "12": "电磁感应", "13": "交变电流与传感器", "14": "电磁振荡与电磁波",
      "15": "光学", "16": "热学", "17": "原子物理", "18": "测量仪器与实验基础", "90": "数学与物理方法（通用）", "99": "其他学科与未归类笔记"}
blocks = json.load(open(os.path.join(W, "blocks.json"), encoding="utf8"))
want = [a for a in sys.argv[1:] if not a.startswith("--")] or sorted({b["ch"] for b in blocks})
force = "--force" in sys.argv
os.makedirs(os.path.join(W, "plans"), exist_ok=True)
for ch in want:
    fn = os.path.join(W, "plans", f"ch{ch}.json")
    if os.path.exists(fn) and not force:
        print(f"ch{ch}: plan exists, kept"); continue
    secs = collections.OrderedDict()
    for b in blocks:
        if b["ch"] == ch:
            secs.setdefault(b["sec"] or "未命名", []).append(b["id"])
    plan = {"ch": ch, "title": CH.get(ch, ch), "auto": True, "sections": [{"title": s, "blocks": ids} for s, ids in secs.items()]}
    json.dump(plan, open(fn, "w", encoding="utf8"), ensure_ascii=False, indent=1)
    print(f"ch{ch}: {len(plan['sections'])} sections, {sum(len(v) for v in secs.values())} blocks")
