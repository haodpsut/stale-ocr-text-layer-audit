#!/usr/bin/env python3
"""E15: phan ra BA NHANH ket cuc cho tung truong, tung nhanh doc.
    python3 code/e15_ba_nhanh.py [--n 200]

E10 chi do MOT dai luong: ti le DUNG. Nhung ket cuc that co BA, khong hai, va hai cai sai
KHONG cung gia:

    DUNG      : tra ve mot gia tri, va no khop van ban chuan
    SAI IM LANG: tra ve mot gia tri, trong hop le, va KHAC van ban chuan   <- cai dat nhat
    IM        : khong tra ve gi (goi ben tren BIET la thieu)

Phan biet ay la dieu khien toan bo phan giai tich moi cua bai: `Rec + eps + abst = 1`, va
diem hoa von cua viec OCR lai phu thuoc ti so GIA giua eps va abst chu khong vao Rec.

⚠ GIOI HAN BIET TRUOC, phai in ra chu khong duoc giau: bo trich CO QUAN la mot phep thu
THUOC VE ("co chua 'dhkt'/'kien truc' khong"), nen no KHONG THE tra ve gia tri sai. eps cua
truong ay bang 0 VI CACH DO, khong phai vi truong ay an toan. Script tu dan nhan degenerate.

TU KIEM (script tu choi ghi ket qua neu mot phep hong):
  K1 ba nhanh cong lai dung n, cho moi truong va moi nhanh doc        (dong nhat so hoc)
  K2 so DUNG khop chinh xac E10 da chay doc lap truoc do              (so HAI NGUON)
  K3 bo XEP NHANH: dua vao chinh van ban chuan  -> phai xep DUNG
  K4 bo XEP NHANH: dua vao gia tri KHAC chuan   -> phai xep SAI IM, khong duoc xep IM
  K5 bo XEP NHANH: dua vao None                 -> phai xep IM, khong duoc xep SAI
  K6 truong nao eps = 0 phai duoc giai thich bang kieu bo trich, khong de trong

⛔ K3-K5 la doi chung THAT chu khong phai `x == x`. Ban dau toi viet `dc_duong += 1 if c_so ==
c_so else 0`, tuc so mot gia tri voi CHINH NO: luon dung, khong the hong, nen khong do gi ca.
Dung cai dang do la chinh bo XEP BA NHANH, vi no la DUNG CU MOI cua phep do nay, va dieu de
hong nhat o no la lan giua "tra ve sai" voi "khong tra ve gi".
"""
import argparse, csv, io, math, os, random, re, subprocess, sys, tempfile, glob
import warnings
warnings.filterwarnings("ignore")

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(GOC, "results")
sys.path.insert(0, os.path.join(GOC, "do"))
sys.path.insert(0, os.path.join(GOC, "code"))
from do_lop_chu import cac_pdf, SEED                        # noqa: E402
from e10_bon_truong import KHUON, trich, doc_A, doc_B, wilson   # noqa: E402

# Truong nao co bo trich chi THU THUOC VE (chi ra duoc dung gia tri hoac khong ra gi).
DEGENERATE = {"co quan": "membership test: the extractor can only return the expected value "
                         "or nothing, so a wrong value is unreachable by construction"}
TEN_EN = {"so hieu": "Document number", "ngay": "Issue date", "co quan": "Issuing body"}
THU_TU = ["co quan", "ngay", "so hieu"]
loi = []


def kiem(dk, ten, ct=""):
    if not dk:
        loi.append(ten)
    print("  %s %s%s" % ("DAT " if dk else "HONG", ten, ("  [" + ct + "]") if ct else ""))


DUNG, SAI, IM = 0, 1, 2


def xep(v, chuan):
    """Bo XEP BA NHANH. Day la dung cu moi cua E15, nen no la thu phai doi chung."""
    if v is None:
        return IM
    return DUNG if v == chuan else SAI


def khac(chuan):
    """Mot gia tri CUNG KIEU voi chuan nhung khac han, de thu nhanh SAI IM."""
    if isinstance(chuan, int):
        return chuan + 1
    if isinstance(chuan, tuple):
        return (chuan[0], chuan[1], chuan[2] + 1)
    return str(chuan) + "x"


