#!/usr/bin/env python3
"""E10: ba truong hanh chinh, co VAN BAN CHUAN, phep thu GHEP CAP.  python3 code/e10_bon_truong.py

⭐ Vi sao phep do nay SACH trong khi E8 bi nhiem: no chay HOAN TOAN trong long mot dan so, la
tap van ban da quet cua kho luu tru. Khong so hai kho khac nhau. E11 da cho thay 1422/1422 tep
mang quy uoc dat ten luu tru deu co lop chu hong, nen day la mot dan so dong nhat.

Van ban chuan lay tu he thong luu tru (ten tep), da xac nhan bang MAT tren anh dung lai:
`So: 540/2015/QD-DHKT` va `So: 630/QD-DHKT` khop dung ten tep.
Khuon ten: <so>_<loai>_<nam>_<coquan>[_<ngay>-<thang>]  => chuan cho BA truong:
    T1 so hieu · T2 ngay ban hanh (chi 501 tep co) · T3 co quan ban hanh

Hai nguon doc, cung mot anh trang:
    A = lop chu nhung san     B = OCR hien dai

Thong ke: McNemar ghep cap tren bien nhi phan dung/sai (moi tai lieu cho MOT cap), kem odds
ratio; hieu chinh Holm cho ba truong. Wilson 95% cho tung ti le.

TU KIEM: van ban chuan cho NGAY phai duoc kiem lai, bang cach doi chieu voi nam in trong bai
o nhung ca OCR doc sach; neu khong khop thi ten tep KHONG phai chuan cho ngay va phai bo T2.
"""
import argparse, collections, csv, glob, io, math, os, random, re, subprocess, sys, tempfile
import warnings
warnings.filterwarnings("ignore")

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(GOC, "results")
sys.path.insert(0, os.path.join(GOC, "do"))
from do_lop_chu import cac_pdf, SEED          # noqa: E402
from do_truong import gap_dau                  # noqa: E402

KHUON = re.compile(r"^(\d{3,4})_([A-Z]{2,4})_(\d{4})_([A-Z]+)(?:_(\d{2})-(\d{2}))?", re.I)
DOAN_SO = re.compile(r"\bso\s*[:.]?\s*(.{0,30}?)/\s*(qd|tb|cv|kh|hd|bc|th)\b")
NGAY_CHU = re.compile(r"\bngay\s+(\d{1,2})\s+thang\s+(\d{1,2})\s+nam\s+(\d{4})")
NGAY_SO = re.compile(r"\bngay\s+(\d{1,2})\s*/\s*(\d{1,2})\s*/\s*(\d{4})")
CO_QUAN = {"DHKT": ["dhkt", "kien truc"], "NA": ["dhkt", "kien truc"]}
loi = []


def kiem(dk, ten, ct=""):
    if not dk:
        loi.append(ten)
    print("  %s %s%s" % ("DAT " if dk else "HONG", ten, ("  [" + ct + "]") if ct else ""))


def wilson(k, n, z=1.96):
    if not n:
        return 0.0, 0.0
    p = k / float(n)
    d = 1 + z * z / n
    t = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, t - h), min(1.0, t + h)


def mcnemar(b, c):
    """b = A dung B sai, c = A sai B dung. Tra ve (p hai duoi, odds ratio)."""
    from scipy import stats
    n = b + c
    if n == 0:
        return 1.0, float("nan")
    p = stats.binomtest(min(b, c), n, 0.5).pvalue
    orat = (c / b) if b else float("inf")
    return p, orat


def holm(ps):
    m = len(ps)
    thu = sorted(range(m), key=lambda i: ps[i])
    ra = [0.0] * m
    truoc = 0.0
    for r, i in enumerate(thu):
        v = min(1.0, (m - r) * ps[i])
        truoc = max(truoc, v)
        ra[i] = truoc
    return ra


def doc_A(p):
    return subprocess.run(["pdftotext", "-l", "1", p, "-"],
                          capture_output=True, text=True, timeout=45).stdout


def doc_B(p, dpi=200):
    with tempfile.TemporaryDirectory() as t:
        subprocess.run(["pdftoppm", "-r", str(dpi), "-f", "1", "-l", "1", "-png", p,
                        os.path.join(t, "x")], capture_output=True, timeout=200)
        a = glob.glob(os.path.join(t, "*.png"))
        return subprocess.run(["tesseract", a[0], "stdout", "-l", "vie"],
                              capture_output=True, text=True, timeout=200).stdout if a else ""


