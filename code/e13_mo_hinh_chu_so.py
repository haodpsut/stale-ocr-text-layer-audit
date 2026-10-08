#!/usr/bin/env python3
"""E13: mo hinh dang dong cho sai so DINH DANH.  python3 code/e13_mo_hinh_chu_so.py [--n 400]

Yeu to hinh thuc cua bai, va no giai thich E10 chu khong chi mo ta.

E10 cho thay thiet hai tap trung o truong NGAN DANG SO. Mo hinh don gian nhat giai thich dieu
do: neu moi chu so bi doc sai doc lap voi xac suat p, thi mot dinh danh k chu so dung voi
xac suat

        P(dung | k) = (1 - p)^k                                        (1)

trong khi mot truong tu vung dai duoc bao ve boi du thua (chi can doan dung TU, khong can dung
tung ky tu), nen khong tuan theo (1).

Cach do:
  - p uoc tu cac cap chu so DOI MOT: can le phai trai giua so chuan (ten tep) va so OCR doc ra,
    chi lay cac ca CUNG DO DAI, de khong lan loi chen/xoa vao loi thay the.
  - roi DU BAO P(dung | k) cho k = 1..4 va doi chieu voi ti le do duoc.

⭐ Day la phep thu co the BAC BO mo hinh: neu do khong khop du bao thi ket luan la "sai so chu
so KHONG doc lap" va phai noi vay trong bai, chu khong bo phep do di.

TU KIEM: p phai nam trong (0,1); du bao phai giam theo k; va doi chung: mot bo sinh so NGAU
NHIEN dung mo hinh phai cho sai lech nho, de biet phep so khop co y nghia.
"""
import argparse, collections, csv, glob, io, math, os, random, re, subprocess, sys, tempfile
import warnings
warnings.filterwarnings("ignore")
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES, FIG = os.path.join(GOC, "results"), os.path.join(GOC, "figures")
sys.path.insert(0, os.path.join(GOC, "do"))
from do_lop_chu import cac_pdf, SEED          # noqa: E402
from do_truong import gap_dau                  # noqa: E402

KHUON = re.compile(r"^(\d{3,4})_([A-Z]{2,4})_(\d{4})_([A-Z]+)", re.I)
DOAN = re.compile(r"\bso\s*[:.]?\s*(.{0,30}?)/\s*(qd|tb|cv|kh|hd|bc|th)\b")
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
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, t - h), min(1.0, t + h)


def doc_B(p, dpi=200):
    with tempfile.TemporaryDirectory() as t:
        subprocess.run(["pdftoppm", "-r", str(dpi), "-f", "1", "-l", "1", "-png", p,
                        os.path.join(t, "x")], capture_output=True, timeout=200)
        a = glob.glob(os.path.join(t, "*.png"))
        return subprocess.run(["tesseract", a[0], "stdout", "-l", "vie"],
                              capture_output=True, text=True, timeout=200).stdout if a else ""


