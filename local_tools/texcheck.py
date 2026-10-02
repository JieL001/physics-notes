# usage: python texcheck.py FILE.tex [--doc]
#   Compiles FILE.tex (a LaTeX *fragment*: it is \input into  ctexbook + preamble.tex  inside a \chapter) with xelatex and prints errors.
#   --doc : FILE.tex is already a complete document (compile as is).
# Figures are resolved relative to the project folder (write  figures/xxx.png ).
import sys, os, subprocess, re, hashlib
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
sys.path.insert(0, os.path.dirname(__file__))
from common import PROJ

XE = r"C:\Users\PC\AppData\Local\Programs\MiKTeX\miktex\bin\x64\xelatex.exe"
NL = chr(10)


def winpath(p):
    m = re.match(r"^/([a-zA-Z])/(.*)$", p)
    return (m.group(1).upper() + ":/" + m.group(2)) if m else p


fn = os.path.abspath(winpath(sys.argv[1]))
full = "--doc" in sys.argv
tag = hashlib.md5(fn.encode()).hexdigest()[:8]
wd = os.path.join(PROJ, "_work", "tex", tag)
os.makedirs(wd, exist_ok=True)
if full:
    main = fn
    cwd = os.path.dirname(fn)
else:
    main = os.path.join(wd, "check.tex")
    cwd = wd
    pre = PROJ.replace(chr(92), "/")
    src = NL.join([
        r"\documentclass[UTF8,a4paper,11pt]{ctexbook}",
        r"\input{" + pre + r"/preamble.tex}",
        r"\graphicspath{{" + pre + "/}}",
        r"\begin{document}",
        r"\chapter{check}",
        r"\input{" + fn.replace(chr(92), "/") + "}",
        r"\end{document}",
        "",
    ])
    open(main, "w", encoding="utf8").write(src)
try:
    r = subprocess.run([XE, "--disable-installer", "-interaction=nonstopmode", os.path.basename(main)],
                       cwd=cwd, capture_output=True, timeout=240)
except subprocess.TimeoutExpired:
    print("TIMEOUT (infinite loop or missing-package prompt?)")
    sys.exit(2)
log = r.stdout.decode("utf8", "replace").replace(chr(13), "")
errs = [m.group(0) for m in re.finditer(r"^! [^\n]*\n(?:[^\n]*\n){0,3}", log, flags=re.M)]
pages = re.search(r"Output written on .*\((\d+) pages?", log)
print("ERRORS:", len(errs), "| pages:", pages.group(1) if pages else "no PDF")
for e in errs[:25]:
    print(e.strip(), NL + "---")
miss = sorted(set(re.findall(r"Missing character: There is no (.) in font", log)))
if miss:
    print("MISSING CHARS (not typeset! put Greek letters / math symbols inside $...$, or replace them):", " ".join(miss))
for w in re.findall(r"^[^\n]*(?:File `[^\n]*not found|Undefined control sequence)[^\n]*", log, flags=re.M)[:10]:
    print("WARN:", w)
bad = len(errs) > 0 or bool(miss)
print("RESULT:", "FAIL - fix the problems above" if bad else "OK")
sys.exit(1 if bad else 0)
