# usage: python3 tikzcheck.py NAME [NAME ...]        (NAME like p164_a; or --pages 164 165 for every figure of those pages)
# For each figure that has a redraw  PROJ/figures_tikz/NAME.tex  (one tikzpicture, no preamble):
#   * compiles it alone (standalone + the same packages/macros as preamble.tex) and reports errors per figure;
#   * renders it and writes comparison sheets  (left: original photo crop figures/NAME.png | right: redraw)
#     -> prints "SHEET: path" lines: Read them to check every line, arrow, label and angle against the original;
#   * prints the redraw's natural size and the target width (= the \notefig width fraction x 16.6 cm).
# Figures without a figures_tikz file are listed as "not redrawn".
import sys, os, re, glob, subprocess, concurrent.futures as cf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import PROJ, SCR
import cv2, numpy as np

TIKZ = os.path.join(PROJ, "figures_tikz")
OUT = os.path.join(SCR, "tikz")
os.makedirs(OUT, exist_ok=True)
LINEWIDTH_CM = 16.6

HEADER = r"""\documentclass[tikz,border=4pt]{standalone}
\usepackage[UTF8@FONTSET@]{ctex}
\usepackage{amsmath,amssymb,mathtools,bm,graphicx,xcolor}
\usepackage[normalem]{ulem}
\usetikzlibrary{arrows.meta,calc,positioning,shapes.geometric,decorations.pathmorphing,
  angles,quotes,decorations.pathreplacing,decorations.markings,patterns,intersections,through,backgrounds}
\usepackage[europeanresistors,americaninductors]{circuitikz}
\newcommand{\red}[1]{\textcolor{red!75!black}{#1}}
\newcommand{\unclear}[1]{\textcolor{orange!80!black}{[#1\,\textbf{?}]}}
\newcommand{\struck}[1]{\sout{#1}}
\newcommand{\dd}{\mathrm{d}}
\newcommand{\nuc}[3]{{}^{#1}_{#2}\mathrm{#3}}
\newcommand{\unit}[1]{\,\mathrm{#1}}
\newcommand{\ee}{\mathrm{e}}
\DeclareSymbolFont{pnupgreek}{OT1}{cmr}{m}{n}
\AtBeginDocument{\DeclareMathSymbol{\Delta}{\mathord}{pnupgreek}{"01}\DeclareMathSymbol{\Omega}{\mathord}{pnupgreek}{"0A}%
  \DeclareMathSymbol{\Phi}{\mathord}{pnupgreek}{"08}\DeclareMathSymbol{\Theta}{\mathord}{pnupgreek}{"02}}
\begin{document}
\small
"""


def target_widths():
    w = {}
    for f in glob.glob(os.path.join(PROJ, "_work", "blocks", "p*.tex")):
        for m in re.finditer(r"\\notefig(?:\[([\d.]+)\])?\{figures/([^}]+)\.png\}", open(f, encoding="utf8").read()):
            w[m.group(2)] = float(m.group(1) or 0.6)
    return w


def build(name):
    src = os.path.join(TIKZ, name + ".tex")
    job = os.path.join(OUT, name)
    fontset = "" if os.name == "nt" else ",fontset=ubuntu"
    open(job + ".tex", "w", encoding="utf8").write(HEADER.replace("@FONTSET@", fontset) + r"\input{" + src.replace(chr(92), "/") + "}\n" + r"\end{document}" + "\n")
    cmd = ["xelatex", "-interaction=nonstopmode", "-file-line-error", "-output-directory", OUT, job + ".tex"]
    if os.name == "nt":
        cmd.insert(1, "--disable-installer")
    try:
        subprocess.run(cmd, capture_output=True, timeout=180, cwd=PROJ)
    except subprocess.TimeoutExpired:
        return name, ["TIMEOUT"], None
    log = open(job + ".log", encoding="utf8", errors="replace").read()
    errs = [m.group(0).strip() for m in re.finditer(r"^(?:\S*\.tex:\d+: |! ).*(?:\n.*){0,2}", log, flags=re.M)][:6]
    miss = sorted(set(re.findall(r"Missing character: There is no ([\s\S])(?: \(U\+[0-9A-F]+\))? in font", log)))
    if miss:
        errs.append("MISSING CHARS: " + " ".join(repr(c) for c in miss))
    pdf = job + ".pdf"
    if not os.path.exists(pdf) or os.path.getmtime(pdf) < os.path.getmtime(job + ".tex"):
        return name, errs or ["no PDF produced"], None
    subprocess.run(["pdftoppm", "-r", "200", "-singlefile", "-png", pdf, job], capture_output=True)
    size = subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout
    mp = re.search(r"Pages:\s+(\d+)", size)
    pages = int(mp.group(1)) if mp else -1
    if pages != 1:
        errs.append(f"{pages} pages: a redraw file must contain exactly ONE tikzpicture")
    m = re.search(r"Page size:\s+([\d.]+) x ([\d.]+) pts", size)
    wh = (float(m.group(1)) / 72 * 2.54 - 0.28, float(m.group(2)) / 72 * 2.54 - 0.28) if m else None  # minus the 4pt border
    return name, errs, wh


