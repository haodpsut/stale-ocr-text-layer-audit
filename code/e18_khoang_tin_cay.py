#!/usr/bin/env python3
"""E18: khoang tin cay cho hai so NGUOI DOC NGOAI doi.  python3 code/e18_khoang_tin_cay.py

Sinh tu hai yeu cau cua vong doc ngoai 08/10/2026:

  (1) `p` co khoang tinh tren 125 VI TRI chu so nhu the chung doc lap, nhung cac vi tri trong
      cung mot dinh danh dung chung mot tai lieu, mot ban quet, mot kieu chu. Phai bootstrap
      theo TAI LIEU, va phai noi ro khoang theo vi tri la LAC QUAN.
  (2) `lambda*` la hien vat van hanh cua bai, in toi ba chu so thap phan, ma KHONG co khoang
      nao. No la ti so hai ti le GHEP CAP tren cung tai lieu nen phai bootstrap ghep cap.

Them: lan rut 250 tai lieu cua bai ngu y mot lambda* khac. Kiem xem hai lan rut co TUONG THICH
khong bang Fisher chinh xac, va neu co thi tinh ca ban GOP.

Doc tu:  results/cap-chu-so.csv   (e13 ghi ra)
         results/ket-cuc.csv      (e15 ghi ra)
         results/so-hieu-n250.log (lan rut 250)

TU KIEM:
  K1 so vi tri va so chu so sai dung lai tu CSV phai khop macro \\digitPN \\digitSai dang in
  K2 khoang theo TAI LIEU phai RONG HON hoac bang khoang theo VI TRI (neu hep hon la bo do hong)
  K3 lambda* diem uoc tu CSV phai khop macro \\bnSoHoaVon dang in
  K4 khoang bootstrap phai CHUA diem uoc
  K5 doi chung: bootstrap tren du lieu KHONG co bien thien phai cho khoang co be rong 0
"""
import collections, csv, io, math, os, random, re, sys

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(GOC, "results")
SEED = 20260923
B = 10000
loi = []


def kiem(dk, ten, ct=""):
    if not dk:
        loi.append(ten)
    print("  %s %s%s" % ("DAT " if dk else "HONG", ten, ("  [" + ct + "]") if ct else ""))


def macro():
    import glob
    d = {}
    for f in glob.glob(os.path.join(RES, "so-lieu*.tex")):
        for k, v in re.findall(r"\\newcommand\{\\(\w+)\}\{([^}]*)\}",
                               io.open(f, encoding="utf-8").read()):
            d[k] = v
    return d


def pt(xs, q):
    xs = sorted(xs)
    return xs[max(0, min(len(xs) - 1, int(round(q * (len(xs) - 1)))))]


def fisher(a, b, c, d):
    """Fisher chinh xac hai duoi cho bang 2x2 [[a,b],[c,d]]."""
    def lg(n):
        return math.lgamma(n + 1)

    def pr(x):
        return math.exp(lg(a + b) + lg(c + d) + lg(a + c) + lg(b + d)
                        - lg(a + b + c + d) - lg(x) - lg(a + b - x)
                        - lg(a + c - x) - lg(d - a + x))
    p0 = pr(a)
    tong = 0.0
    for x in range(max(0, a - d), min(a + b, a + c) + 1):
        v = pr(x)
        if v <= p0 * (1 + 1e-9):
            tong += v
    return min(1.0, tong)


