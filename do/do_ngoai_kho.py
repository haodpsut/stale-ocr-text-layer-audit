#!/usr/bin/env python3
"""Hien tuong co song NGOAI mot kho khong?  python3 do/do_ngoai_kho.py

Day la rui ro lon nhat cua bai, lon hon moi bai chua doc. Moi so do den nay lay tu mot kho ma
phan lon la van ban cua MOT truong. Neu `DPE Build 5656` chi la quy trinh quet cua rieng noi ay
thi bai la BAO CAO MOT CA, khong phai nghien cuu ti le mac, va tieu de phai viet khac.

Do ba viec, tach theo TUNG NGUON:
  1. ti le lop chu hong
  2. phan bo phan mem sinh PDF
  3. `DPE Build 5656` co mat o nguon nao

Phan quyet phai dua ra TRUOC khi viet mot dong nao cua bai.
"""
import collections, os, sys, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from do_lop_chu import phan_loai, cac_pdf, SEED     # noqa: E402
from do_producer import nguon                        # noqa: E402
import random


def main():
    random.seed(SEED)
    kho = cac_pdf()
    print("== SUC KHOE LOP CHU + PHAN MEM SINH PDF, TACH THEO NGUON ==\n")
    tong_dpe = collections.Counter()
    for ten, ps in kho.items():
        if not ps:
            continue
        mau = random.sample(ps, min(90, len(ps)))
        d = collections.Counter()
        pm = collections.defaultdict(collections.Counter)
        for p in mau:
            k, _ = phan_loai(p)
            d[k] += 1
            if k in ("LOP CHU HONG", "LOP CHU TOT"):
                pm[nguon(p)][k] += 1
        cc = d["LOP CHU HONG"] + d["LOP CHU TOT"]
        print("### %s  (n=%d / %d PDF)" % (ten, len(mau), len(ps)))
        print("   quet %d · lop chu hong %d · tot %d   =>  %s" %
              (d["QUET"], d["LOP CHU HONG"], d["LOP CHU TOT"],
               ("%.0f%% tep CO lop chu thi HONG" % (100.0 * d["LOP CHU HONG"] / cc))
               if cc else "khong tep nao co lop chu"))
        for t, c in sorted(pm.items(), key=lambda x: -sum(x[1].values()))[:5]:
            print("     %-46s hong %2d  tot %2d" % (t[:46], c["LOP CHU HONG"], c["LOP CHU TOT"]))
            if "DPE" in t:
                tong_dpe[ten] += c["LOP CHU HONG"] + c["LOP CHU TOT"]
        print()

    print("== PHAN QUYET NGOAI SUY ==")
    print("  'DPE Build 5656' xuat hien o:", dict(tong_dpe) or "CHI mot nguon")
    if len(tong_dpe) <= 1:
        print("  ⛔ Chi mot nguon => day la BAO CAO MOT CA (one archive), khong phai ti le mac.")
        print("     Bai phai khai dieu do trong tieu de va trong phan han che, hoac phai lay")
        print("     them kho cua co quan khac truoc khi viet.")
    else:
        print("  ✅ Nhieu nguon => co co so noi ve ti le mac, nhung van phai khai so nguon.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