def tile(path, label, W=600, H=430):
    t = np.full((H, W, 3), 255, np.uint8)
    im = cv2.imread(path) if path and os.path.exists(path) else None
    if im is not None:
        sc = min((W - 16) / im.shape[1], (H - 40) / im.shape[0], 3.0)
        im = cv2.resize(im, (max(1, int(im.shape[1] * sc)), max(1, int(im.shape[0] * sc))), interpolation=cv2.INTER_AREA)
        y0, x0 = 32 + (H - 36 - im.shape[0]) // 2, (W - im.shape[1]) // 2
        t[y0:y0 + im.shape[0], x0:x0 + im.shape[1]] = im
    else:
        cv2.putText(t, "(no image)", (20, H // 2), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 200), 2)
    cv2.putText(t, label, (6, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (160, 40, 0), 2)
    cv2.rectangle(t, (0, 0), (W - 1, H - 1), (190, 190, 190), 1)
    return t


args = sys.argv[1:]
if args and args[0] == "--pages":
    names = sorted({os.path.basename(f)[:-4] for p in args[1:] for f in glob.glob(os.path.join(PROJ, "figures", f"p{int(p):03d}_*.png"))})
    tw = target_widths()
    names = [n for n in names if n in tw]          # only figures that the transcription actually uses
else:
    names = args
tw = target_widths()
todo = [n for n in names if os.path.exists(os.path.join(TIKZ, n + ".tex"))]
skipped = [n for n in names if n not in todo]
with cf.ThreadPoolExecutor(max_workers=4) as ex:
    results = list(ex.map(build, todo))
bad = 0
rows = []
for name, errs, wh in results:
    tgt = tw.get(name, 0.6) * LINEWIDTH_CM
    size = f"{wh[0]:.1f}x{wh[1]:.1f}cm" if wh else "?"
    flag = "FAIL" if errs else "OK  "
    bad += bool(errs)
    note = ""
    if wh and (wh[0] > max(2.2 * tgt, 9) or wh[0] < 0.5 * tgt):
        note = f"  <- natural width {wh[0]:.1f}cm vs target ~{tgt:.1f}cm: rescale"
    print(f"{flag} {name}: {size} (target width ~{tgt:.1f}cm){note}")
    for e in errs:
        print("      " + e.replace(chr(10), " | ")[:300])
    rows.append(np.hstack([tile(os.path.join(PROJ, "figures", name + ".png"), name + "  original"),
                           tile(os.path.join(OUT, name + ".png") if wh else None, name + "  redraw")]))
for k in range(0, len(rows), 3):
    fn = os.path.join(OUT, f"sheet_{results[k][0]}_{k // 3 + 1}.jpg")
    cv2.imwrite(fn, np.vstack(rows[k:k + 3]), [cv2.IMWRITE_JPEG_QUALITY, 88])
    print("SHEET:", fn)
if skipped:
    print("not redrawn (no figures_tikz file):", " ".join(skipped))
print("ALL OK" if not bad else f"{bad} figure(s) FAILED")
sys.exit(1 if bad else 0)
