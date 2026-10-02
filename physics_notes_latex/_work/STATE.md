# 高中物理笔记 → LaTeX：进度与续跑说明（最后更新 2026-10-03 02:50，+08）

## 现状（数字以 `python tools/remaining.py` 的输出为准；它会重算还剩哪些页并刷新 units_remaining.json）
- 02:50 之后又转录了 p137–163、p164–173 的若干单元（见 blocks/ 目录里有哪些文件）；被打断的单元：用 remaining.py 看“缺配图的页”，对这些页补跑 `crop_batch.py --blocks` + `texcheck_all.py`。
- **p162 整页失焦**：它的 7 张配图是用 `scratchpad\crop_soft_p162.py` 裁的（默认裁图会洗掉淡笔迹），**不要对 p162 重跑 crop_batch / 不要覆盖 figures/p162_*.png**。
- p012 页眉区、p127/p129/p131 等页右上角的“混合气体 ρ=1.429 g·L⁻¹”是下层纸（化学）透出的字，已按 ch=99 小块处理或忽略。
- 下面“现状”各条是 02:50 的快照：
- 原件 `Desktop\高中物理笔记.pdf`：300 页手写照片（无文字层）。已切成 10 页一块的小 PDF（会话临时目录 `scratchpad\split\`，丢了可用 PyMuPDF 重切）。
- **已转录（50%）**：全局页 1–136（除重复页 12、96）+ 195–199 → 139 个独立页、796 个块、662 张配图、366 处 `\unclear`、246 处 `% CHECK`。`collect.py` 校验无格式问题。已覆盖章：01–15、17 + 90（方法）+ 99（非物理）；**16 热学、18 测量仪器还没出现**（应在后面的页）。
- **已排除（重复页，不用转录）**：151–157、201–206、251–257（字节级相同，见 `dups.json`），12→11、96→95（同页重拍，`dups_extra.json`）。
- **待转录（50%）**：139 页 = 28 个单元，见 `units_remaining.json`（第一个单元 137–141，最后 297–300）。若有页文件已写出但缺配图/未过编译的（被打断的单元），先对这些页跑 `crop_batch.py --blocks` + `texcheck_all.py`。
- 试编译（已转录部分，按小节名自动分组的临时大纲）：`main.tex` 上次 290 页/0 错误（124 页时）。

## 额度
- 2026-10-03 02:50：每周（所有模型）99%，2026-10-05 04:00(+08) 重置；5 小时窗口 50%。用户选择“用到额度耗尽”，已跑到周额度线。
- 用户另有“云会话额度 $250（11-05 过期）”，但云会话只能从 GitHub 仓库拉文件，笔记图片不在仓库里（本机无 gh、目录不是 git 仓库）。用户 02:30 说“先不用云额度”；若之后要用：需用户建私有 GitHub 仓库、同意上传页面图片，云端 agent 只做“读图→写块文件+%FIG 行”，裁图/编译检查仍在本地。
- 实测：一个 5 页单元约 21–41 万新增 token，周额度约 0.5–1%；剩余 28 个单元约需 15–25%，必须等重置（或用户开启额外用量）。

## 续跑步骤（Workflow 工具需用户明确授权；默认用 Agent 工具，≤3 并发，每完成一个补一个）
1. 读 `_work/GUIDE.md`（规范）和 `_work/AGENT_PROMPT.txt`（提示词模板）。
2. 对 `units_remaining.json` 里的每个单元起一个 `general-purpose` agent（不指定 model），产出 `_work/blocks/pNNN.tex`、`figures/pNNN_x.png`。提示词里加一句“推理要简练”可省约 20–30% 成本。
3. 每放 2 个单元查一次 `get_usage`；周额度 ≥ ~97% 或 5 小时 ≥ ~90% 就停。会话被打断时：已落盘的 `pNNN.tex` 是完整的（每页一次写完），缺的页重新分配即可；配图在最后一步统一 `crop_batch.py --blocks`。
4. 全部转录完：`python tools/collect.py`（校验，必须无格式问题）→ 针对性复核（见下）→ 章节大纲 → 组装 → 编译。

## 工具（都在 `_work/tools/`，实际运行的副本在会话 scratchpad\tools；`common.py` 里写死了 scratchpad 路径 SCR，换会话要改）
`prep.py`（整单元渲染+坐标尺）、`crop_batch.py --blocks …`（按块里 `%FIG` 行裁图+联系表）、`texcheck.py/texcheck_all.py`（片段编译检查，带 `--disable-installer`）、`collect.py`（解析/校验/按章导出 `chapters_in/`、`blocks.json`）、`survey.py/neardup.py`（查重复页）、`plan_input.py NN`（章节块清单，供大纲规划）、`autoplan.py --force`（零成本按 sec 自动分组的大纲）、`assemble.py NN…`（按 `plans/chNN.json` 逐字组装，含覆盖校验）、`build_main.py`（生成 main.tex）。
编译：`xelatex --disable-installer -interaction=nonstopmode main.tex`（MiKTeX 完整路径见记忆；不要引入 cancel/physics/mhchem/circuitikz 宏包；写 .tex 用 Write 工具，别用 bash heredoc——会吞反斜杠；python 里写 `\unclear` 之类要用 chr(92)）。

## 最终汇编设计（待做）
- 章节：01–18 物理章（实验归入所属物理章，块上有 `exp=1`）、90 数学与物理方法（放最后一章）、99 非物理（化学/生物，放附录，不混进物理章）。综合题已按“核心考点”单归一章，`alt=` 仅作备注。
- 大纲：对每章用便宜的 agent 读 `plan_input.py` 的清单（只看 sec/摘要，不看全文），把相近 sec 归并成规范小节并排序，输出 `plans/chNN.json`（格式见 assemble.py 头部注释）；`assemble.py` 逐字组装并校验“每个块恰好出现一次”。当前 `autoplan` 的小节名太碎（目录里一章有几十节），最终必须做这一步。
- 复核：不做全量二次阅读（太贵）。用“墨迹量 vs 转录字数”的启发式 + 各 agent 自报的存疑点，挑高风险页做针对性复核；抽查 p005 逐字对得上，仅少量连笔字存疑。p112 页眉区残字（疑为 p111 溢出）已标 `DUP?`。
- 交付：`main.tex`（+ chapters/、figures/、preamble.tex）与编译好的 PDF；附“待核对清单”（所有 `% CHECK` 与 `\unclear`）。
