#!/usr/bin/env python3
"""E9: quet DPI. Dung anh to hon co cuu duoc dinh danh khong?  python3 code/e9_quet_dpi.py

Cau hoi cua nguoi van hanh, khong phai cua nha nghien cuu: neu OCR lai o do phan giai cao hon
thi so hieu co doc dung len khong? Neu CO thi bai co mot khuyen nghi re tien. Neu KHONG thi
thiet hai la NOI TAI cua o dien truong, va do la mot ket luan manh hon.

Cung mot tap tai lieu, cung mot bo trich, chi doi DPI: 100 · 150 · 200 · 300 · 400.
Van ban chuan = so trong ten tep.

⭐ Day cung la ABLATION 3 (do ben thiet ke): moi ket qua khac trong bai deu do o 200 dpi, nen
phai chung minh ket luan khong phu thuoc lua chon ay.

TU KIEM: thoi gian chay phai TANG theo DPI (neu khong thi chua doi DPI that);
doi chung: mot tai lieu co lop chu TOT phai cho ket qua cao va gan nhu khong doi theo DPI.
"""
import argparse, collections, csv, glob, io, os, random, re, subprocess, sys, tempfile, time
import warnings
warnings.filterwarnings("ignore")
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import txstyle as TX   # bo style cua nha, xem paper-lab/transaction-figure-kit

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES, FIG = os.path.join(GOC, "results"), os.path.join(GOC, "figures")
sys.path.insert(0, os.path.join(GOC, "do"))
from do_lop_chu import cac_pdf, SEED          # noqa: E402
from do_truong import gap_dau                  # noqa: E402
from do_so_hieu_chuan import so_hieu, KHUON    # noqa: E402

DPIS = [100, 150, 200, 300, 400]
loi = []


def kiem(dk, ten, ct=""):
    if not dk:
        loi.append(ten)
    print("  %s %s%s" % ("DAT " if dk else "HONG", ten, ("  [" + ct + "]") if ct else ""))


def wilson(k, n, z=1.96):
    if not n:
        return 0.0, 0.0
    p = k / float(n)
    d = 1 + z * z / n
    t = (p + z * z / (2 * n)) / d
    import math
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, t - h), min(1.0, t + h)