def trich(t):
    g0 = gap_dau(t)
    k = g0.find("can c")
    dau = g0[:k] if k > 80 else g0
    m = DOAN_SO.search(dau)
    so = None
    if m:
        s = re.match(r"^\s*(\d{1,5})\b", m.group(1).strip())
        so = int(s.group(1)) if s else None
    nm = NGAY_CHU.search(dau) or NGAY_SO.search(dau)
    ngay = (int(nm.group(1)), int(nm.group(2)), int(nm.group(3))) if nm else None
    cq = "dhkt" if ("dhkt" in g0 or "kien truc" in g0) else None
    return so, ngay, cq


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=200)
    a = ap.parse_args()
    random.seed(SEED)
    with io.open(os.path.join(RES, "toan-kho.csv"), encoding="utf-8") as f:
        hang = [r for r in csv.DictReader(f)
                if r["phan_loai"] == "LOP CHU HONG" and KHUON.match(r["tep"])]
    # uu tien tep CO ngay day du, de T2 du mau
    co_ngay = [r for r in hang if KHUON.match(r["tep"]).group(5)]
    khong = [r for r in hang if not KHUON.match(r["tep"]).group(5)]
    random.shuffle(co_ngay); random.shuffle(khong)
    mau = (co_ngay[:a.n // 2] + khong[:a.n - len(co_ngay[:a.n // 2])])
    print("== E10: ba truong, n=%d (%d tep co ngay trong ten) ==" % (len(mau), len(co_ngay[:a.n // 2])))

    goc = {}
    for n_, ps in cac_pdf().items():
        for p in ps:
            goc.setdefault((n_, os.path.basename(p)), p)

    kq = {t: {"A": [], "B": []} for t in ("so hieu", "ngay", "co quan")}
    kiem_ngay = collections.Counter()
    xong = 0
    for r in mau:
        p = goc.get((r["nguon"], r["tep"]))
        if not p:
            continue
        m = KHUON.match(r["tep"])
        c_so = int(m.group(1))
        c_ngay = (int(m.group(5)), int(m.group(6)), int(m.group(3))) if m.group(5) else None
        try:
            ra, rb = trich(doc_A(p)), trich(doc_B(p))
        except Exception:
            continue
        xong += 1
        for ten, idx, chuan in (("so hieu", 0, c_so), ("ngay", 1, c_ngay),
                                ("co quan", 2, "dhkt")):
            if chuan is None:
                continue
            kq[ten]["A"].append(1 if ra[idx] == chuan else 0)
            kq[ten]["B"].append(1 if rb[idx] == chuan else 0)
        # tu kiem van ban chuan cho NGAY: khi OCR doc duoc mot ngay sach, nam co khop ten tep?
        if c_ngay and rb[1]:
            kiem_ngay["khop nam" if rb[1][2] == c_ngay[2] else "lech nam"] += 1
        if xong % 40 == 0:
            print("  ... %d" % xong, flush=True)

    print("\n== TU KIEM VAN BAN CHUAN CHO NGAY ==")
    tong_kn = sum(kiem_ngay.values())
    print("  OCR doc duoc ngay o %d ca: khop nam %d, lech nam %d" %
          (tong_kn, kiem_ngay["khop nam"], kiem_ngay["lech nam"]))
    kiem(tong_kn == 0 or kiem_ngay["khop nam"] >= kiem_ngay["lech nam"],
         "nam trong ten tep khop nam doc duoc nhieu hon la lech",
         "%d vs %d" % (kiem_ngay["khop nam"], kiem_ngay["lech nam"]))

    print("\n  %-10s %5s %14s %14s %10s %8s" %
          ("truong", "n", "A lop chu", "B OCR moi", "McNemar p", "Holm p"))
    ps, dong = [], []
    for ten in ("so hieu", "ngay", "co quan"):
        A, B = kq[ten]["A"], kq[ten]["B"]
        n = len(A)
        if n < 10:
            continue
        b = sum(1 for i in range(n) if A[i] and not B[i])
        c = sum(1 for i in range(n) if B[i] and not A[i])
        p, orat = mcnemar(b, c)
        ps.append(p)
        dong.append((ten, n, sum(A), sum(B), b, c, p, orat))
    hp = holm(ps)
    for (ten, n, sa, sb, b, c, p, orat), h in zip(dong, hp):
        la, ha = wilson(sa, n)
        lb, hb = wilson(sb, n)
        print("  %-10s %5d %5d (%4.1f%%) %5d (%4.1f%%) %10.2e %8.2e" %
              (ten, n, sa, 100.0 * sa / n, sb, 100.0 * sb / n, p, h))
        print("             %26s %14s  b=%d c=%d OR=%s" %
              ("[%.1f, %.1f]" % (100 * la, 100 * ha), "[%.1f, %.1f]" % (100 * lb, 100 * hb),
               b, c, ("%.1f" % orat) if orat != float("inf") else "inf"))
    kiem(len(dong) >= 2, "co it nhat 2 truong du mau", "%d truong" % len(dong))

    with io.open(os.path.join(RES, "tables", "tab-bontruong.tex"), "w", encoding="utf-8") as f:
        f.write("%% SINH TU DONG boi code/e10_bon_truong.py. KHONG sua tay.\n")
        f.write("\\begin{tabular}{lrrrr}\n\\toprule\nField & $n$ & Text layer & Modern OCR & "
                "Holm-adj. $p$ \\\\\n\\midrule\n")
        ten_en = {"so hieu": "Document number", "ngay": "Issue date",
                  "co quan": "Issuing body"}
        for (ten, n, sa, sb, b, c, p, orat), h in zip(dong, hp):
            f.write("%s & %d & %.1f\\%% & %.1f\\%% & %.1e \\\\\n" %
                    (ten_en[ten], n, 100.0 * sa / n, 100.0 * sb / n, h))
        f.write("\\bottomrule\n\\end{tabular}\n")

    print("\n=> %s (%d loi)" % ("DAT" if not loi else "CHUA DAT", len(loi)))
    for x in loi:
        print("   loi: " + x)
    return 0 if not loi else 1


if __name__ == "__main__":
    sys.exit(main())