def main():
    print("== E18: khoang tin cay cho p va lambda* ==")
    mac = macro()
    rnd = random.Random(SEED)
    ra = {}

    # ---------------- (1) p, bootstrap theo TAI LIEU
    pcs = os.path.join(RES, "cap-chu-so.csv")
    if not os.path.exists(pcs):
        kiem(False, "doc duoc results/cap-chu-so.csv (chay code/e13_mo_hinh_chu_so.py truoc)")
        print("=> CHUA DAT"); return 1
    hang = list(csv.DictReader(io.open(pcs, encoding="utf-8")))
    cung = [h for h in hang if h["cung_do_dai"] == "1"]
    # moi tai lieu -> (so vi tri, so vi tri sai)
    theo_tep = []
    for h in cung:
        c, d = h["chuan"], h["ocr_doc_ra"]
        theo_tep.append((len(c), sum(1 for x, y in zip(c, d) if x != y)))
    n_vt = sum(a for a, _ in theo_tep)
    n_sai = sum(b for _, b in theo_tep)
    p_hat = n_sai / float(n_vt)
    print("  p: %d tai lieu tra ve so · %d cap cung do dai · %d vi tri · %d sai => p = %.4f"
          % (len(hang), len(cung), n_vt, n_sai, p_hat))
    # ⛔ CA HO khoang cua p nay o DAY, khong o e13. Truoc do `so-lieu-e13.tex` co
    # digitPLo/digitPHi/digitPN nhung ban ma e13 hien tai KHONG sinh chung: do la tep TON tu
    # mot ban ma cu. Mot con so con song trong tep ma khong con ai sinh ra no la mot cho o MA.
    kiem(mac.get("digitTong") == str(n_vt) and mac.get("digitSai") == str(n_sai),
         "K1 so vi tri va so sai khop macro e13 sinh ra",
         "%s/%s vs %d/%d" % (mac.get("digitTong"), mac.get("digitSai"), n_vt, n_sai))
    # K1b: chuoi RUT -> PHAT RA -> CUNG DO DAI -> VI TRI phai giam dan va ti le phat ra phai
    # nam cung co voi ti le o Bang 6 va Bang 8. Day la phep bat dung cai loi vong 2.
    rut = int(mac.get("digitRut", "0") or 0)
    phat = len(hang)
    kiem(rut > phat > len(cung) and n_vt >= len(cung),
         "K1b chuoi rut > phat ra > cap cung do dai",
         "%d > %d > %d, vi tri %d" % (rut, phat, len(cung), n_vt))
    tl = 100.0 * phat / rut if rut else 0
    kiem(5.0 < tl < 60.0, "K1b ti le phat ra nam trong co hop ly", "%.1f%%" % tl)

    def boot_p(don_vi):
        out = []
        for _ in range(B):
            m = [don_vi[rnd.randrange(len(don_vi))] for _ in range(len(don_vi))]
            tv = sum(a for a, _ in m)
            out.append(sum(b for _, b in m) / float(tv) if tv else 0.0)
        return pt(out, 0.025), pt(out, 0.975)

    vt_don = [(1, 1)] * n_sai + [(1, 0)] * (n_vt - n_sai)      # theo VI TRI
    lo_vt, hi_vt = boot_p(vt_don)
    lo_tl, hi_tl = boot_p(theo_tep)                             # theo TAI LIEU
    print("  khoang theo VI TRI   : [%.3f, %.3f]" % (lo_vt, hi_vt))
    print("  khoang theo TAI LIEU : [%.3f, %.3f]  <- cai nay la cai dung" % (lo_tl, hi_tl))
    kiem(hi_tl - lo_tl >= (hi_vt - lo_vt) - 1e-9,
         "K2 khoang theo tai lieu khong hep hon khoang theo vi tri",
         "%.4f vs %.4f" % (hi_tl - lo_tl, hi_vt - lo_vt))

    ra.update({"digitPN": "%d" % n_vt,
               "digitPLo": "%.3f" % lo_vt, "digitPHi": "%.3f" % hi_vt,
               "digitCung": "%d" % len(cung),
               "digitViTri": "%.1f" % (n_vt / float(len(cung))),
               "digitPCumLo": "%.3f" % lo_tl, "digitPCumHi": "%.3f" % hi_tl,
               "tranCao": "%.1f" % (100 * (1 - p_hat)),
               "tranCaoLo": "%.1f" % (100 * (1 - hi_tl)),
               "tranCaoHi": "%.1f" % (100 * (1 - lo_tl))})

    # ---------------- (2) lambda*, bootstrap GHEP CAP theo tai lieu
    pkc = os.path.join(RES, "ket-cuc.csv")
    if not os.path.exists(pkc):
        kiem(False, "doc duoc results/ket-cuc.csv (chay code/e15_ba_nhanh.py truoc)")
        print("=> CHUA DAT"); return 1
    kc = [h for h in csv.DictReader(io.open(pkc, encoding="utf-8")) if h["truong"] == "so hieu"]
    DUNG, SAI = "0", "1"
    n = len(kc)
    dA = sum(1 for h in kc if h["A"] == DUNG); sA = sum(1 for h in kc if h["A"] == SAI)
    dB = sum(1 for h in kc if h["B"] == DUNG); sB = sum(1 for h in kc if h["B"] == SAI)
    lam = ((dB - dA) / float(n)) / ((sB - sA) / float(n))
    print("  lambda*: n=%d · A %d dung/%d sai · B %d dung/%d sai => %.4f" % (n, dA, sA, dB, sB, lam))
    kiem(abs(float(mac.get("bnSoHoaVon", "0")) - lam) < 5e-4,
         "K3 diem uoc khop macro dang in", "%s vs %.4f" % (mac.get("bnSoHoaVon"), lam))

    def boot_lam(rows):
        out = []
        for _ in range(B):
            m = [rows[rnd.randrange(len(rows))] for _ in range(len(rows))]
            k = len(m)
            a1 = sum(1 for h in m if h["A"] == DUNG); a2 = sum(1 for h in m if h["A"] == SAI)
            b1 = sum(1 for h in m if h["B"] == DUNG); b2 = sum(1 for h in m if h["B"] == SAI)
            de = (b2 - a2) / float(k)
            if de > 0:
                out.append(((b1 - a1) / float(k)) / de)
        return out

    bs = boot_lam(kc)
    lo_l, hi_l = pt(bs, 0.025), pt(bs, 0.975)
    print("  bootstrap ghep cap, %d lan: [%.3f, %.3f] (%d/%d lan co dEps > 0)"
          % (B, lo_l, hi_l, len(bs), B))
    kiem(lo_l <= lam <= hi_l, "K4 khoang chua diem uoc",
         "%.3f trong [%.3f, %.3f]" % (lam, lo_l, hi_l))

    # doi chung K5: du lieu KHONG co bien thien thi khoang phai rong 0
    gia = [{"A": DUNG, "B": SAI} for _ in range(n)]
    bs0 = boot_lam(gia)
    kiem(not bs0 or (pt(bs0, 0.975) - pt(bs0, 0.025)) < 1e-9,
         "K5 doi chung: du lieu khong bien thien cho khoang rong 0",
         "%.6f" % ((pt(bs0, 0.975) - pt(bs0, 0.025)) if bs0 else 0.0))

    # ---------------- lan rut 250 va phep gop
    t250 = io.open(os.path.join(RES, "so-hieu-n250.log"), encoding="utf-8").read()
    m = re.search(r"B OCR hien dai\s*\n\s*DUNG\s+(\d+)\s.*?SAI TRONG NHU THAT\s+(\d+)\s", t250, re.S)
    n250 = int(re.search(r"n thuc te = (\d+)", t250).group(1))
    d250, s250 = int(m.group(1)), int(m.group(2))
    lam250 = (d250 / float(n250)) / (s250 / float(n250))
    dG = (dB - dA) + d250
    sG = (sB - sA) + s250
    lamG = (dG / float(n + n250)) / (sG / float(n + n250))
    p_rec = fisher(dB, n - dB, d250, n250 - d250)
    p_eps = fisher(sB, n - sB, s250, n250 - s250)
    print("  lan rut 250: %d dung / %d sai => lambda* = %.4f" % (d250, s250, lam250))
    print("  Fisher hai duoi: phuc hoi p = %.3f · sai im p = %.3f  => %s"
          % (p_rec, p_eps, "TUONG THICH, gop duoc" if min(p_rec, p_eps) > 0.05 else "KHONG gop"))
    print("  gop hai lan rut: lambda* = %.4f" % lamG)

    ra.update({"bnSoHoaVonHai": "%.2f" % lam, "bnSoHoaVonLo": "%.2f" % lo_l,
               "bnSoHoaVonHi": "%.2f" % hi_l, "bnSoHoaVonHaiTram": "%.2f" % lam250,
               "bnSoHoaVonGop": "%.2f" % lamG,
               "bnFisherRec": "%.2f" % p_rec, "bnFisherEps": "%.2f" % p_eps})

    if loi:
        print("\n=> CHUA DAT, KHONG ghi (%d loi)" % len(loi))
        for x in loi:
            print("   loi: " + x)
        return 1
    xau = [k for k in ra if not k.isalpha()]
    assert not xau, "ten macro co chu so: %s" % xau
    with io.open(os.path.join(RES, "so-lieu-e18.tex"), "w", encoding="utf-8") as f:
        f.write("%% SINH TU DONG boi code/e18_khoang_tin_cay.py. KHONG sua tay.\n")
        for k in sorted(ra):
            f.write("\\newcommand{\\%s}{%s}\n" % (k, ra[k]))
    print("\n  da ghi results/so-lieu-e18.tex (%d macro)" % len(ra))
    print("=> DAT")
    return 0


if __name__ == "__main__":
    sys.exit(main())
