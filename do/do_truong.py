#!/usr/bin/env python3
"""Thiet hai xuoi dong tren TRUONG HANH CHINH:  python3 do/do_truong.py [--n 30]

Cung MOT anh trang, hai cach doc:
  A = lop chu NHUNG SAN trong tep (thu moi pipeline dung khi thay "da co lop chu")
  B = OCR HIEN DAI (tesseract vie) tren anh dung lai tu chinh trang ay
Roi chay CUNG bo trich tren ca hai, dem bon truong: so hieu, ngay ban hanh, can cu, loai van ban.

⭐ CONG BANG VOI A: lop chu cu mat dau, nen moi mau deu chay tren ban DA GAP DAU ca hai phia.
Neu chi so ban co dau thi A thua ngay tu vach xuat phat va con so khong noi len dieu gi.
(Bai hoc IoT-J: baseline bi thiet thoi o hai cho doc lap, sua mot cho da xoa khoang cach.)

DOI CHUNG DUONG: chay y het tren nhom LOP CHU TOT. O do A phai TOT, neu khong thi bo trich
cua toi hong chu khong phai lop chu cu hong.
"""
import argparse, collections, glob, os, random, re, subprocess, sys, tempfile, unicodedata
import warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from do_lop_chu import phan_loai, cac_pdf, SEED     # noqa: E402


def gap_dau(s):
    """Bo moi dau thanh va dau mu, ha chu thuong. 'Quyết định' -> 'quyet dinh'."""
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.replace("Đ", "D").replace("đ", "d").lower()


# Bon bo trich, viet tren ban DA GAP DAU nen cong bang voi ca hai nguon.
SO_HIEU = re.compile(r"\bso[:\s.]*(\d{1,5})\s*/\s*([A-Za-z0-9\-]{2,20})")
NGAY_CHU = re.compile(r"\bngay\s+(\d{1,2})\s+thang\s+(\d{1,2})\s+nam\s+(\d{4})")
NGAY_SO = re.compile(r"\bngay\s+(\d{1,2})\s*/\s*(\d{1,2})\s*/\s*(\d{4})")
CAN_CU = re.compile(r"\bcan\s*c[uw]\b")
LOAI = re.compile(r"\b(quyet\s*dinh|thong\s*bao|cong\s*van|ke\s*hoach|to\s*trinh|bao\s*cao)\b")


def trich(t):
    g = gap_dau(t)
    sh = SO_HIEU.search(g)
    nc = NGAY_CHU.search(g) or NGAY_SO.search(g)
    return {
        "so hieu": ("%s/%s" % (sh.group(1), sh.group(2))) if sh else None,
        "ngay": ("%s-%s-%s" % (nc.group(3), nc.group(2), nc.group(1))) if nc else None,
        "can cu": len(CAN_CU.findall(g)) or None,
        "loai vb": re.sub(r"\s+", " ", LOAI.search(g).group(1)) if LOAI.search(g) else None,
    }


def doc_A(p):
    return subprocess.run(["pdftotext", "-l", "2", p, "-"],
                          capture_output=True, text=True, timeout=40).stdout


def doc_B(p, dpi=200):
    with tempfile.TemporaryDirectory() as t:
        subprocess.run(["pdftoppm", "-r", str(dpi), "-f", "1", "-l", "2", "-png", p,
                        os.path.join(t, "x")], capture_output=True, timeout=180)
        ra = []
        for a in sorted(glob.glob(os.path.join(t, "*.png"))):
            ra.append(subprocess.run(["tesseract", a, "stdout", "-l", "vie"],
                                     capture_output=True, text=True, timeout=180).stdout)
        return "\n".join(ra)


def chay(tap, ten):
    truong = ["so hieu", "ngay", "can cu", "loai vb"]
    co = {"A": collections.Counter(), "B": collections.Counter()}
    khop = collections.Counter()
    vi_du = []
    for p in tap:
        try:
            ta, tb = doc_A(p), doc_B(p)
        except Exception:
            continue
        ra, rb = trich(ta), trich(tb)
        for k in truong:
            if ra[k] is not None:
                co["A"][k] += 1
            if rb[k] is not None:
                co["B"][k] += 1
            if ra[k] is not None and rb[k] is not None and str(ra[k]) == str(rb[k]):
                khop[k] += 1
        if len(vi_du) < 4 and (ra["so hieu"] != rb["so hieu"] or ra["ngay"] != rb["ngay"]):
            vi_du.append((os.path.basename(p)[:34], ra, rb))
    n = len(tap)
    print("\n== %s (n=%d) ==" % (ten, n))
    print("  %-10s %14s %14s %14s" % ("truong", "A lop chu", "B OCR moi", "hai ben khop"))
    for k in truong:
        print("  %-10s %9d (%3.0f%%) %9d (%3.0f%%) %9d (%3.0f%%)" %
              (k, co["A"][k], 100.0 * co["A"][k] / n, co["B"][k], 100.0 * co["B"][k] / n,
               khop[k], 100.0 * khop[k] / n))
    for ten_t, ra, rb in vi_du:
        print("  vi du %-34s A=%-16s B=%-16s | A.ngay=%-12s B.ngay=%s" %
              (ten_t, ra["so hieu"], rb["so hieu"], ra["ngay"], rb["ngay"]))
    return co


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=30)
    a = ap.parse_args()
    random.seed(SEED)
    tat = [p for v in cac_pdf().values() for p in v]
    random.shuffle(tat)
    nhom = {"LOP CHU HONG": [], "LOP CHU TOT": []}
    for p in tat:
        if all(len(v) >= a.n for v in nhom.values()):
            break
        k, _ = phan_loai(p)
        if k in nhom and len(nhom[k]) < a.n:
            nhom[k].append(p)

    print("== THIET HAI XUOI DONG TREN TRUONG HANH CHINH ==")
    print("   moi phep so deu chay tren ban DA GAP DAU (cong bang voi lop chu cu)")
    chay(nhom["LOP CHU TOT"], "DOI CHUNG DUONG: lop chu TOT (A phai tot)")
    chay(nhom["LOP CHU HONG"], "CHINH: lop chu cu NHUNG SAN (A la thu pipeline dang dung)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
