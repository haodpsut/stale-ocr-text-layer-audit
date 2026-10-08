#!/usr/bin/env python3
"""Nguon goc: phan mem nao sinh ra tep co lop chu HONG?  python3 do/do_producer.py [--mau 300]

Tim ra khi soi cau truc PDF: nhom hong KHONG thieu bang /ToUnicode. Bang co du, dung cu phap,
nhung ANH XA SAI: glyph ve chu Viet lai khai la chu Latin (/Differences ghi /A /B /asciitilde...,
ToUnicode tra ve U+0021, U+0026...). Nghia la bo boc chu khong he hong, chung tuan thu dung mot
bang KHAI SAI. Khong co cau truc di dang nao de phat hien => hong IM LANG.

Neu lop hong tap trung o VAI phan mem sinh PDF thi do la mot su that co the kiem chung, va no
bien bai tu "co mot van de" thanh "co mot van de, day la nguon goc, day la dau hieu nhan biet".
"""
import argparse, collections, os, random, sys, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from do_lop_chu import phan_loai, cac_pdf, SEED     # noqa: E402


def nguon(p):
    from pypdf import PdfReader
    try:
        m = PdfReader(p).metadata
    except Exception:
        return "(khong doc duoc)"
    if not m:
        return "(khong co metadata)"
    pr = m.get("/Producer") or m.get("/Creator") or "(trong)"
    return str(pr).strip()[:46] or "(trong)"


def co_tounicode(p):
    """True neu MOI font cua trang 1 deu co /ToUnicode."""
    from pypdf import PdfReader
    try:
        pg = PdfReader(p).pages[0]
        fo = (pg.get("/Resources") or {}).get("/Font")
        if not fo:
            return None
        fo = fo.get_object()
        c = [("/ToUnicode" in fo[k].get_object()) for k in fo]
        return all(c) if c else None
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mau", type=int, default=300)
    a = ap.parse_args()
    random.seed(SEED)
    tat = [p for v in cac_pdf().values() for p in v]
    mau = random.sample(tat, min(a.mau, len(tat)))

    bang = collections.defaultdict(collections.Counter)
    tu = collections.Counter()
    for p in mau:
        k, _ = phan_loai(p)
        if k not in ("LOP CHU HONG", "LOP CHU TOT"):
            continue
        bang[nguon(p)][k] += 1
        c = co_tounicode(p)
        if c is not None:
            tu[(k, c)] += 1

    print("== PHAN MEM SINH PDF vs SUC KHOE LOP CHU (n=%d) ==" % len(mau))
    print("  %-46s %6s %6s %s" % ("producer", "hong", "tot", "ti le hong"))
    hang = sorted(bang.items(), key=lambda x: -(x[1]["LOP CHU HONG"] + x[1]["LOP CHU TOT"]))
    th, tt = 0, 0
    for ten, c in hang:
        h, t = c["LOP CHU HONG"], c["LOP CHU TOT"]
        th += h
        tt += t
        print("  %-46s %6d %6d   %s" %
              (ten, h, t, ("%.0f%%" % (100.0 * h / (h + t))) if (h + t) else "-"))
    print("  %-46s %6d %6d   %.0f%%" % ("TONG", th, tt, 100.0 * th / (th + tt) if th + tt else 0))

    print("\n== CO BANG /ToUnicode KHONG? ==")
    print("  (neu nhom HONG van co du bang thi khong co dau hieu cau truc nao de bao dong)")
    for k in ("LOP CHU HONG", "LOP CHU TOT"):
        co, khong = tu[(k, True)], tu[(k, False)]
        tong = co + khong
        print("  %-14s co du bang: %3d/%-3d (%s)" %
              (k, co, tong, ("%.0f%%" % (100.0 * co / tong)) if tong else "-"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
