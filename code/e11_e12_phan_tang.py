#!/usr/bin/env python3
"""E11 phan tang theo LOAI van ban + E12 theo NAM.  python3 code/e11_e12_phan_tang.py

Hai cau hoi ve tinh khai quat BEN TRONG kho, doc tu `results/toan-kho.csv`, khong ton them gi.

E11: hien tuong co deu tren cac loai van ban khong (QD quyet dinh · TB thong bao · CV cong van
     · KH ke hoach · HD · BC · TH)? Neu chi tap trung o mot loai thi phai khai.
E12: hien tuong co theo thoi gian khong? Neu no giam dan theo nam thi day la mot van de DANG
     TU KHOI, va ket luan cua bai phai noi vay. Neu khong doi thi no la van de TON DONG.
     ⚠ 1644/3877 ten tep ghi nam '0000' tuc KHONG RO; nhung tep ay phai bi loai khoi E12 va
     phai KHAI so luong, khong duoc lang le bo.

Ra: figures/f5-theo-loai.pdf · figures/f6-theo-nam.pdf
    results/tables/tab-loai.tex · results/so-lieu-e1112.tex
TU KIEM: tong cac tang phai bang tong da phan loai; ti le toan cuc tinh lai tu cac tang phai
khop con so goc; va phai in DO PHU (bao nhieu tep khong vao duoc tang nao).
"""
import collections, csv, io, os, re, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import txstyle as TX   # bo style cua nha, xem paper-lab/transaction-figure-kit

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES, FIG = os.path.join(GOC, "results"), os.path.join(GOC, "figures")
TEN_LOAI = {"QD": "Decision", "TB": "Notice", "CV": "Dispatch", "KH": "Plan",
            "HD": "Guidance", "BC": "Report", "TH": "Circular", "UNK": "Unlabelled"}
loi = []


def kiem(dk, ten, ct=""):
    if not dk:
        loi.append(ten)
    print("  %s %s%s" % ("DAT " if dk else "HONG", ten, ("  [" + ct + "]") if ct else ""))


