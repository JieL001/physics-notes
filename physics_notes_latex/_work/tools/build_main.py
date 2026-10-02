# usage: python build_main.py      -> writes PROJ/main.tex from the chapters present in PROJ/chapters/
import os, re, sys
PROJ = r"C:\Users\PC\Desktop\zuoye\intern\physics_notes_latex"
ORDER = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12", "13", "14", "15", "16", "17", "18", "90"]
present = [c for c in ORDER if os.path.exists(os.path.join(PROJ, "chapters", f"ch{c}.tex"))]
appendix = os.path.exists(os.path.join(PROJ, "chapters", "ch99.tex"))
NL = chr(10)
L = []
L.append(r"\documentclass[UTF8,a4paper,11pt,openany]{ctexbook}")
L.append(r"\input{preamble.tex}")
L.append(r"\pagestyle{fancy}\fancyhf{}\fancyhead[LE]{\small\leftmark}\fancyhead[RO]{\small\rightmark}\fancyfoot[C]{\thepage}")
L.append(r"\setcounter{tocdepth}{2}")
L.append(r"\title{高中物理笔记（整理版）}")
L.append(r"\author{}")
L.append(r"\date{}")
L.append(r"\begin{document}")
L.append(r"\frontmatter")
L.append(r"\maketitle")
L.append(r"\tableofcontents")
L.append(r"\mainmatter")
for c in present:
    L.append(r"\input{chapters/ch" + c + "}")
if appendix:
    L.append(r"\appendix")
    L.append(r"\input{chapters/ch99}")
L.append(r"\end{document}")
open(os.path.join(PROJ, "main.tex"), "w", encoding="utf8").write(NL.join(L) + NL)
print("main.tex written with chapters:", present, "+ appendix ch99" if appendix else "")
