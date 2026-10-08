#!/bin/zsh
# Dung goi nop cho IPM.  zsh build-submit.sh
#
# Luat G7 cua nha, moi dieu deu tu mot ca hong that:
#   - goi nguon PHANG, khong long thu muc (he thong nop khong tim ra tep chinh o goc)
#   - dung MOT tep mang \documentclass (cover letter va thu tra loi nop rieng dang PDF)
#   - co san .bbl (latexmk tu chay BibTeX nen cong xanh tren goi THIEU .bbl)
#   - thu phong sach: giai nen ra thu muc TRONG, dung bang CHI pdflatex, phai ra dung so trang
#   - khong lan ghi chu noi bo vao thu muc nop
set -e
GOC=${0:a:h}
S=$GOC/submit
T=$GOC/_flat

rm -rf $S $T && mkdir -p $S $T

# ---------- 1. gom PHANG ----------
cp $GOC/paper/main.tex $T/
cp $GOC/paper/sections/*.tex $T/
cp $GOC/paper/frag-*.tex $T/   # manh dung chung: khoi tac gia va highlights
cp $GOC/paper/refs.bib $T/
cp $GOC/results/so-lieu*.tex $T/
cp $GOC/results/tables/*.tex $T/
# ⛔ Chi chep hinh bai THUC SU chen. Truoc day chep `figures/*.pdf` nen goi nguon van mang
# f5-theo-loai.pdf sau khi Hinh 7 da bi bo, va nguoi doc ngoai bat duoc o vong 2.
python3 - "$GOC" "$T" <<'PYFIG'
import glob, io, os, re, shutil, sys
goc, t = sys.argv[1], sys.argv[2]
src = "".join(io.open(f, encoding="utf-8").read()
              for f in glob.glob(os.path.join(goc, "paper", "sections", "*.tex"))
              + [os.path.join(goc, "paper", "main.tex")])
dung = set(re.findall(r"includegraphics\[[^\]]*\]\{\.\./figures/([^}]+)\}", src))
# ⛔ Hinh dau trang duoc chen qua MACRO (\HINHDAUTRANG) vi ban an danh dung ban da che.
# Phai no macro ay ra CA HAI ten, de goi nguon dung lai duoc ca hai ban.
if "\\HINHDAUTRANG.pdf" in dung:
    dung.discard("\\HINHDAUTRANG.pdf")
    dung |= {"f9-header.pdf", "f9-header-anon.pdf"}
for ten in sorted(dung):
    shutil.copy2(os.path.join(goc, "figures", ten), os.path.join(t, ten))
print("  chep %d hinh bai dung (bo qua %d hinh khong dung)"
      % (len(dung), len(glob.glob(os.path.join(goc, "figures", "*.pdf"))) - len(dung)))
PYFIG

# ---------- 2. viet lai duong dan ----------
cd $T
for f in *.tex; do
  perl -pi -e 's{\.\./figures/}{}g; s{\.\./results/tables/}{}g; s{\.\./results/}{}g; s{sections/}{}g' $f
done

# ---------- 3. dung, kem .bbl ----------
pdflatex -interaction=nonstopmode main.tex >/dev/null 2>&1 || true
bibtex main >/dev/null 2>&1 || true
pdflatex -interaction=nonstopmode main.tex >/dev/null 2>&1 || true
pdflatex -interaction=nonstopmode main.tex >/dev/null 2>&1 || true

TRANG=$(python3 -c "from pypdf import PdfReader; print(len(PdfReader('main.pdf').pages))")
GOCTRANG=$(python3 -c "from pypdf import PdfReader; print(len(PdfReader('$GOC/paper/main.pdf').pages))")
echo "  ban phang: $TRANG trang   ·   ban goc: $GOCTRANG trang"
[[ "$TRANG" == "$GOCTRANG" ]] || { echo "  HONG: so trang lech"; exit 1; }

# ---------- 4. don sach roi nen ----------
rm -f main.aux main.log main.out main.blg
cd $T && zip -qr $S/source.zip . -x '*.DS_Store'
cp $T/main.pdf $S/manuscript-full.pdf

# ---------- 4b. BON TEP he nop cua IPM doi rieng ----------
# Phan bien AN DANH HAI CHIEU: ban thao nop KHONG duoc mang chi tiet tac gia, va hinh dau
# trang phai dung ban DA CHE ma co quan (ma ay trung ten truong cua tac gia thu nhat).
cd $GOC/paper
for i in 1 2 3; do
  pdflatex -interaction=nonstopmode -jobname=manuscript-anon \
           "\\def\\ANON{1}\\input{main.tex}" >/dev/null 2>&1
  [[ $i == 1 ]] && bibtex manuscript-anon >/dev/null 2>&1
done
for f in highlights title-page cover-letter; do
  pdflatex -interaction=nonstopmode $f.tex >/dev/null 2>&1
  pdflatex -interaction=nonstopmode $f.tex >/dev/null 2>&1
done
cp $GOC/paper/cover-letter.pdf      $S/1-cover-letter.pdf
cp $GOC/paper/manuscript-anon.pdf   $S/2-manuscript-no-author-details.pdf
cp $GOC/paper/highlights.pdf        $S/3-highlights.pdf
cp $GOC/paper/title-page.pdf        $S/4-title-page-with-author-details.pdf
cd $GOC

# ---------- 5 va 6: thu phong sach + kiem goi, lam bang Python ----------
# ⛔ Phan nay tung viet bang shell va CHET am tham. Mau `$( ... | grep -c X; true )` duoi
# `set -e` cua zsh thoat ca script du da co `true`, va `grep -c` con in "0" roi thoat ma 1 nen
# `|| echo 0` sinh ra chuoi "0\n0". Hai bay trong mot dong. Python khong co ca hai.
python3 - "$GOC" <<'PYEOF'
import os, re, subprocess, sys, tempfile, zipfile
goc = sys.argv[1]
S = os.path.join(goc, "submit")
zp = os.path.join(S, "source.zip")
goc_trang = len(__import__("pypdf").PdfReader(os.path.join(goc, "paper", "main.pdf")).pages)
loi = []

def kiem(dk, ten, ct=""):
    if not dk:
        loi.append(ten)
    print("  %s %s%s" % ("DAT " if dk else "HONG", ten, ("  [" + ct + "]") if ct else ""))

cr = tempfile.mkdtemp()
with zipfile.ZipFile(zp) as z:
    z.extractall(cr)
os.path.exists(os.path.join(cr, "main.pdf")) and os.remove(os.path.join(cr, "main.pdf"))
for _ in range(2):
    subprocess.run(["pdflatex", "-interaction=nonstopmode", "main.tex"],
                   cwd=cr, capture_output=True)
pdf = os.path.join(cr, "main.pdf")
kiem(os.path.exists(pdf), "ban giai nen dung duoc bang CHI pdflatex")
if os.path.exists(pdf):
    n = len(__import__("pypdf").PdfReader(pdf).pages)
    kiem(n == goc_trang, "so trang khop ban goc", "%d vs %d" % (n, goc_trang))
    log = open(os.path.join(cr, "main.log"), encoding="utf-8", errors="ignore").read()
    kiem("not found" not in log.lower(), "khong tep nao 'not found'")
    kiem(len(re.findall(r"(?m)^!", log)) == 0, "0 loi LaTeX o ban giai nen")
    txt = subprocess.run(["pdftotext", pdf, "-"], capture_output=True, text=True).stdout
    kiem("[?]" not in txt, "khong dau '[?]' (thieu trich dan)")

with zipfile.ZipFile(zp) as z:
    ten = z.namelist()
    dc = [x for x in ten if x.endswith(".tex")
          and b"documentclass" in z.read(x)]
    kiem(len(dc) == 1, "dung MOT tep mang documentclass", ", ".join(dc))
    kiem(not [x for x in ten if "/" in x], "goi PHANG, khong thu muc long")
    kiem("main.bbl" in ten, "co san main.bbl")
    kiem(not [x for x in ten if x.endswith((".md", ".log", ".aux", ".out"))],
         "khong lan ghi chu noi bo hay tep trung gian",
         ", ".join(x for x in ten if x.endswith((".md", ".log", ".aux", ".out"))))
    print("  %d tep trong zip" % len(ten))

print()
for f in sorted(os.listdir(S)):
    print("  %-22s %8.1f KB" % (f, os.path.getsize(os.path.join(S, f)) / 1024.0))
print("\n=> %s" % ("GOI DAT, san sang nop" if not loi else "GOI HONG (%d loi)" % len(loi)))
sys.exit(0 if not loi else 1)
PYEOF
