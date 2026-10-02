# usage: python texcheck_all.py FILE1.tex FILE2.tex ...   -> runs texcheck.py on each and prints a compact report
import sys, os, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
bad = 0
for f in sys.argv[1:]:
    r = subprocess.run([sys.executable, os.path.join(HERE, "texcheck.py"), f], capture_output=True)
    out = r.stdout.decode("utf8", "replace").strip()
    ok = "RESULT: OK" in out
    print(("OK    " if ok else "FAIL  ") + os.path.basename(f))
    if not ok:
        bad += 1
        print(out)
print("ALL OK" if not bad else f"{bad} file(s) FAILED")
sys.exit(1 if bad else 0)
