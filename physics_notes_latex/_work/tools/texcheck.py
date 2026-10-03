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
from common import PROJ, SCR

XE = r"C:\Users\PC\AppData\Local\Programs\MiKTeX\miktex\bin\x64\xelatex.exe" if os.name == "nt" else "xelatex"
NL = chr(10)


def xe_cmd(texfile):
    if os.name == "nt":
        return [XE, "--disable-installer", "-interaction=nonstopmode", texfile]
    # TeX Live on Linux: ctex's default Fandol fonts lack ⑪–⑳, so use the Noto CJK fontset (the .tex files stay unchanged)
    job = os.path.splitext(texfile)[0]
    return [XE, "-interaction=nonstopmode", "-jobname=" + job, r"\PassOptionsToClass{fontset=ubuntu}{ctexbook}\input{" + texfile + "}"]


def winpath(p):
    m = re.match(r"^/([a-zA-Z])/(.*)$", p)
    return (m.group(1).upper() + ":/" + m.group(2)) if m else p


fn = os.path.abspath(winpath(sys.argv[1]))
full = "--doc" in sys.argv
tag = hashlib.md5(fn.encode()).hexdigest()[:8]
wd = os.path.join(PROJ, "_work", "tex", tag) if os.name == "nt" else os.path.join(SCR, "tex", tag)
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
        r"\def\notefigroot{" + pre + "/}",
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
    r = subprocess.run(xe_cmd(os.path.basename(main)),
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
# XeTeX logs "There is no φ (U+03C6) in font …" (older builds omit the U+ part); the glyph itself may be a newline (U+000A)
miss = sorted({f"U+{u}" if u and int(u, 16) < 0x21 else c for c, u in
               re.findall(r"Missing character: There is no ([\s\S])(?: \(U\+([0-9A-Fa-f]{4,6})\))? in font", log)})
if miss:
    print("MISSING CHARS (not typeset! put Greek letters / math symbols inside $...$, or replace them;"
          " U+000A usually means a capital Greek letter inside \\mathrm/\\unit):", " ".join(miss))
for w in re.findall(r"^[^\n]*(?:File `[^\n]*not found|Undefined control sequence)[^\n]*", log, flags=re.M)[:10]:
    print("WARN:", w)
bad = len(errs) > 0 or bool(miss)
print("RESULT:", "FAIL - fix the problems above" if bad else "OK")
sys.exit(1 if bad else 0)