def so_doc_ra(t):
    g = gap_dau(t)
    k = g.find("can c")
    m = DOAN.search(g[:k] if k > 80 else g)
    if not m:
        return None
    s = re.match(r"^\s*(\d{1,5})\b", m.group(1).strip())
    return s.group(1) if s else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=400)
    a = ap.parse_args()
    random.seed(SEED)
    with io.open(os.path.join(RES, "toan-kho.csv"), encoding="utf-8") as f:
        hang = [r for r in csv.DictReader(f)
                if r["phan_loai"] == "LOP CHU HONG" and r["so_hieu_ten_tep"]]
    random.shuffle(hang)
    hang = hang[:a.n]
    goc = {}
    for n_, ps in cac_pdf().items():
        for p in ps:
            goc.setdefault((n_, os.path.basename(p)), p)

    print("== E13: mo hinh (1-p)^k cho dinh danh (n=%d) ==" % len(hang))
    cap = []           # (chuan, doc_ra) o dang chuoi
    ten_cap = []       # ten tep tuong ung, de bootstrap theo TAI LIEU
    for i, r in enumerate(hang, 1):
        p = goc.get((r["nguon"], r["tep"]))
        if not p:
            continue
        try:
            s = so_doc_ra(doc_B(p))
        except Exception:
            continue
        if s:
            cap.append((r["so_hieu_ten_tep"], s))
            ten_cap.append(r["tep"])
        if i % 80 == 0:
            print("  ... %d/%d" % (i, len(hang)), flush=True)

    # ⭐ Ghi TUNG CAP ra dia. Khong co tep nay thi muon bootstrap theo TAI LIEU phai chay lai
    # 400 lan OCR (15 phut). Nguoi doc ngoai hoi dung cho nay: 125 vi tri chu so den TU DAU.
    import csv as _csv
    with io.open(os.path.join(RES, "cap-chu-so.csv"), "w", encoding="utf-8", newline="") as _f:
        _w = _csv.writer(_f); _w.writerow(["tep", "chuan", "ocr_doc_ra", "cung_do_dai"])
        for _t, (_c, _d) in zip(ten_cap, cap):
            _w.writerow([_t, _c, _d, int(len(_c) == len(_d))])
    print("\n  OCR tra ve mot so o %d/%d ca" % (len(cap), len(hang)))
    kiem(len(cap) >= 30, "du cap de uoc p", "%d cap" % len(cap))
    if len(cap) < 30:
        print("=> CHUA DAT"); return 1

    # --- uoc p tu cac cap CUNG DO DAI
    cung = [(c, d) for c, d in cap if len(c) == len(d)]
    sai_cs = sum(1 for c, d in cung for x, y in zip(c, d) if x != y)
    tong_cs = sum(len(c) for c, d in cung)
    p = sai_cs / float(tong_cs) if tong_cs else 0.0
    print("  cap CUNG do dai: %d  ·  chu so sai %d/%d  =>  p = %.4f"
          % (len(cung), sai_cs, tong_cs, p))
    kiem(0 < p < 1, "p nam trong (0,1)", "%.4f" % p)

    # --- do thuc te theo do dai k
    theo_k = collections.defaultdict(lambda: [0, 0])
    for c, d in cap:
        theo_k[len(c)][1] += 1
        if c == d:
            theo_k[len(c)][0] += 1
    ks = sorted(k for k in theo_k if theo_k[k][1] >= 10)
    print("\n  %-4s %6s %10s %10s %16s" % ("k", "n", "do duoc", "du bao", "KTC 95% do"))
    do, db, lo_, hi_ = [], [], [], []
    for k in ks:
        dung, n = theo_k[k]
        t = dung / float(n)
        m = (1 - p) ** k
        l, h = wilson(dung, n)
        print("  %-4d %6d %9.3f %10.3f  [%.3f, %.3f]" % (k, n, t, m, l, h))
        do.append(t); db.append(m); lo_.append(l); hi_.append(h)
    kiem(len(ks) >= 2, "co it nhat 2 do dai du mau", "%d" % len(ks))
    kiem(all(db[i] >= db[i + 1] for i in range(len(db) - 1)), "du bao giam theo k")

    trong_ktc = sum(1 for i in range(len(ks)) if lo_[i] <= db[i] <= hi_[i])
    print("\n  du bao nam trong KTC do duoc o %d/%d do dai" % (trong_ktc, len(ks)))
    # ⛔ Tieu chi cu cua toi la `trong_ktc >= len(ks)-1`, tuc voi 2 do dai thi CHI CAN 1 diem
    # khop la tuyen bo "mo hinh khop". Qua long, va no da in ra mot phan quyet sai. Phep thu chi
    # co nghia khi CO DU DO DAI de bac bo duoc.
    du_suc = len(ks) >= 3
    khop = du_suc and trong_ktc >= len(ks) - 1
    if not du_suc:
        print("  => KHONG KET LUAN DUOC: chi %d do dai du mau, phep thu khong co suc bac bo"
              % len(ks))
    else:
        print("  => mo hinh %s" % ("KHOP" if khop else "KHONG khop: sai so chu so KHONG doc lap"))

    # doi chung: sinh so ngau nhien DUNG mo hinh, xem phep so co bat duoc khong
    rng = np.random.default_rng(SEED)
    gia = []
    for k in ks:
        n = theo_k[k][1]
        gia.append(float(rng.binomial(n, (1 - p) ** k)) / n)
    lech_gia = float(np.mean([abs(gia[i] - db[i]) for i in range(len(ks))]))
    lech_that = float(np.mean([abs(do[i] - db[i]) for i in range(len(ks))]))
    print("  doi chung: du lieu SINH TU mo hinh lech %.3f; du lieu that lech %.3f"
          % (lech_gia, lech_that))
    # ⛔ Doi chung nay PHAI duoc doc nhu mot phep do SUC MANH, khong phai mot dau tick. Neu du
    # lieu SINH TU chinh mo hinh cung lech ngang du lieu that thi phep so KHONG phan biet duoc
    # gi, va moi phan quyet "khop" deu vo nghia.
    kiem(lech_gia < 0.5 * lech_that,
         "doi chung CO SUC: du lieu sinh tu mo hinh lech NHO HON HAN du lieu that",
         "sinh %.3f vs that %.3f => phep thu %s" %
         (lech_gia, lech_that, "co suc" if lech_gia < 0.5 * lech_that else "KHONG co suc"))

    fig, ax = plt.subplots(figsize=(5.0, 3.0))
    ax.errorbar(ks, do, yerr=[np.array(do) - np.array(lo_), np.array(hi_) - np.array(do)],
                fmt="o", color="#3b6ea5", capsize=3, label="measured")
    kk = np.linspace(min(ks), max(ks), 50)
    ax.plot(kk, (1 - p) ** kk, "--", color="#d9534f", lw=1.4,
            label=r"model $(1-p)^k$, $p=%.3f$" % p)
    ax.set_xlabel("number of digits $k$ in the identifier")
    ax.set_ylabel("P(identifier read correctly)")
    ax.set_xticks(ks)
    ax.set_ylim(-0.03, 1.03)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "f7-mo-hinh-chu-so.pdf"))
    plt.close(fig)

    with io.open(os.path.join(RES, "so-lieu-e13.tex"), "w", encoding="utf-8") as f:
        f.write("%% SINH TU DONG. KHONG sua tay.\n")
        # ⛔ Phai sinh CA HAI: co mau RUT va so ca PHAT RA. Thieu cai dau thi van xuoi lay
        # nham cai sau lam cai truoc. Do la dung loi nguoi doc ngoai bat o vong doc thu hai:
        # bai viet "mot lan rut 92 tai lieu, may tra ve so o 92 ca", tuc ti le phat ra 100%,
        # mau thuan voi chinh Bang 6 (59/250) va Bang 8 (61/200) cua bai.
        f.write("\\newcommand{\\digitRut}{%d}\n" % len(hang))
        f.write("\\newcommand{\\digitPhatRa}{%.1f}\n" % (100.0 * len(cap) / len(hang)))
        f.write("\\newcommand{\\digitP}{%.3f}\n" % p)
        f.write("\\newcommand{\\digitN}{%d}\n" % len(cap))
        f.write("\\newcommand{\\digitSai}{%d}\n" % sai_cs)
        f.write("\\newcommand{\\digitTong}{%d}\n" % tong_cs)
        f.write("\\newcommand{\\digitKhop}{%d}\n" % trong_ktc)
        f.write("\\newcommand{\\digitSoK}{%d}\n" % len(ks))
    print("\n=> %s (%d loi). Da sinh F7." % ("DAT" if not loi else "CHUA DAT", len(loi)))
    for x in loi:
        print("   loi: " + x)
    return 0 if not loi else 1


if __name__ == "__main__":
    sys.exit(main())
