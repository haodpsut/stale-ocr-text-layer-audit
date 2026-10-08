#!/usr/bin/env python3
"""PHEP GIET cho ung vien U5: thu vien boc chu PHO THONG co tu xu ma cu khong?

  python3 do/do_thu_vien.py [--n 20]

Tuyen bo cua U5 la: he thong thay PDF "co lop chu" thi bo qua OCR, va tren kho van ban hanh
chinh VN quyet dinh ay sai IM LANG. Tuyen bo ay SUP neu thu vien pho thong tu phat hien va
tu chuyen ma TCVN3/VNI sang Unicode. Tep nay hoi thang cau do.

Nam bo boc: pdftotext (poppler) · PyMuPDF · pdfplumber · pypdf · pdfminer.six.

DOI CHUNG DUONG (bat buoc): chay dung nam bo boc ay tren nhom LOP CHU TOT. Chung phai cho ti
le ky tu co dau CAO. Neu khong thi bo do hong, va moi ket luan tren nhom hong deu vo nghia.
Ma thoat: 0 doi chung dat, 1 doi chung that bai.
"""
import argparse, io, os, random, sys, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from do_lop_chu import ti_le_co_dau, phan_loai, cac_pdf, SEED       # noqa: E402

TRANG = 3


def b_pdftotext(p):
    import subprocess
    return subprocess.run(["pdftotext", "-l", str(TRANG), p, "-"],
                          capture_output=True, text=True, timeout=40).stdout


def b_pymupdf(p):
    import fitz
    d = fitz.open(p)
    return "\n".join(d[i].get_text() for i in range(min(TRANG, d.page_count)))


def b_pdfplumber(p):
    import pdfplumber
    with pdfplumber.open(p) as d:
        return "\n".join((pg.extract_text() or "") for pg in d.pages[:TRANG])


def b_pypdf(p):
    from pypdf import PdfReader
    r = PdfReader(p)
    return "\n".join(pg.extract_text() or "" for pg in r.pages[:TRANG])


def b_pdfminer(p):
    from pdfminer.high_level import extract_text
    return extract_text(p, maxpages=TRANG)


BO = [("pdftotext", b_pdftotext), ("PyMuPDF", b_pymupdf), ("pdfplumber", b_pdfplumber),
      ("pypdf", b_pypdf), ("pdfminer.six", b_pdfminer)]


def chay(tap, ten_tap):
    print("\n== %s (n=%d) ==" % (ten_tap, len(tap)))
    print("  %-14s %8s %8s %8s   %s" % ("bo boc", "tb dau", "trung vi", "tot/n", "ghi chu"))
    ket = {}
    for ten, ham in BO:
        tl, loi = [], 0
        for p in tap:
            try:
                t = ham(p)
            except Exception:
                loi += 1
                continue
            r = ti_le_co_dau(t or "")
            if r is not None:
                tl.append(r)
        if not tl:
            print("  %-14s %8s %8s %8s   %d loi" % (ten, "-", "-", "-", loi))
            ket[ten] = None
            continue
        tl.sort()
        tot = sum(1 for x in tl if x > 0.12)
        print("  %-14s %8.3f %8.3f %5d/%-3d   %s" %
              (ten, sum(tl) / len(tl), tl[len(tl) // 2], tot, len(tl),
               ("%d loi mo" % loi) if loi else ""))
        ket[ten] = sum(tl) / len(tl)
    return ket


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=20)
    a = ap.parse_args()
    random.seed(SEED)

    kho = cac_pdf()
    tat = [p for v in kho.values() for p in v]
    random.shuffle(tat)
    hong, tot = [], []
    for p in tat:
        if len(hong) >= a.n and len(tot) >= a.n:
            break
        k, _ = phan_loai(p)
        if k == "LOP CHU HONG" and len(hong) < a.n:
            hong.append(p)
        elif k == "LOP CHU TOT" and len(tot) < a.n:
            tot.append(p)

    print("== PHEP GIET U5: bo boc pho thong co tu chuyen ma cu khong? ==")
    print("   seed=%d, %d trang dau moi tep" % (SEED, TRANG))
    k_tot = chay(tot, "DOI CHUNG DUONG: nhom LOP CHU TOT (phai ra ti le dau CAO)")
    k_hong = chay(hong, "NHOM LOP CHU HONG (neu co bo nao ra ti le CAO thi U5 chet)")

    print("\n== PHAN QUYET ==")
    dat = all(v is not None and v > 0.15 for v in k_tot.values())
    print("  doi chung duong: %s" % ("DAT, tin duoc so duoi" if dat
                                     else "HONG, KHONG ket luan duoc"))
    if not dat:
        return 1
    cuu = [t for t, v in k_hong.items() if v is not None and v > 0.12]
    if cuu:
        print("  %s cuu duoc ma cu  =>  U5 BI GIET" % ", ".join(cuu))
    else:
        print("  KHONG bo boc nao cuu duoc ma cu  =>  U5 CON SONG")
        print("  ca 5 bo deu tra ve rac ma KHONG bao loi: dung la 'sai im lang'")
    return 0


if __name__ == "__main__":
    sys.exit(main())
