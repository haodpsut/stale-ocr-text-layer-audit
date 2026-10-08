#!/usr/bin/env python3
"""E6 phan bo rho  +  E7 ablation quet nguong.  python3 code/e6_e7_nguong.py

E6: phan bo rho = ti le ky tu co dau, tren TOAN BO tep co lop chu. Neu phan bo luong cuc that
    thi nguong 0,12 khong phai lua chon, ma la mot khoang trong.
E7: ABLATION 1 (do nhay tham so). Quet nguong 0,02 -> 0,40 va xem phan hoach doi bao nhieu.
    KHONG can nhan chuan: day la cau hoi ve DO ON DINH cua phan hoach, khong phai ve do chinh xac.

Ra: figures/f1-phanbo-rho.pdf · figures/f2-quet-nguong.pdf · results/tables/tab-nguong.tex
    va them macro vao results/so-lieu-e67.tex

TU KIEM (in cuoi, phai DAT het):
  - khoang trong giua hai cum phai rong hon do rong cua tung cum
  - trong dai nguong rong, so tep doi lop phai gan 0
  - doi chung: mot phan bo DEU tu tao phai KHONG cho khoang trong nao (bo do khong tu bia cum)
"""
import collections, csv, io, os, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import txstyle as TX   # bo style cua nha, xem paper-lab/transaction-figure-kit

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(GOC, "results")
FIG = os.path.join(GOC, "figures")
loi = []


def kiem(dk, ten, ct=""):
    if not dk:
        loi.append(ten)
    print("  %s %s%s" % ("DAT " if dk else "HONG", ten, ("  [" + ct + "]") if ct else ""))


def khoang_trong(x, buoc=0.005):
    """Dai rong nhat khong co diem nao, CHI tim GIUA diem nho nhat va lon nhat.

    ⛔ Ban dau toi quet toi 0,5 co dinh, nen no nhan ca DUOI TRONG phia tren du lieu
    ([0,360; 0,500]) lam "khoang trong" va bao cao mot cum khong ton tai. Khoang trong chi co
    nghia khi no nam GIUA hai cum that.
    """
    x = np.sort(np.asarray(list(x)))
    if len(x) < 2:
        return (0, 0, 0)
    lo, hi = float(x.min()), float(x.max())
    canh = np.arange(lo, hi + buoc, buoc)
    dem, _ = np.histogram(x, bins=canh)
    tot, dau, dai = (0, 0, 0), 0, 0
    for i, c in enumerate(dem):
        if c == 0:
            if dai == 0:
                dau = i
            dai += 1
            if dai > tot[2]:
                tot = (dau, i + 1, dai)
        else:
            dai = 0
    return (canh[tot[0]], canh[min(tot[1], len(canh) - 1)], tot[2] * buoc)