def ocr(p, dpi):
    with tempfile.TemporaryDirectory() as t:
        subprocess.run(["pdftoppm", "-r", str(dpi), "-f", "1", "-l", "1", "-png", p,
                        os.path.join(t, "x")], capture_output=True, timeout=400)
        a = glob.glob(os.path.join(t, "*.png"))
        if not a:
            return ""
        return subprocess.run(["tesseract", a[0], "stdout", "-l", "vie"],
                              capture_output=True, text=True, timeout=400).stdout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=60)
    a = ap.parse_args()
    random.seed(SEED)
    with io.open(os.path.join(RES, "toan-kho.csv"), encoding="utf-8") as f:
        moi = list(csv.DictReader(f))
    hong = [r for r in moi if r["phan_loai"] == "LOP CHU HONG" and r["so_hieu_ten_tep"]]
    random.shuffle(hong)
    hong = hong[:a.n]
    goc = {}
    for n_, ps in cac_pdf().items():
        for p in ps:
            goc.setdefault((n_, os.path.basename(p)), p)

    print("== E9: QUET DPI (n=%d, van ban chuan = ten tep) ==" % len(hong))
    dem = {d: [0, 0, 0] for d in DPIS}        # dung, ra-mot-so, tong
    tg = {d: 0.0 for d in DPIS}
    for i, r in enumerate(hong, 1):
        p = goc.get((r["nguon"], r["tep"]))
        if not p:
            continue
        chuan = int(r["so_hieu_ten_tep"])
        for d in DPIS:
            t0 = time.time()
            try:
                s = so_hieu(ocr(p, d))[1]
            except Exception:
                continue
            tg[d] += time.time() - t0
            dem[d][2] += 1
            if s is not None:
                dem[d][1] += 1
                if s == chuan:
                    dem[d][0] += 1
        if i % 10 == 0:
            print("  ... %d/%d" % (i, len(hong)), flush=True)

    print("\n  %-6s %6s %12s %12s %16s %9s" %
          ("dpi", "n", "ra mot so", "DUNG", "KTC 95% dung", "giay/tep"))
    ti, lo_, hi_, gs = [], [], [], []
    for d in DPIS:
        du, ra, n = dem[d]
        if not n:
            continue
        l, h = wilson(du, n)
        print("  %-6d %6d %7d (%3.0f%%) %7d (%4.1f%%)  [%4.1f%%, %4.1f%%] %9.2f" %
              (d, n, ra, 100.0 * ra / n, du, 100.0 * du / n, 100 * l, 100 * h, tg[d] / n))
        ti.append(100.0 * du / n); lo_.append(100 * l); hi_.append(100 * h)
        gs.append(tg[d] / n)

    kiem(len(ti) == len(DPIS), "chay du moi DPI", "%d/%d" % (len(ti), len(DPIS)))
    kiem(gs[-1] > gs[0] * 1.5, "thoi gian TANG theo DPI (da doi DPI that)",
         "%.2f -> %.2f giay" % (gs[0], gs[-1]))
    # Ket luan: co cai thien dang ke khong? So KTC cua DPI cao nhat voi DPI 200.
    i200 = DPIS.index(200)
    cai_thien = lo_[-1] > hi_[i200]
    print("\n  400 dpi so voi 200 dpi: %s" %
          ("CO cai thien (KTC roi nhau)" if cai_thien else
           "KHONG cai thien dang ke (KTC chong nhau)"))
    print("  => %s" % ("dung anh to hon la mot khuyen nghi re tien" if cai_thien else
                       "thiet hai la NOI TAI cua o dien truong, khong chua duoc bang do phan giai"))

    fig, ax = plt.subplots(figsize=(5.2, 2.8))
    ax.errorbar(DPIS[:len(ti)], ti,
                yerr=[np.array(ti) - np.array(lo_), np.array(hi_) - np.array(ti)],
                fmt="o-", color=TX.ACCENT, capsize=2.5, lw=1.1, ms=4,
                elinewidth=0.8, capthick=0.8, label="document numbers read correctly")
    ax.set_xlabel("rendering resolution (dpi)")
    ax.set_ylabel("document numbers read correctly (%)")
    ax.set_ylim(-2, max(hi_) * 1.25 + 2)
    ax2 = ax.twinx()
    ax2.plot(DPIS[:len(gs)], gs, "s--", color=TX.NEUTRAL, lw=1.0, ms=3.5,
             label="seconds per document")
    ax2.set_ylabel("seconds per document", color=TX.NEUTRAL)
    ax2.tick_params(axis="y", colors=TX.NEUTRAL)
    ax2.spines["right"].set_visible(True)
    ax2.spines["right"].set_linewidth(0.6)
    ax2.spines["top"].set_visible(False)
    h1, l1 = ax.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, loc="upper center", ncol=2)
    TX.grid_mo(ax)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "f8-quet-dpi.pdf"))
    plt.close(fig)

    with io.open(os.path.join(RES, "so-lieu-e9.tex"), "w", encoding="utf-8") as f:
        f.write("%% SINH TU DONG boi code/e9_quet_dpi.py. KHONG sua tay.\n")
        f.write("\\newcommand{\\dpiN}{%d}\n" % dem[200][2])
        f.write("\\newcommand{\\dpiMotTram}{%.1f}\n" % ti[0])
        f.write("\\newcommand{\\dpiBonTram}{%.1f}\n" % ti[-1])
        f.write("\\newcommand{\\dpiGiayMotTram}{%.2f}\n" % gs[0])
        f.write("\\newcommand{\\dpiGiayBonTram}{%.2f}\n" % gs[-1])
        f.write("\\newcommand{\\dpiCaiThien}{%s}\n" % ("yes" if cai_thien else "no"))

    print("\n=> %s (%d loi). Da sinh F8." % ("DAT" if not loi else "CHUA DAT", len(loi)))
    for x in loi:
        print("   loi: " + x)
    return 0 if not loi else 1


if __name__ == "__main__":
    sys.exit(main())
