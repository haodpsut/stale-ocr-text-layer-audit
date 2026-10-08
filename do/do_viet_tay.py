#!/usr/bin/env python3
"""So hieu van ban co VIET TAY khong?  python3 do/do_viet_tay.py [--n 40]

Phat hien khi kiem gia thuyet ten tep. Hai the gioi trong cung mot kho:

  0471: 'So: ..4-44../QD-DHKT ... ngay .(O. thang ..QA nam 2014'  <- so hieu VIET TAY len mau in
  0442: 'So: 442 /2015/QD-KTD ... ngay 17 thang 6 nam 2015'       <- in san, va KHOP ten tep

Neu ti le viet tay cao thi co mot ket luan doc lap voi moi tranh luan ve lop chu:
**ngay ca OCR hoan hao cung khong lay duoc so hieu**, vi no khong duoc in ra. Ma so hieu lai
la truong quan trong nhat cho viec noi trich dan phap ly.

Phan biet tren ban OCR HIEN DAI (khong dung lop chu cu, de khong lan nguyen nhan):
  - tim doan 'So:' ... '/QD' hoac '/TB' ...
  - IN SAN  : giua chung co 1-5 chu so lien tuc
  - VIET TAY: giua chung toan dau cham, gach, ngoac, chu cai le  (OCR doc chu viet tay ra rac)

DOI CHUNG: in ra ca hai loai vi du de nguoi doc tu kiem bo phan loai, va dem rieng o "khong ro".
"""
import argparse, collections, os, random, re, sys, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from do_lop_chu import phan_loai, cac_pdf, SEED     # noqa: E402
from do_truong import gap_dau, doc_B                # noqa: E402

# Doan tu 'so' toi ky hieu loai van ban. Lay toi 30 ky tu cho du cho dau cham.
DOAN = re.compile(r"\bso\s*[:.]?\s*(.{0,30}?)/\s*(qd|tb|cv|kh|hd|bc)\b")
CHI_SO = re.compile(r"^\s*(\d{1,5})\s*(/\s*\d{4}\s*)?$")


def loai_dong(g):
    m = DOAN.search(g)
    if not m:
        return "khong thay dong so hieu", None
    giua = m.group(1)
    if CHI_SO.match(giua):
        return "IN SAN", giua.strip()
    if re.search(r"\d", giua) and len(re.sub(r"[^\d]", "", giua)) >= 1 and \
            len(re.sub(r"[\s\d]", "", giua)) >= 2:
        return "VIET TAY", giua.strip()
    if not re.search(r"\d", giua):
        return "VIET TAY", giua.strip()
    return "khong ro", giua.strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=40)
    a = ap.parse_args()
    random.seed(SEED)
    tat = [p for v in cac_pdf().values() for p in v]
    random.shuffle(tat)

    mau = []
    for p in tat:
        if len(mau) >= a.n:
            break
        if phan_loai(p)[0] == "LOP CHU HONG":     # tep quet, la noi van de nam
            mau.append(p)

    d = collections.Counter()
    vd = collections.defaultdict(list)
    for p in mau:
        try:
            g = gap_dau(doc_B(p))
        except Exception:
            continue
        k, giua = loai_dong(g)
        d[k] += 1
        if len(vd[k]) < 4:
            vd[k].append((os.path.basename(p)[:30], giua))

    n = sum(d.values()) or 1
    print("== SO HIEU VAN BAN: IN SAN hay VIET TAY? (n=%d, doc bang OCR hien dai) ==" % n)
    for k, v in d.most_common():
        print("  %-26s %3d  (%.0f%%)" % (k, v, 100.0 * v / n))
    print("\n== VI DU DE TU KIEM BO PHAN LOAI ==")
    for k in ("IN SAN", "VIET TAY", "khong ro", "khong thay dong so hieu"):
        for ten, giua in vd.get(k, []):
            print("  %-24s %-30s giua 'So:' va '/QD' = %r" % (k, ten, giua))
    print("\n  Neu ti le VIET TAY cao: **khong may OCR nao lay duoc so hieu**, va ban ghi")
    print("  may doc duoc duy nhat nam O NGOAI tep (ten tep, so cong van, he thong luu tru).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