def e10_dung_tu_log():
    """Doc so DUNG ma E10 da bao, de so HAI NGUON. Tra {truong: (n, dungA, dungB)}."""
    p = os.path.join(RES, "e10.log")
    if not os.path.exists(p):
        return {}
    t = io.open(p, encoding="utf-8").read()
    ra = {}
    for ten in THU_TU:
        m = re.search(r"^\s+%s\s+(\d+)\s+(\d+)\s*\(\s*[\d.]+%%\)\s+(\d+)\s*\(" % ten, t, re.M)
        if m:
            ra[ten] = (int(m.group(1)), int(m.group(2)), int(m.group(3)))
    return ra


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=200)
    a = ap.parse_args()
    random.seed(SEED)
    with io.open(os.path.join(RES, "toan-kho.csv"), encoding="utf-8") as f:
        hang = [r for r in csv.DictReader(f)
                if r["phan_loai"] == "LOP CHU HONG" and KHUON.match(r["tep"])]
    co_ngay = [r for r in hang if KHUON.match(r["tep"]).group(5)]
    khong = [r for r in hang if not KHUON.match(r["tep"]).group(5)]
    random.shuffle(co_ngay); random.shuffle(khong)
    mau = (co_ngay[:a.n // 2] + khong[:a.n - len(co_ngay[:a.n // 2])])
    print("== E15: ba nhanh ket cuc, n=%d ==" % len(mau))

    goc = {}
    for n_, ps in cac_pdf().items():
        for p in ps:
            goc.setdefault((n_, os.path.basename(p)), p)

    # kq[truong][nhanh] = [dung, sai, im]
    kq = {t: {"A": [0, 0, 0], "B": [0, 0, 0]} for t in THU_TU}
    dong = []          # (tep, truong, ket_cuc_A, ket_cuc_B) de bootstrap GHEP CAP
    dc = {"duong": 0, "khac": 0, "rong": 0, "n": 0}
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
            xa, xb = xep(ra[idx], chuan), xep(rb[idx], chuan)
            kq[ten]["A"][xa] += 1
            kq[ten]["B"][xb] += 1
            dong.append((r["tep"], ten, xa, xb))
            # K3-K5: thu chinh bo XEP NHANH tren ba dau vao da biet truoc ket cuc
            dc["n"] += 1
            dc["duong"] += 1 if xep(chuan, chuan) == DUNG else 0
            dc["khac"] += 1 if xep(khac(chuan), chuan) == SAI else 0
            dc["rong"] += 1 if xep(None, chuan) == IM else 0
        if xong % 25 == 0:
            print("  ... %d" % xong, flush=True)

    print("\n  %-16s %4s %6s %8s %8s %8s %8s" %
          ("truong/nhanh", "n", "dung", "sai im", "im", "Rec", "eps"))
    sl, bang = {}, []
    for ten in THU_TU:
        for nhanh in ("A", "B"):
            d, s, i = kq[ten][nhanh]
            n = d + s + i
            if n < 10:
                continue
            print("  %-16s %4d %6d %8d %8d %7.1f%% %7.1f%%" %
                  ("%s / %s" % (ten, nhanh), n, d, s, i,
                   100.0 * d / n, 100.0 * s / n))
            bang.append((ten, nhanh, n, d, s, i))
            sl[(ten, nhanh)] = (n, d, s, i)

    # ---- K1: dong nhat so hoc
    xau = [k for k, (n, d, s, i) in sl.items() if d + s + i != n]
    kiem(not xau, "K1 ba nhanh cong lai dung n o moi truong", ", ".join(map(str, xau)))

    # ---- K2: so HAI NGUON voi E10
    e10 = e10_dung_tu_log()
    kiem(bool(e10), "K2 doc duoc e10.log de so hai nguon")
    lech = []
    for ten, (n10, a10, b10) in e10.items():
        for nhanh, d10 in (("A", a10), ("B", b10)):
            if (ten, nhanh) in sl:
                n, d, s, i = sl[(ten, nhanh)]
                if (n, d) != (n10, d10):
                    lech.append("%s/%s: E15 %d/%d vs E10 %d/%d" % (ten, nhanh, d, n, d10, n10))
    kiem(not lech, "K2 so DUNG khop chinh xac E10 chay doc lap", "; ".join(lech))

    # ---- K3-K5: doi chung tren bo XEP BA NHANH
    kiem(dc["n"] > 0 and dc["duong"] == dc["n"], "K3 chuan -> DUNG",
         "%d/%d" % (dc["duong"], dc["n"]))
    kiem(dc["n"] > 0 and dc["khac"] == dc["n"], "K4 gia tri khac -> SAI IM (khong lan sang IM)",
         "%d/%d" % (dc["khac"], dc["n"]))
    kiem(dc["n"] > 0 and dc["rong"] == dc["n"], "K5 None -> IM (khong lan sang SAI IM)",
         "%d/%d" % (dc["rong"], dc["n"]))

    # ---- K6: eps = 0 phai co ly do
    thieu_lydo = [ten for ten in THU_TU
                  if all(sl.get((ten, x), (0, 0, 1, 0))[2] == 0 for x in ("A", "B"))
                  and ten not in DEGENERATE]
    kiem(not thieu_lydo, "K6 moi truong co eps=0 deu duoc giai thich",
         ", ".join(thieu_lydo))

    if loi:
        print("\n=> CHUA DAT, KHONG ghi ket qua (%d loi)" % len(loi))
        for x in loi:
            print("   loi: " + x)
        return 1

    # ⭐ Ghi TUNG DONG ket cuc. Nguoi doc ngoai doi khoang tin cay cho lambda*, ma lambda* la
    # ti so hai ti le GHEP CAP tren cung tai lieu, nen phai bootstrap theo TAI LIEU.
    import csv as _csv
    with io.open(os.path.join(RES, "ket-cuc.csv"), "w", encoding="utf-8", newline="") as _f:
        _w = _csv.writer(_f); _w.writerow(["tep", "truong", "A", "B"])
        _w.writerows(dong)
    print("  da ghi results/ket-cuc.csv (%d dong)" % len(dong))

    # ---- bang
    with io.open(os.path.join(RES, "tables", "tab-banhanh.tex"), "w", encoding="utf-8") as f:
        f.write("%% SINH TU DONG boi code/e15_ba_nhanh.py. KHONG sua tay.\n")
        f.write("\\begin{tabular}{llrrrrr}\n\\toprule\n"
                "Field & Reading & $n$ & Correct & Silent error & Abstain & "
                "$\\widehat{\\varepsilon}$ \\\\\n\\midrule\n")
        for ten, nhanh, n, d, s, i in bang:
            f.write("%s & %s & %d & %d & %d & %d & %.1f\\%% \\\\\n" %
                    (TEN_EN[ten], "text layer" if nhanh == "A" else "re-OCR",
                     n, d, s, i, 100.0 * s / n))
        f.write("\\bottomrule\n\\end{tabular}\n")

    # ---- macro
    def ten_mac(ten, nhanh, hau):
        return "bn" + {"so hieu": "So", "ngay": "Ngay", "co quan": "CoQuan"}[ten] + nhanh + hau

    with io.open(os.path.join(RES, "so-lieu-e15.tex"), "w", encoding="utf-8") as f:
        f.write("%% SINH TU DONG boi code/e15_ba_nhanh.py. KHONG sua tay.\n")
        for ten, nhanh, n, d, s, i in bang:
            for hau, v in (("N", n), ("Dung", d), ("Sai", s), ("Im", i)):
                f.write("\\newcommand{\\%s}{%d}\n" % (ten_mac(ten, nhanh, hau), v))
            for hau, v in (("Rec", 100.0 * d / n), ("Eps", 100.0 * s / n),
                           ("Abst", 100.0 * i / n)):
                f.write("\\newcommand{\\%s}{%.1f}\n" % (ten_mac(ten, nhanh, hau), v))
            # pi = do chinh xac KHI DA TRA RA MOT GIA TRI, va so cai da tra ra
            ra = d + s
            f.write("\\newcommand{\\%s}{%d}\n" % (ten_mac(ten, nhanh, "Ra"), ra))
            if ra:
                lo, hi = wilson(d, ra)
                for hau, v in (("Pi", 100.0 * d / ra), ("PiSai", 100.0 * s / ra),
                               ("PiLo", 100.0 * lo), ("PiHi", 100.0 * hi)):
                    f.write("\\newcommand{\\%s}{%.1f}\n" % (ten_mac(ten, nhanh, hau), v))
        # diem hoa von: OCR lai hon lop chu khi  c/g < (RecB-RecA) / (epsB-epsA)
        for ten in THU_TU:
            if (ten, "A") in sl and (ten, "B") in sl:
                nA, dA, sA, _ = sl[(ten, "A")]
                nB, dB, sB, _ = sl[(ten, "B")]
                dRec = dB / float(nB) - dA / float(nA)
                dEps = sB / float(nB) - sA / float(nA)
                hv = (dRec / dEps) if dEps > 0 else float("inf")
                f.write("\\newcommand{\\%s}{%s}\n" %
                        (ten_mac(ten, "", "HoaVon"),
                         ("%.3f" % hv) if hv != float("inf") else "\\infty"))
                # dRec va dEps tinh bang DIEM PHAN TRAM, de van xuoi khong go tay con nao
                f.write("\\newcommand{\\%s}{%.1f}\n" % (ten_mac(ten, "", "DRec"), 100 * dRec))
                f.write("\\newcommand{\\%s}{%.1f}\n" % (ten_mac(ten, "", "DEps"), 100 * abs(dEps)))
                f.write("\\newcommand{\\%s}{%s}\n" % (ten_mac(ten, "", "Trum"),
                                                     "yes" if dEps <= 0 else "no"))
    print("\n  da ghi results/tables/tab-banhanh.tex va results/so-lieu-e15.tex")
    print("=> DAT")
    return 0


if __name__ == "__main__":
    sys.exit(main())