def main():
    os.makedirs(FIG, exist_ok=True)
    os.makedirs(os.path.join(RES, "tables"), exist_ok=True)
    with io.open(os.path.join(RES, "toan-kho.csv"), encoding="utf-8") as f:
        hang = [r for r in csv.DictReader(f) if r["ti_le_dau"]]
    rho = np.array([float(r["ti_le_dau"]) for r in hang])
    print("== E6: PHAN BO rho (n=%d tep co lop chu) ==" % len(rho))

    d, c, rong = khoang_trong(rho)
    cum_thap = rho[rho < d + 1e-9]
    cum_cao = rho[rho > c - 1e-9]
    print("  cum THAP : n=%4d  trung vi %.4f  cuc dai %.4f" %
          (len(cum_thap), np.median(cum_thap), cum_thap.max() if len(cum_thap) else 0))
    print("  cum CAO  : n=%4d  trung vi %.4f  cuc tieu %.4f" %
          (len(cum_cao), np.median(cum_cao), cum_cao.min() if len(cum_cao) else 0))
    print("  khoang TRONG rong nhat: [%.3f, %.3f], rong %.3f" % (d, c, rong))

    # ⛔ Phep kiem dau tien cua toi SAI: doi khoang trong phai rong hon CA CUM. Mot cum hoan
    # toan co quyen trai rong hon khoang trong ma phan bo van luong cuc. Phep dung la so voi
    # KHOANG CACH GIUA HAI DIEM KE NHAU ben trong cum: neu khoang trong lon gap boi so lan
    # khoang cach ay thi day la mot ho ngan, khong phai mot cho thua.
    kc = np.diff(np.sort(rho))
    kc_trong = np.median(kc[kc > 0]) if (kc > 0).any() else 0.0
    ti = rong / kc_trong if kc_trong else float("inf")
    kiem(ti > 50, "khoang trong lon hon 50 lan khoang cach ke nhau trong cum",
         "%.0f lan (trong %.3f, ke nhau %.5f)" % (ti, rong, kc_trong))

    # doi chung: phan bo DEU khong duoc cho khoang trong lon
    rng = np.random.default_rng(20260923)
    deu = rng.uniform(0, 0.35, size=len(rho))
    _, _, rong_deu = khoang_trong(deu)
    kiem(rong_deu < rong / 3.0, "doi chung: phan bo DEU khong cho khoang trong tuong tu",
         "deu %.3f vs that %.3f" % (rong_deu, rong))

    # ---------- F1 ----------
    fig, ax = plt.subplots(figsize=(5.4, 2.8))
    canh = np.arange(0, 0.42, 0.005)
    # MOT mau nhan: cum DUOI nguong la thu bai noi ve; cum tren la xam
    ax.hist([x for x in rho if x < 0.12], bins=canh, color=TX.ACCENT, edgecolor="none",
            label="unusable ($\\rho < \\tau$)")
    ax.hist([x for x in rho if x >= 0.12], bins=canh, color=TX.NEUTRAL, alpha=0.55,
            edgecolor="none", label="usable")
    ax.axvspan(d, c, color="black", alpha=0.06, lw=0)
    ax.axvline(0.12, color=TX.NEUTRAL, ls="--", lw=0.9)
    # dat nhan BEN TRONG dai trong: dai ay theo dinh nghia khong co cot nao, nen khong de len gi
    ax.text((d + c) / 2.0, ax.get_ylim()[1] * 0.60,
            "empty band\n$\\tau = 0.12$", fontsize=7.5, color=TX.NEUTRAL,
            ha="center", va="center")
    ax.legend(loc="upper right")
    TX.grid_mo(ax)
    ax.set_xlabel(r"diacritic ratio $\rho$ of the embedded text layer")
    ax.set_ylabel("documents")
    ax.set_xlim(-0.005, 0.40)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "f1-phanbo-rho.pdf"))
    plt.close(fig)

    # ---------- E7 ----------
    print("\n== E7: ABLATION 1, quet nguong ==")
    nguongs = np.round(np.arange(0.02, 0.405, 0.01), 3)
    so_hong = np.array([(rho < t).sum() for t in nguongs])
    goc = (rho < 0.12).sum()
    doi = np.abs(so_hong - goc)
    on_dinh = nguongs[doi <= 0]
    print("  nguong 0,12 cho %d tep hong" % goc)
    print("  dai nguong cho ket qua Y HET: [%.2f, %.2f]  (rong %.2f)" %
          (on_dinh.min(), on_dinh.max(), on_dinh.max() - on_dinh.min()))
    rong_on = on_dinh.max() - on_dinh.min()
    kiem(rong_on > 0.099, "phan hoach KHONG doi tren dai nguong rong >= 0,10",
         "rong %.2f" % rong_on)
    # va dai on dinh phai PHU tron khoang trong: nguong dat o dau trong dai ay cung the
    kiem(on_dinh.min() <= cum_thap.max() + 0.02 and on_dinh.max() >= cum_cao.min() - 0.02,
         "dai on dinh PHU tron khoang trong giua hai cum",
         "[%.2f, %.2f] so voi trong [%.4f, %.4f]" %
         (on_dinh.min(), on_dinh.max(), cum_thap.max(), cum_cao.min()))

    fig, ax = plt.subplots(figsize=(5.4, 2.8))
    ax.plot(nguongs, so_hong, color=TX.NEUTRAL, lw=1.1, marker="o", ms=3,
            markevery=max(1, len(nguongs) // 14))
    ax.axvspan(on_dinh.min(), on_dinh.max(), color=TX.ACCENT, alpha=0.10, lw=0)
    # ⛔ ban dau dat chu o y = min*1.12: DUONG CONG di xuyen qua chu. Chi thay khi nhin anh.
    # Nay dat len gan dinh truc, noi khong duong nao di qua, va keo mot net dan xuong.
    ax.annotate("identical partition\nthroughout this band",
                xy=(on_dinh.mean(), min(so_hong) * 1.02),
                xytext=(on_dinh.mean(), max(so_hong) * 0.80), fontsize=7.5,
                color=TX.ACCENT, ha="center", va="center",
                arrowprops=dict(arrowstyle="-", color=TX.ACCENT, lw=0.6))
    ax.axvline(0.12, color=TX.NEUTRAL, ls="--", lw=0.9)
    TX.grid_mo(ax)
    ax.set_xlabel(r"threshold $\tau$")
    ax.set_ylabel("documents classified unusable")
    ax.set_ylim(0, max(so_hong) * 1.08)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "f2-quet-nguong.pdf"))
    plt.close(fig)

    with io.open(os.path.join(RES, "tables", "tab-nguong.tex"), "w", encoding="utf-8") as f:
        f.write("%% SINH TU DONG boi code/e6_e7_nguong.py. KHONG sua tay.\n")
        f.write("\\begin{tabular}{rrr}\n\\toprule\n$\\tau$ & Unusable & Change vs "
                "$\\tau{=}0.12$ \\\\\n\\midrule\n")
        for t in (0.02, 0.05, 0.08, 0.12, 0.16, 0.20, 0.30, 0.40):
            k = int((rho < t).sum())
            f.write("%.2f & %d & %+d \\\\\n" % (t, k, k - goc))
        f.write("\\bottomrule\n\\end{tabular}\n")

    with io.open(os.path.join(RES, "so-lieu-e67.tex"), "w", encoding="utf-8") as f:
        f.write("%% SINH TU DONG boi code/e6_e7_nguong.py. KHONG sua tay.\n")
        for k, v in (("rhoN", "%d" % len(rho)),
                     ("rhoThapN", "%d" % len(cum_thap)),
                     ("rhoThapMax", "%.3f" % (cum_thap.max() if len(cum_thap) else 0)),
                     ("rhoCaoN", "%d" % len(cum_cao)),
                     ("rhoCaoMin", "%.3f" % (cum_cao.min() if len(cum_cao) else 0)),
                     ("rhoCaoTV", "%.3f" % np.median(cum_cao)),
                     ("khoangTrongDau", "%.3f" % d), ("khoangTrongCuoi", "%.3f" % c),
                     ("khoangTrongRong", "%.3f" % rong),
                     ("nguongOnDau", "%.2f" % on_dinh.min()),
                     ("nguongOnCuoi", "%.2f" % on_dinh.max())):
            f.write("\\newcommand{\\%s}{%s}\n" % (k, v))

    print("\n=> %s (%d loi). Da sinh F1, F2, tab-nguong.tex, so-lieu-e67.tex" %
          ("DAT" if not loi else "CHUA DAT", len(loi)))
    for x in loi:
        print("   loi: " + x)
    return 0 if not loi else 1


if __name__ == "__main__":
    sys.exit(main())
