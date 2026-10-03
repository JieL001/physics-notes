# 手绘配图 → TikZ 电脑重画规范（所有重画 agent 必读）

## 0. 目标
笔记 PDF 里的配图目前是从手机照片裁出来的手绘图（`figures/pNNN_x.png`）。你的任务：把分到你手上的每张图**用 TikZ 重新画成规整的电脑图**，存成 `figures_tikz/pNNN_x.tex`。书里的 `\notefig` 发现有这个文件就自动用它，没有就继续用照片——所以**画不好的图宁可不交（保留照片），也不要交一张错图**。

**保真第一**：原图里有的每一样东西都要有——每条线、每个箭头（方向要对）、每个字母/数字/中文标注（含下标、撇号）、角标记、虚线、阴影/斜线（地面、墙）、点、圆、曲线的大致形状与走向、红笔加的东西（用红色）。**不要添加**原图没有的元素或标注，不要“纠正”物理（原图画错也照画），不要改变各部分的相对位置和大致比例。看不清的标注写 `\unclear{最佳猜测}`。

**规整第二（同样必须做到）**：成品要像**教科书/试卷里的印刷插图**，而不是把手迹描一遍。
- **禁止描像素**：不要用原图像素当坐标（不要 `x=0.185mm, y=-0.185mm` 这类比例尺），不要用一长串 `plot[smooth] coordinates {…}` 去描手抖的线。先看懂图画的是什么，再用规整的几何元素重新构图，坐标用 cm，取到 0.1 cm（能取 0.5 cm 的倍数更好）。
- **手绘时想画成什么，就画成精确的什么**：圆 → `circle`；同心圆 → 同一个圆心；相切的圆 → 精确相切；直线 → 直线；矩形/方块 → `rectangle`；本应水平的（地面、能级、极板、水平面、桌面）→ 严格水平；本应竖直的 → 严格竖直；平行、等长、等间距、对称、直角 → 精确做到。
- **坐标轴**：横轴严格水平、纵轴严格竖直，两轴垂直相交；原图画歪了一律扶正（这不算“纠正物理”）。
- **电路**：导线横平竖直、走成矩形网格，元件放在导线上并对齐；电表画成“圆圈 + 字母”（用 `to[rmeter, t=A]`，或 `circle` + 字母且导线只接到圆周），**不要让导线穿过圆圈内部**，也不要画成双圈。
- **曲线**：用函数 `plot` 或 1–4 段 `.. controls ..` / `to[out=…, in=…]` 画成光滑曲线，保持原图走势（单调、凹凸、峰的位置与相对高低、交点、渐近线、起点终点）。
- **保留的是**：拓扑关系（什么连着什么、谁在谁里面）、相对位置与大致比例（上下左右、大小、哪段长、间距是越来越大还是越来越小）、全部标注及其相对位置、箭头方向。**故意**画成不规则的（任意形状的导体、弯曲的轨迹、波形）仍画不规则，但要用光滑曲线。
- **风格样例**（动笔前先 Read 其中两个）：`figures_tikz/p164_b.tex`（坐标图像）、`figures_tikz/p212_a.tex`（电路）、`figures_tikz/p209_a.tex`、`figures_tikz/p111_g.tex`。

## 1. 路径与工具（云端 Linux，命令用 python3）
```
PROJ  = /home/user/physics-notes/physics_notes_latex
原图  = PROJ/figures/pNNN_x.png            （只读）
页文件 = PROJ/_work/blocks/pNNN.tex         （只读：看图的上下文、转录员写的“图内标注”注释、题目文字）
输出  = PROJ/figures_tikz/pNNN_x.tex        （你要写的文件，每张图一个）
检查  = python3 PROJ/_work/tools/tikzcheck.py 名字1 名字2 …   （或 --pages 页1 页2 …）
```
`tikzcheck.py` 对每张图：单独编译、报错误、给出自然尺寸和目标宽度，并生成**对照表**（左原图 | 右重画），打印 `SHEET: 路径` —— **用 Read 看对照表逐项核对**。

## 2. 文件格式（严格）
```
% pNNN_x 的电脑重画（一句话说明是什么图）
\begin{tikzpicture}[line width=0.7pt, >={Stealth[length=2.2mm]}]
  ...
\end{tikzpicture}
```
- 只能有**一个** `tikzpicture` 环境；不要 `\documentclass`、`\usepackage`、`\begin{document}`、全局 `\tikzset`、`\begin{circuitikz}`（电路也写在 `tikzpicture` 里，circuitikz 的 `to[R]` 等元件照常可用）。
- 可用的库：arrows.meta, calc, positioning, shapes.geometric, decorations.pathmorphing（coil 弹簧、zigzag）, decorations.pathreplacing（brace 大括号）, decorations.markings（线段中间画箭头）, angles, quotes, patterns, intersections, through, backgrounds；circuitikz（已设 europeanresistors、americaninductors）。可用宏：`\red{}` `\unclear{}` `\unit{}` `\dd` `\nuc{}{}{}`。中文直接写在 node 里。
- **大小**：自然宽度大约等于 tikzcheck 给的目标宽度（= 原图在书里的显示宽度），为了标注清楚可放大到 1.5–2 倍；不要超过 15 cm。标注字号就用默认（书里会自动用 \small）。
- 坐标用 cm，整数或一位小数即可；**角弧必须用具名坐标**：`\coordinate (A) at (..);` 再 `\pic[draw, angle radius=0.5cm, "$\theta$", angle eccentricity=1.5] {angle = A--O--B};`（从射线 OA **逆时针**转到 OB；画反了会变成大角——这是最常见的错）。