def main():
    with io.open(os.path.join(RES, "toan-kho.csv"), encoding="utf-8") as f:
        hang = [r for r in csv.DictReader(f)
                if r["phan_loai"] in ("LOP CHU HONG", "LOP CHU TOT")]
    tong = len(hang)
    hong_tong = sum(1 for r in hang if r["phan_loai"] == "LOP CHU HONG")
    print("== E11: PHAN TANG THEO LOAI VAN BAN ==")
    print("   nen: %d tep co lop chu, %d hong (%.1f%%)" %
          (tong, hong_tong, 100.0 * hong_tong / tong))

    theo_loai = collections.defaultdict(collections.Counter)
    khong_ro = 0
    for r in hang:
        lo = r["loai_ten_tep"]
        if not lo:
            khong_ro += 1
            continue
        theo_loai[lo][r["phan_loai"]] += 1
    phu = tong - khong_ro
    print("   DO PHU: %d/%d tep co nhan loai trong ten tep (%.1f%%), %d KHONG ro" %
          (phu, tong, 100.0 * phu / tong, khong_ro))
    kiem(phu > 0.5 * tong, "tren mot nua so tep co nhan loai", "%.1f%%" % (100.0 * phu / tong))

    xep = sorted(theo_loai.items(), key=lambda x: -sum(x[1].values()))
    print("\n   %-12s %7s %7s %9s" % ("loai", "hong", "tot", "ti le hong"))
    ten, tih, so = [], [], []
    # ⛔ Hinh nay tung ve THIEU mot hang so voi bang cung du lieu: no bo cac loai <20 tep trong
    # khi bang co hang gop. Chu thich lai viet "every type without exception". Nguoi doc ngoai
    # bat duoc. Nay hinh va bang ve tu CUNG mot danh sach.
    gop_h = sum(c["LOP CHU HONG"] for _, c in xep if sum(c.values()) < 20)
    gop_t = sum(c["LOP CHU TOT"] for _, c in xep if sum(c.values()) < 20)
    for lo, c in xep:
        h, t = c["LOP CHU HONG"], c["LOP CHU TOT"]
        if h + t < 20:
            continue
        print("   %-12s %7d %7d %8.1f%%" % (TEN_LOAI.get(lo, lo), h, t, 100.0 * h / (h + t)))
        ten.append(TEN_LOAI.get(lo, lo))
        tih.append(100.0 * h / (h + t))
        so.append(h + t)
    if gop_h + gop_t:
        ten.append("Other types"); tih.append(100.0 * gop_h / (gop_h + gop_t))
        so.append(gop_h + gop_t)
    kiem(len(ten) >= 3, "co it nhat 3 loai du mau de so", "%d loai" % len(ten))
    kiem(sum(so) == sum(c["LOP CHU HONG"] + c["LOP CHU TOT"] for _, c in xep),
         "hinh ve DU moi tep, khong bo hang nao", "%d" % sum(so))
    kiem(sum(sum(c.values()) for c in theo_loai.values()) + khong_ro == tong,
         "tong cac tang cong voi 'khong ro' bang tong")

    fig, ax = plt.subplots(figsize=(5.4, 2.6))
    y = np.arange(len(ten))
    ax.barh(y, tih, color=TX.ACCENT, height=0.6, edgecolor="white", linewidth=0.5)
    ax.set_yticks(y)
    ax.set_yticklabels(["%s (n=%d)" % (a, b) for a, b in zip(ten, so)], fontsize=8)
    ax.axvline(100.0 * hong_tong / tong, color=TX.NEUTRAL, ls="--", lw=0.9)
    ax.set_xlabel("share of documents with an unusable text layer (%)")
    ax.set_xlim(0, 108)
    TX.grid_mo(ax, "x")
    ax.invert_yaxis()
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "f5-theo-loai.pdf"))
    plt.close(fig)

    # ---------- E12 ----------
    print("\n== E12: PHAN TANG THEO NAM ==")
    nam = collections.defaultdict(collections.Counter)
    khong_nam = 0
    for r in hang:
        m = re.match(r"^(\d{3,4})_[A-Z]{2,4}_(\d{4})_", r["tep"], re.I)
        if not m or m.group(2) == "0000":
            khong_nam += 1
            continue
        y_ = int(m.group(2))
        if 1990 <= y_ <= 2026:
            nam[y_][r["phan_loai"]] += 1
        else:
            khong_nam += 1
    co_nam = tong - khong_nam
    print("   DO PHU: %d/%d tep co nam doc duoc (%.1f%%), %d khong ro (phan lon ghi '0000')"
          % (co_nam, tong, 100.0 * co_nam / tong, khong_nam))
    kiem(co_nam >= 200, "du mau de xet theo nam", "%d tep" % co_nam)

    ns = sorted(n for n in nam if sum(nam[n].values()) >= 15)
    print("\n   %-6s %7s %7s %9s" % ("nam", "hong", "tot", "ti le hong"))
    ti = []
    for n_ in ns:
        h, t = nam[n_]["LOP CHU HONG"], nam[n_]["LOP CHU TOT"]
        print("   %-6d %7d %7d %8.1f%%" % (n_, h, t, 100.0 * h / (h + t)))
        ti.append(100.0 * h / (h + t))
    if len(ns) >= 3:
        fig, ax = plt.subplots(figsize=(5.4, 2.6))
        ax.plot(ns, ti, "o-", color=TX.ACCENT, lw=1.1, ms=4)
        ax.axhline(100.0 * hong_tong / tong, color=TX.NEUTRAL, ls="--", lw=0.9)
        ax.set_xlabel("year of issue (from the filing system)")
        ax.set_ylabel("unusable text layer (%)")
        ax.set_ylim(-3, 103)
        fig.tight_layout()
        fig.savefig(os.path.join(FIG, "f6-theo-nam.pdf"))
        plt.close(fig)
        print("   da sinh F6")
    else:
        print("   ⚠ chi %d nam du mau, KHONG ve F6 (khong bia hinh tu 2 diem)" % len(ns))

    with io.open(os.path.join(RES, "tables", "tab-loai.tex"), "w", encoding="utf-8") as f:
        f.write("%% SINH TU DONG boi code/e11_e12_phan_tang.py. KHONG sua tay.\n")
        f.write("\\begin{tabular}{lrrr}\n\\toprule\nDocument type & Unusable & Usable & "
                "Share unusable \\\\\n\\midrule\n")
        # ⛔ Ban dau bang chi in loai co >=20 tep va LANG LE bo phan con lai, nen cong lai ra
        # 1393 trong khi dan so la 1422. Nguoi doc ngoai cong tay va bat duoc. Nay co hang gop
        # cho cac loai it mau, va mot hang TONG de bang tu chung minh no cong dung.
        gh = gt = 0
        for lo, c in xep:
            h, t = c["LOP CHU HONG"], c["LOP CHU TOT"]
            if h + t < 20:
                gh += h; gt += t
                continue
            f.write("%s & %d & %d & %.1f\\%% \\\\\n" %
                    (TEN_LOAI.get(lo, lo), h, t, 100.0 * h / (h + t)))
        if gh + gt:
            f.write("Other types (each $<$20 files) & %d & %d & %.1f\\%% \\\\\n" %
                    (gh, gt, 100.0 * gh / (gh + gt)))
        th = sum(c["LOP CHU HONG"] for _, c in xep)
        tt = sum(c["LOP CHU TOT"] for _, c in xep)
        f.write("\\midrule\nAll typed records & %d & %d & %.1f\\%% \\\\\n"
                % (th, tt, 100.0 * th / (th + tt)))
        f.write("\\bottomrule\n\\end{tabular}\n")

    with io.open(os.path.join(RES, "so-lieu-e1112.tex"), "w", encoding="utf-8") as f:
        f.write("%% SINH TU DONG. KHONG sua tay.\n")
        f.write("\\newcommand{\\loaiPhu}{%.1f}\n" % (100.0 * phu / tong))
        f.write("\\newcommand{\\loaiSo}{%d}\n" % len(ten))
        f.write("\\newcommand{\\loaiMin}{%.1f}\n" % min(tih))
        f.write("\\newcommand{\\loaiMax}{%.1f}\n" % max(tih))
        f.write("\\newcommand{\\namPhu}{%.1f}\n" % (100.0 * co_nam / tong))
        f.write("\\newcommand{\\namKhongRo}{%d}\n" % khong_nam)
        if ti:
            f.write("\\newcommand{\\namMin}{%.1f}\n" % min(ti))
            f.write("\\newcommand{\\namMax}{%.1f}\n" % max(ti))

    print("\n=> %s (%d loi)" % ("DAT" if not loi else "CHUA DAT", len(loi)))
    for x in loi:
        print("   loi: " + x)
    return 0 if not loi else 1


if __name__ == "__main__":
    sys.exit(main())
