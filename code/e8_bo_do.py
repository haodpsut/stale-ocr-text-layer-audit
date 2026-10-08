#!/usr/bin/env python3
"""E8, ABLATION 2: bo do NOI DUNG vs bon bo do CAU TRUC.  python3 code/e8_bo_do.py [--n 300]

Bien C2 tu mot QUAN SAT thanh mot PHUONG PHAP CO DANH GIA.

⭐ VAN DE NHAN CHUAN, va cach tranh vong tron:
Khong duoc lay nhan tu rho (chinh la thu dang danh gia), cung khong duoc lay tu cau truc
(chinh la thu dang so sanh). Nhan phai den tu ANH TRANG:

    lop chu la DUNG DUOC  <=>  no khop voi mot cach doc DOC LAP cua cung trang giay

Cach doc doc lap = OCR hien dai tren anh dung lai. Do khop bang Jaccard tren tap TU, tinh tren
chu THO (khong gap dau), vi mat dau chinh la kieu hong can phat hien.

Nam bo do duoc cham tren cung mot nhan:
  D1 rho            (NOI DUNG)  ti le ky tu co dau
  D2 /ToUnicode     (CAU TRUC)  moi font co bang anh xa day du
  D3 do phu anh     (CAU TRUC)  anh trang 1 phu bao nhieu phan trang
  D4 so font        (CAU TRUC)
  D5 so ky tu/trang (CAU TRUC)

Ra: figures/f3-roc.pdf · figures/f4-phanbo-khop.pdf · results/tables/tab-bodo.tex
TU KIEM: phan bo do khop cung phai luong cuc (neu khong thi nhan khong dang tin);
AUC cua D2 phai < 0,5 (dung nhu Menh de); doi chung: bo do NGAU NHIEN cho AUC ~ 0,5.
"""
import argparse, collections, csv, glob, io, os, random, subprocess, sys, tempfile
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
from do_lop_chu import cac_pdf, SEED     # noqa: E402
loi = []


def kiem(dk, ten, ct=""):
    if not dk:
        loi.append(ten)
    print("  %s %s%s" % ("DAT " if dk else "HONG", ten, ("  [" + ct + "]") if ct else ""))


def jaccard(a, b):
    A = set(w for w in a.split() if len(w) > 2)
    B = set(w for w in b.split() if len(w) > 2)
    if not A or not B:
        return 0.0
    return len(A & B) / float(len(A | B))


def doc_A(p):
    return subprocess.run(["pdftotext", "-l", "2", p, "-"],
                          capture_output=True, text=True, timeout=45).stdout


def doc_B(p, dpi=200):
    with tempfile.TemporaryDirectory() as t:
        subprocess.run(["pdftoppm", "-r", str(dpi), "-f", "1", "-l", "2", "-png", p,
                        os.path.join(t, "x")], capture_output=True, timeout=240)
        r = []
        for a in sorted(glob.glob(os.path.join(t, "*.png"))):
            r.append(subprocess.run(["tesseract", a, "stdout", "-l", "vie"],
                                    capture_output=True, text=True, timeout=240).stdout)
        return "\n".join(r)


def dac_trung_cau_truc(p):
    """(co_tounicode, do_phu_anh, so_font, so_ky_tu_moi_trang)."""
    import fitz
    try:
        d = fitz.open(p)
        tr = d[0]
    except Exception:
        return None
    dt = abs(tr.rect.width * tr.rect.height) or 1.0
    phu = 0.0
    try:
        from fitz import Rect
        for im in tr.get_image_info():
            b = im.get("bbox")
            if b:
                r = Rect(b)
                phu = max(phu, abs(r.width * r.height) / dt)
    except Exception:
        pass
    try:
        from pypdf import PdfReader
        pr = PdfReader(p)
        fo = (pr.pages[0].get("/Resources") or {}).get("/Font")
        n_font, co_tu = 0, 0
        if fo:
            fo = fo.get_object()
            ks = list(fo)
            n_font = len(ks)
            co_tu = 1 if (ks and all("/ToUnicode" in fo[k].get_object() for k in ks)) else 0
        sotr = max(1, len(pr.pages))
    except Exception:
        n_font, co_tu, sotr = 0, 0, 1
    return co_tu, phu, n_font, sotr


