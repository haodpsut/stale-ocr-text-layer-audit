#!/usr/bin/env python3
"""Ten tep co lam VAN BAN CHUAN cho so hieu duoc khong?  python3 do/do_ten_tep.py [--n 40]

Ten tep trong kho co dang 0471_QD_0000_DHKT.pdf, doan la <so hieu>_<loai>_<nam>_<co quan>.
Neu dung thi co san van ban chuan cho ~5000 van ban, khoi gan nhan tay.

Nhung co mot nghi ngo phai kiem truoc: trong mau da xem, dong so hieu cua lop chu la
'se. ..r.dl ..l QD-DHKT', tuc so hieu trong ban IN la DAU CHAM, duoc dien TAY sau khi in.
Neu vay thi khong may OCR nao doc duoc, va ten tep la ban ghi DUY NHAT.

Do ba viec:
  1. ten tep co phan tich duoc theo khuon khong
  2. so trong ten tep co xuat hien trong ban OCR hien dai khong (B)
  3. dong "So:" trong van ban co BO TRONG khong (dau cham, gach, khoang trang)
"""
import argparse, collections, glob, os, random, re, subprocess, sys, tempfile, unicodedata
import warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from do_lop_chu import phan_loai, cac_pdf, SEED     # noqa: E402
from do_truong import gap_dau, doc_A, doc_B          # noqa: E402

KHUON = re.compile(r"^(\d{3,4})_([A-Z]{2,4})_(\d{4})_([A-Z]+)", re.I)
# Dong so hieu bo trong: 'So:' roi toan dau cham/gach/khoang trang truoc dau '/'
BO_TRONG = re.compile(r"\bso[:\s]*[.\s\-_/]{3,}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=40)
    a = ap.parse_args()
    random.seed(SEED)
    tat = [p for v in cac_pdf().values() for p in v]
    random.shuffle(tat)

    hop = [p for p in tat if KHUON.match(os.path.basename(p))]
    print("== 1. TEN TEP CO THEO KHUON KHONG ==")
    print("  %d/%d tep toan kho khop khuon <so>_<loai>_<nam>_<coquan>  (%.1f%%)" %
          (len(hop), len(tat), 100.0 * len(hop) / len(tat)))
    loai = collections.Counter(KHUON.match(os.path.basename(p)).group(2).upper() for p in hop)
    print("  loai van ban trong ten tep:", dict(loai.most_common(8)))
    nam = collections.Counter(KHUON.match(os.path.basename(p)).group(3) for p in hop)
    print("  nam '0000' (khong ro):", nam.get("0000", 0), "/", len(hop))

    mau = [p for p in hop if phan_loai(p)[0] == "LOP CHU HONG"][:a.n]
    print("\n== 2+3. SO TRONG TEN TEP co xuat hien trong ban OCR moi khong (n=%d) ==" % len(mau))
    d = collections.Counter()
    vd = []
    for p in mau:
        m = KHUON.match(os.path.basename(p))
        so = str(int(m.group(1)))          # bo so 0 dung dau: 0471 -> 471
        co_quan = m.group(4).upper()
        try:
            tb, ta = doc_B(p), doc_A(p)
        except Exception:
            continue
        gb, ga = gap_dau(tb), gap_dau(ta)
        d["xet"] += 1
        # so hieu rieng cua van ban: <so>/<gi do co ten co quan>
        rieng = re.search(r"\b%s\s*/\s*[A-Za-z0-9\-]*%s" % (re.escape(so), co_quan.lower()), gb)
        bat_ky = re.search(r"\b%s\b" % re.escape(so), gb)
        if rieng:
            d["B tim thay dung dang <so>/<coquan>"] += 1
        elif bat_ky:
            d["B co so nhung khong dung dang"] += 1
        else:
            d["B KHONG co so cua ten tep"] += 1
        if BO_TRONG.search(gb) or BO_TRONG.search(ga):
            d["dong 'So:' BO TRONG trong ban in"] += 1
        if len(vd) < 5 and not rieng:
            k = gb.find("/%s" % co_quan.lower())
            vd.append((os.path.basename(p)[:30], so,
                       re.sub(r"\s+", " ", gb[max(0, k - 40):k + 14]) if k > 0 else "(khong thay)"))
    for k, v in d.most_common():
        print("  %-42s %3d  (%.0f%%)" % (k, v, 100.0 * v / max(1, d["xet"])))
    print("\n  vi du cho ca B khong tim thay dung dang:")
    for t, so, ctx in vd:
        print("   %-30s ten tep=%-5s  ngu canh trong OCR: ...%s..." % (t, so, ctx))
    return 0


if __name__ == "__main__":
    sys.exit(main())