## 3. 各类图的画法要点
- **坐标图像**（v-t、x-t、a-F、E-x、U-I…）：`\draw[->] (0,0) -- (4,0) node[right] {$t$};`；曲线用 `plot[domain=..,samples=..] (\x,{...})` 或 `.. controls ..`；虚线辅助线 `dashed`；轴上的刻度/截距标注照原图（`node[left] {$v_0$}`）。曲线的形状（上凸/下凹、交点、渐近、斜率大小关系）要和原图一致。
- **受力/运动示意**：物块 `\draw (0,0) rectangle (1,0.6);`，斜面三角形，地面 `\draw (0,0) -- (4,0);` + 斜线阴影 `\fill[pattern=north east lines] (0,0) rectangle (4,-0.15);`；力用粗箭头 `[->, thick]`，箭头起点在作用点；绳、杆为直线，滑轮为圆；弹簧 `\draw[decorate, decoration={coil, aspect=0.4, segment length=2mm, amplitude=2.5mm}] (0,0) -- (2,0);`；小球 `\draw (0,0) circle (0.15);` 或实心点。
- **电路**：导线直角走线；`to[R, l=$R$]` 电阻、`to[vR]` 电阻箱/可变电阻、`to[pR, n=p]` 滑动变阻器（滑片 `(p.wiper)`）、`to[battery1]` 电池（长线正极）、`to[nos, l=$S$]` 开关、`to[rmeter, t=A]` / `t=V` / `t=G` 电表、`to[lamp]` 灯泡、`to[C]` 电容、`to[L]` 线圈、`to[D]` 二极管、`node[circ]{}` 结点；元件标注 `l=` 在上/左、`l_=` 在下/右。元件的先后顺序、所在支路、电表/开关位置必须与原图一致。
- **磁场/电场**：垂直纸面向里 `\node at (x,y) {$\times$};` 网格排列，向外用 `\node {$\cdot$}` 或 `\fill (x,y) circle (1pt)` 加小圆圈；电场线、磁感线中间画箭头：`postaction={decorate}, decoration={markings, mark=at position 0.5 with {\arrow{>}}}`；粒子轨迹圆弧 `arc`；有界磁场区域用矩形/圆框住。
- **光路**：界面实线，法线 `dashed`，光线中间画箭头（markings），角用 angle pic。
- **大括号/尺寸**：`decorate, decoration={brace, amplitude=4pt}`；尺寸线 `\draw[|<->|] ...`。
- 红笔画的线、圈、字：`red!75!black`（文字可用 `\red{}`）。

**图外文字**：裁图时顺带裁进来的整行正文/公式（页文件里紧挨着这个 `\notefig` 的正文已经转录了它，或注释写明“图中已含”而正文也写出了），不要再画进图里（避免重复）；属于图本身的标注（轴名、物体名、数值、箭头旁的字）照画。

## 4. 跳过（不交文件、保留照片）的情况
- 图里主要是**手写文字/公式**而不是图形（裁图时把一块文字当成了图）；
- **照片性质**的内容（实物照片、看不清的涂改团）或残缺到无法判断原貌的图；
- 极其复杂、无法在合理代价内忠实重画的草图（如几十条交错曲线）。
跳过的图在最终回复里列出名字和原因（一句话）。贴在本子上的**印刷体题图**照样重画（它们本来就是规整的图）。

## 5. 流程（省调用）
1. 对单元里的每一页：同一轮里并行 Read 页文件 `blocks/pNNN.tex`（看每个 `\notefig` 周围的文字和“图内标注”注释）和该页所有原图 `figures/pNNN_*.png`。
2. 逐张写 `figures_tikz/pNNN_x.tex`（Write 工具，**一张图一次写完**；不要用 bash heredoc——会吞反斜杠）。
3. 整个单元写完后**一次**运行 `tikzcheck.py`（列出本单元全部图名）：先把 FAIL 的编译错误改掉；再 **Read 每一张 SHEET**，逐图核对：元素齐不齐、箭头方向、标注文字与位置、曲线形状、角度标在哪两条线之间、红笔部分；以及**是否规整**（轴/水平线/竖直线有没有歪、圆是不是正圆、导线是否横平竖直、有没有手抖的线）。有问题就 Edit 对应文件，再对改过的图重跑 tikzcheck。
4. 最后对本单元的页文件跑一次 `python3 PROJ/_work/tools/texcheck_all.py PROJ/_work/blocks/pNNN.tex …`，必须 ALL OK。
5. **只写** `figures_tikz/` 里本单元的文件；不要改页文件、原图、导言区和任何工具；不要运行 git / collect.py / assemble.py（别人同时在工作）。
6. 最终回复 ≤5 行：`DONE pages=…, redrawn=N/M, skipped=[名字:原因, …]`，以及最没把握的 1–3 张。
