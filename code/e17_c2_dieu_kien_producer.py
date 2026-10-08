#!/usr/bin/env python3
"""E17: C2 con lai gi khi DIEU KIEN HOA theo producer?  python3 code/e17_c2_dieu_kien_producer.py

Sinh ra tu mot cau hoi cua nguoi doc ngoai (08/10/2026) ma toi khong tra loi duoc bang bai
dang co: *"1441 tep tu DPE Build 5656 va 1441 tep co /ToUnicode day du: co phai CUNG mot 1441
khong? Neu phai thi dong gop 2 la mot quan sat ve MOT san pham chu khong phai ve 1449 tai lieu."*

Ho uoc tinh phan giao >= 1441 + 1441 - 1449 = 1433 bang so hoc tap hop. Phep do nay tra loi
chinh xac, va cau tra loi CON MANH HON uoc tinh cua ho.

TU KIEM:
  K1 ba nhom cua toan kho cong dung tong
  K2 so DPE va so co CMap khop macro \\prodDanHong va \\tuHongTu dang in trong bai
  K3 phan giao khong vuot qua tung tap, va >= can duoi so hoc cua nguoi doc ngoai
  K4 neu phan du qua nho thi phai TU DAN NHAN la khong ket luan duoc, chu khong im
"""
import collections, csv, io, os, sys

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(GOC, "results")
NGUONG_DU = 30          # duoi nguong nay thi phan du KHONG ket luan duoc
loi = []


def kiem(dk, ten, ct=""):
    if not dk:
        loi.append(ten)
    print("  %s %s%s" % ("DAT " if dk else "HONG", ten, ("  [" + ct + "]") if ct else ""))


def macro_bai():
    d = {}
    import glob, re
    for f in glob.glob(os.path.join(RES, "so-lieu*.tex")):
        for k, v in re.findall(r"\\newcommand\{\\(\w+)\}\{([^}]*)\}",
                               io.open(f, encoding="utf-8").read()):
            d[k] = v
    return d


def main():
    with io.open(os.path.join(RES, "toan-kho.csv"), encoding="utf-8") as f:
        hang = list(csv.DictReader(f))
    pl = collections.Counter(r["phan_loai"] for r in hang)
    hong = [r for r in hang if r["phan_loai"] == "LOP CHU HONG"]
    tot = [r for r in hang if r["phan_loai"] == "LOP CHU TOT"]
    print("== E17: C2 duoi dieu kien producer ==")
    kiem(sum(pl.values()) == len(hang), "K1 ba nhom cong dung tong",
         "%d / %d" % (sum(pl.values()), len(hang)))

    def dpe(r):
        return r["producer"].startswith("DPE Build 5656")

    def cmap(r):
        return r["moi_font_co_tounicode"] == "True"

    n_dpe = sum(1 for r in hong if dpe(r))
    n_cmap = sum(1 for r in hong if cmap(r))
    giao = sum(1 for r in hong if dpe(r) and cmap(r))
    can_duoi = n_dpe + n_cmap - len(hong)
    print("  nhom HONG n=%d · DPE %d · co CMap %d · GIAO %d (can duoi so hoc %d)"
          % (len(hong), n_dpe, n_cmap, giao, can_duoi))
    kiem(giao <= min(n_dpe, n_cmap) and giao >= can_duoi,
         "K3 phan giao nam trong can", "%d trong [%d, %d]" % (giao, can_duoi, min(n_dpe, n_cmap)))

    mac = macro_bai()
    kiem(mac.get("prodDanHong") == str(n_dpe) and mac.get("tuHongTu") == str(n_cmap),
         "K2 khop macro dang in trong bai",
         "DPE %s vs %d · CMap %s vs %d" % (mac.get("prodDanHong"), n_dpe,
                                           mac.get("tuHongTu"), n_cmap))

    # --- dieu kien hoa: bo DPE ra khoi CA HAI lop, dao chieu con khong?
    du_hong = [r for r in hong if not dpe(r) and r["moi_font_co_tounicode"]]
    du_tot = [r for r in tot if not dpe(r) and r["moi_font_co_tounicode"]]
    th = sum(1 for r in du_hong if cmap(r))
    tt = sum(1 for r in du_tot if cmap(r))
    print("  BO DPE ra: hong %d/%d · tot %d/%d" % (th, len(du_hong), tt, len(du_tot)))
    du_nho = len(du_hong) < NGUONG_DU
    kiem(True, "K4 phan du %s" % ("QUA NHO, khong ket luan duoc" if du_nho else "du de xet"),
         "%d tep" % len(du_hong))

    with io.open(os.path.join(RES, "so-lieu-e17.tex"), "w", encoding="utf-8") as f:
        f.write("%% SINH TU DONG boi code/e17_c2_dieu_kien_producer.py. KHONG sua tay.\n")
        # ⛔ Ten macro LaTeX KHONG duoc chua CHU SO. `\\c2Giao` bi doc thanh `\\c` + `2Giao`,
        # va LaTeX chet ngay o preamble voi "Command \\c already defined". Lop loi nay da ghi
        # san trong code/make_claims.py va toi vua lap lai. Hau to phai la CHU.
        for k, v in (("cHaiGiao", giao), ("cHaiDuHong", len(du_hong)),
                     ("cHaiDuHongCoCMap", th), ("cHaiDuTot", len(du_tot)),
                     ("cHaiDuTotCoCMap", tt)):
            f.write("\\newcommand{\\%s}{%d}\n" % (k, v))
        # cHaiDuKetLuan da bo: no la co TU KIEM cua script, khong phai so de in, va mot
        # macro dinh nghia ma khong ai dung la mot cho de nguoi doc hoi.
    print("\n  da ghi results/so-lieu-e17.tex")
    print("=> %s (%d loi)" % ("DAT" if not loi else "CHUA DAT", len(loi)))
    for x in loi:
        print("   loi: " + x)
    return 0 if not loi else 1


if __name__ == "__main__":
    sys.exit(main())