def auc(diem, nhan):
    """AUC = P(diem cua lop duong > diem cua lop am). Lop duong = DUNG DUOC."""
    d, y = np.asarray(diem, float), np.asarray(nhan, int)
    pos, neg = d[y == 1], d[y == 0]
    if not len(pos) or not len(neg):
        return float("nan")
    tot = 0.0
    for v in pos:
        tot += (v > neg).sum() + 0.5 * (v == neg).sum()
    return tot / (len(pos) * len(neg))


def roc(diem, nhan):
    d, y = np.asarray(diem, float), np.asarray(nhan, int)
    thu = np.unique(d)
    tpr, fpr = [], []
    for t in np.concatenate(([-np.inf], thu, [np.inf])):
        du = d >= t
        tpr.append((du & (y == 1)).sum() / max(1, (y == 1).sum()))
        fpr.append((du & (y == 0)).sum() / max(1, (y == 0).sum()))
    return np.array(fpr), np.array(tpr)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=300)
    a = ap.parse_args()
    random.seed(SEED)
    with io.open(os.path.join(RES, "toan-kho.csv"), encoding="utf-8") as f:
        hang = [r for r in csv.DictReader(f)
                if r["phan_loai"] in ("LOP CHU HONG", "LOP CHU TOT")]
    random.shuffle(hang)
    hang = hang[:a.n]
    goc = {}
    for n, ps in cac_pdf().items():
        for p in ps:
            goc.setdefault((n, os.path.basename(p)), p)

    print("== E8: nhan chuan tu ANH TRANG, roi cham 5 bo do (n=%d) ==" % len(hang))
    rows = []
    for i, r in enumerate(hang, 1):
        p = goc.get((r["nguon"], r["tep"]))
        if not p:
            continue
        try:
            ta, tb = doc_A(p), doc_B(p)
        except Exception:
            continue
        ct = dac_trung_cau_truc(p)
        if ct is None:
            continue
        rows.append({"khop": jaccard(ta, tb), "rho": float(r["ti_le_dau"] or 0),
                     "tu": ct[0], "phu": ct[1], "font": ct[2], "kt": len(ta) / ct[3]})
        if i % 50 == 0:
            print("  ... %d/%d" % (i, len(hang)), flush=True)

    k = np.array([x["khop"] for x in rows])
    print("\n  do khop lop chu voi OCR: trung vi %.3f, tu %.3f toi %.3f" %
          (np.median(k), k.min(), k.max()))
    # nguong nhan: diem giua khoang trong rong nhat cua phan bo do khop
    s = np.sort(k)
    hieu = np.diff(s)
    i0 = int(np.argmax(hieu))
    nguong = (s[i0] + s[i0 + 1]) / 2.0
    print("  khoang trong rong nhat cua do khop: [%.3f, %.3f] => nguong nhan %.3f"
          % (s[i0], s[i0 + 1], nguong))
    kiem(hieu.max() > 5 * np.median(hieu[hieu > 0]),
         "phan bo do khop CUNG luong cuc (nhan dang tin)",
         "trong %.3f vs trung vi buoc %.4f" % (hieu.max(), np.median(hieu[hieu > 0])))

    y = (k >= nguong).astype(int)          # 1 = DUNG DUOC
    print("  nhan: %d dung duoc / %d hong" % (y.sum(), len(y) - y.sum()))
    kiem(0 < y.sum() < len(y), "ca hai lop deu co mau")

    bo = [("D1 rho (content)", np.array([x["rho"] for x in rows])),
          ("D2 /ToUnicode (structure)", np.array([x["tu"] for x in rows], float)),
          ("D3 image coverage (structure)", -np.array([x["phu"] for x in rows])),
          ("D4 font count (structure)", np.array([x["font"] for x in rows], float)),
          ("D5 chars/page (structure)", np.array([x["kt"] for x in rows]))]
    rng = np.random.default_rng(SEED)
    bo.append(("D0 random (control)", rng.random(len(rows))))

    print("\n  %-32s %6s" % ("bo do", "AUC"))
    kq = []
    for ten, d in bo:
        v = auc(d, y)
        kq.append((ten, v, d))
        print("  %-32s %6.3f" % (ten, v))
    d2 = [v for t, v, _ in kq if t.startswith("D2")][0]
    d0 = [v for t, v, _ in kq if t.startswith("D0")][0]
    d1 = [v for t, v, _ in kq if t.startswith("D1")][0]
    kiem(d2 < 0.5, "D2 /ToUnicode co AUC < 0,5 dung nhu Menh de", "%.3f" % d2)
    kiem(abs(d0 - 0.5) < 0.12, "doi chung: bo do NGAU NHIEN cho AUC ~ 0,5", "%.3f" % d0)
    kiem(d1 > 0.95, "D1 noi dung tach duoc hai lop", "%.3f" % d1)

    # ---- F3 ROC ----
    fig, ax = plt.subplots(figsize=(4.0, 3.5))
    KIEU = [(TX.ACCENT, "o", "-"), (TX.C["blue"], "s", "--"), (TX.C["green"], "^", "-."),
            (TX.C["orange"], "D", ":"), (TX.C["sky"], "v", "-"), (TX.NEUTRAL, "x", "--")]
    for ten, v, d in kq:
        if ten.startswith("D0"):
            continue
        f_, t_ = roc(d, y)
        mau, mk, net = KIEU[len(ax.lines) % len(KIEU)]
        ax.plot(f_, t_, lw=1.1, color=mau, ls=net, marker=mk, ms=3.2,
                markevery=max(1, len(f_) // 7),
                label="%s  AUC=%.2f" % (ten.split(" (")[0], v))
    ax.plot([0, 1], [0, 1], color="black", alpha=0.35, ls=":", lw=0.8)
    ax.set_xlabel("false positive rate")
    ax.set_ylabel("true positive rate")
    ax.legend(fontsize=7, loc="lower right")
    ax.set_aspect("equal")
    TX.grid_mo(ax, "both")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "f3-roc.pdf"))
    plt.close(fig)

    # ---- F4 phan bo do khop ----
    fig, ax = plt.subplots(figsize=(5.4, 2.8))
    canh = np.linspace(min(k), max(k), 41)
    ax.hist([x for x in k if x < nguong], bins=canh, color=TX.ACCENT, edgecolor="none",
            label="labelled unusable")
    ax.hist([x for x in k if x >= nguong], bins=canh, color=TX.NEUTRAL, alpha=0.55,
            edgecolor="none", label="labelled usable")
    ax.axvline(nguong, color=TX.NEUTRAL, ls="--", lw=0.9)
    ax.legend(loc="upper right")
    TX.grid_mo(ax)
    ax.set_xlabel("word-level agreement between text layer and re-OCR of the same page")
    ax.set_ylabel("documents")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "f4-phanbo-khop.pdf"))
    plt.close(fig)

    with io.open(os.path.join(RES, "tables", "tab-bodo.tex"), "w", encoding="utf-8") as f:
        f.write("%% SINH TU DONG boi code/e8_bo_do.py. KHONG sua tay.\n")
        f.write("\\begin{tabular}{llr}\n\\toprule\nDetector & Signal & AUC \\\\\n\\midrule\n")
        for ten, v, _ in kq:
            n2 = ten.replace("_", "\\_")
            f.write("%s & %s & %.3f \\\\\n" %
                    (n2.split(" (")[0], n2.split("(")[-1].rstrip(")"), v))
        f.write("\\bottomrule\n\\end{tabular}\n")

    with io.open(os.path.join(RES, "so-lieu-e8.tex"), "w", encoding="utf-8") as f:
        f.write("%% SINH TU DONG boi code/e8_bo_do.py. KHONG sua tay.\n")
        # ⛔ Ten macro LaTeX KHONG duoc chua chu so: `\\aucD1` lam LaTeX chet o preamble voi
        # thong bao lac de "Missing \\begin{document}". Hau to phai la CHU.
        CHU = {"0": "zero", "1": "one", "2": "two", "3": "three", "4": "four", "5": "five"}
        for t, v, _ in kq:
            ma = "aucD" + CHU[t.split()[0][1]]
            f.write("\\newcommand{\\%s}{%.3f}\n" % (ma, v))
        f.write("\\newcommand{\\eEightN}{%d}\n" % len(rows))
        f.write("\\newcommand{\\eEightNguong}{%.3f}\n" % nguong)
        f.write("\\newcommand{\\eEightTot}{%d}\n" % int(y.sum()))
        f.write("\\newcommand{\\eEightHong}{%d}\n" % int(len(y) - y.sum()))

    print("\n=> %s (%d loi)" % ("DAT" if not loi else "CHUA DAT", len(loi)))
    for x in loi:
        print("   loi: " + x)
    return 0 if not loi else 1


if __name__ == "__main__":
    sys.exit(main())
