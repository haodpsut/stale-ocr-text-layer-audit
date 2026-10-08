#!/usr/bin/env python3
"""So hieu, n LON, co khoang tin cay:  python3 do/do_so_hieu_n_lon.py [--n 250]

Ban n=50 o `do_so_hieu_chuan.py` chi du de biet huong. Bang trong bai can khoang tin cay va
can TACH NGUYEN NHAN, vi "sai" gop chung thi khong noi len duoc dieu gi sua duoc.

Van ban chuan = so trong ten tep (da xac nhan bang mat tren anh: 'So: 540/2015/QD-DHKT' va
'So: 630/QD-DHKT' khop dung ten tep).

Ba ket cuc cho moi nguon doc:
  DUNG            : lay ra dung so hieu
  SAI TRONG NHU THAT: lay ra mot so khac  <- nguy hiem nhat, pipeline khong the tu biet
  KHONG RA SO     : khong lay duoc gi     <- vo hai hon, vi con bao duoc

Khoang tin cay Wilson 95%, phu hop cho ti le gan 0 va gan 1 hon khoang chuan thuong.
Chi dung trang 1 (so hieu luon o dau trang) de chay nhanh gap doi.
"""
import argparse, collections, csv, glob, io, math, os, random, re, subprocess, sys, tempfile
import warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from do_lop_chu import cac_pdf, SEED                 # noqa: E402
from do_truong import gap_dau                        # noqa: E402
from do_so_hieu_chuan import so_hieu, KHUON          # noqa: E402

CSV = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "results", "toan-kho.csv")


def wilson(k, n, z=1.96):
    if n == 0:
        return 0.0, 0.0
    p = k / float(n)
    d = 1 + z * z / n
    tam = (p + z * z / (2 * n)) / d
    nua = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, tam - nua), min(1.0, tam + nua)


def doc_A1(p):
    return subprocess.run(["pdftotext", "-l", "1", p, "-"],
                          capture_output=True, text=True, timeout=45).stdout


def doc_B1(p, dpi=200):
    with tempfile.TemporaryDirectory() as t:
        subprocess.run(["pdftoppm", "-r", str(dpi), "-f", "1", "-l", "1", "-png", p,
                        os.path.join(t, "x")], capture_output=True, timeout=180)
        a = glob.glob(os.path.join(t, "*.png"))
        if not a:
            return ""
        return subprocess.run(["tesseract", a[0], "stdout", "-l", "vie"],
                              capture_output=True, text=True, timeout=180).stdout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=250)
    a = ap.parse_args()
    random.seed(SEED)

    # Lay danh sach tu CSV toan kho: nhanh, va dung dung tap da phan loai.
    hang = []
    with io.open(CSV, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["phan_loai"] == "LOP CHU HONG" and r["so_hieu_ten_tep"]:
                hang.append(r)
    random.shuffle(hang)
    hang = hang[:a.n]
    print("== SO HIEU, n=%d, van ban chuan = ten tep ==" % len(hang))

    goc = {}
    for n, ps in cac_pdf().items():
        for p in ps:
            goc.setdefault((n, os.path.basename(p)), p)

    d = {"A": collections.Counter(), "B": collections.Counter()}
    vd = []
    xong = 0
    for r in hang:
        p = goc.get((r["nguon"], r["tep"]))
        if not p:
            continue
        chuan = int(r["so_hieu_ten_tep"])
        try:
            ra = so_hieu(doc_A1(p))[1]
            rb = so_hieu(doc_B1(p))[1]
        except Exception:
            continue
        xong += 1
        for ten, s in (("A", ra), ("B", rb)):
            if s is None:
                d[ten]["KHONG RA SO"] += 1
            elif s == chuan:
                d[ten]["DUNG"] += 1
            else:
                d[ten]["SAI TRONG NHU THAT"] += 1
                if ten == "B" and len(vd) < 10:
                    vd.append((r["tep"][:28], chuan, s))
        if xong % 50 == 0:
            print("  ... %d" % xong, flush=True)

    print("\n  %-22s %8s %8s %-18s" % ("nguon doc", "so ca", "ti le", "KTC 95%"))
    for ten, nhan in (("A", "A lop chu nhung san"), ("B", "B OCR hien dai")):
        print("  %s" % nhan)
        for k in ("DUNG", "SAI TRONG NHU THAT", "KHONG RA SO"):
            v = d[ten][k]
            lo, hi = wilson(v, xong)
            print("    %-20s %8d %7.1f%%  [%.1f%%, %.1f%%]" %
                  (k, v, 100.0 * v / xong, 100 * lo, 100 * hi))
        ra = d[ten]["DUNG"] + d[ten]["SAI TRONG NHU THAT"]
        if ra:
            lo, hi = wilson(d[ten]["DUNG"], ra)
            print("    ⭐ KHI DA RA MOT SO thi dung %.1f%% (%d/%d)  [%.1f%%, %.1f%%]" %
                  (100.0 * d[ten]["DUNG"] / ra, d[ten]["DUNG"], ra, 100 * lo, 100 * hi))

    print("\n== VI DU B SAI ==")
    for t, c, s in vd:
        print("  %-28s chuan=%-5d doc ra=%-5d" % (t, c, s))
    print("\n  n thuc te = %d" % xong)
    return 0


if __name__ == "__main__":
    sys.exit(main())
