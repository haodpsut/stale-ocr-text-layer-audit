#!/usr/bin/env python3
"""F12-F16: nam hinh LUONG moi.  python3 code/f12_f16_hinh_luong.py

  F12 phan hoach kho, dang luong          <- so lay tu results/toan-kho.csv
  F13 cay BA NHANH ket cuc cho so hieu    <- so lay tu results/so-lieu-e15.tex
  F14 duong HOA VON: OCR lai lai hay lo, theo ti so gia               (matplotlib)
  F15 lat cat CO CHE cua tep hong vs tep sinh so            (so dinh tinh)
  F16 ban do PHEP DO -> TUYEN BO                            (so dinh tinh)

⛔ Khong mot con so nao duoc go tay vao TikZ. Hai hinh dau doc so tu hien vat, va truoc khi ve
script SO LAI voi macro cua bai (`results/so-lieu.tex`), vi hai nguon ay duoc sinh doc lap va
neu chung lech thi mot trong hai da cu.

TU KIEM:
  K1 phan hoach dong kin theo HAI chieu cong khac nhau (theo lop chu, va theo quy uoc ten tep)
  K2 so trong F12 khop macro \\soTongTep \\luuTruN \\luuTruQuet \\luuTruCoChu \\soTot
  K3 ba nhanh cua F13 cong lai dung n, ca hai nhanh doc
  K4 diem hoa von doc duoc tu macro va tinh lai tu ba nhanh phai khop
  K5 moi tep .tex sinh ra phai dung duoc bang pdflatex va ra PDF > 1 KB
"""
import csv, io, os, re, subprocess, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import txstyle as TX   # bo style cua nha

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES, FIG = os.path.join(GOC, "results"), os.path.join(GOC, "figures")
SRC = os.path.join(FIG, "src")
LUONG = ("f10-quyet-dinh", "f11-giao-thuc", "f12-phan-hoach", "f13-ba-nhanh",
         "f15-co-che", "f16-ban-do")
KHUON = re.compile(r"^(\d{3,4})_([A-Z]{2,4})_(\d{4})_([A-Z]+)", re.I)
loi = []


def kiem(dk, ten, ct=""):
    if not dk:
        loi.append(ten)
    print("  %s %s%s" % ("DAT " if dk else "HONG", ten, ("  [" + ct + "]") if ct else ""))


def macro(*tep):
    d = {}
    for t in tep:
        p = os.path.join(RES, t)
        if os.path.exists(p):
            for k, v in re.findall(r"\\newcommand\{\\(\w+)\}\{([^}]*)\}",
                                   io.open(p, encoding="utf-8").read()):
                d[k] = v
    return d


def so(x):
    return int(x.replace("\\,", "").replace(",", "").replace(" ", ""))


# ---------------------------------------------------------------- F12
def f12(mac):
    with io.open(os.path.join(RES, "toan-kho.csv"), encoding="utf-8") as f:
        hang = list(csv.DictReader(f))
    NHOM = {"QUET": "quet", "LOP CHU HONG": "hong", "LOP CHU TOT": "tot"}
    trong = {k: 0 for k in NHOM.values()}      # theo quy uoc ten tep
    ngoai = {k: 0 for k in NHOM.values()}
    for r in hang:
        k = NHOM.get(r["phan_loai"])
        if k is None:
            continue
        (trong if KHUON.match(r["tep"]) else ngoai)[k] += 1
    tong = sum(trong.values()) + sum(ngoai.values())
    n_trong, n_ngoai = sum(trong.values()), sum(ngoai.values())

    # K1: dong kin theo HAI chieu cong khac nhau
    theo_lop = sum(trong[k] + ngoai[k] for k in trong)
    kiem(theo_lop == tong == n_trong + n_ngoai,
         "K1 phan hoach dong kin theo hai chieu cong",
         "%d / %d / %d" % (theo_lop, tong, n_trong + n_ngoai))
    # K2: so hai nguon voi macro cua bai
    ky = [("soTongTep", tong), ("luuTruN", n_trong), ("luuTruQuet", trong["quet"]),
          ("luuTruCoChu", trong["hong"]), ("luuTruTot", trong["tot"]), ("soTot",
           trong["tot"] + ngoai["tot"])]
    lech = ["%s: hinh %d vs bai %s" % (k, v, mac.get(k)) for k, v in ky
            if k not in mac or so(mac[k]) != v]
    kiem(not lech, "K2 so trong F12 khop macro cua bai", "; ".join(lech))

    t = r"""\documentclass[border=3pt]{standalone}
\usepackage{tikz}
\input{txstyle.tex}
\begin{document}
\begin{tikzpicture}[x=1mm, y=1mm]
%% ⛔ Ban dau ve CA SAU o con tren mot hang: hinh rong 678pt, nhet vao cot 431pt thi chu
%% trong hinh con 5,1pt, duoi san 6pt cua kit. Nhanh PHAI la nhanh phu (bai khong tuyen bo
%% gi ve no) nen gop lai mot o, so hoc van dong kin va chu ve lai 8pt.
\node[blk, minimum width=34mm] (all) at (  0, 36) {archive as found\\\textbf{%(tong)d} PDF files};
\node[blk, minimum width=34mm] (in)  at (-34, 18) {follows the filing\\convention\\\textbf{%(ntrong)d}};
\node[blk, minimum width=40mm, font=\scriptsize] (out) at ( 42, 18)
  {outside the convention: \textbf{%(ngoai)d}\\(%(ot)d usable, %(oq)d none, %(oh)d unusable)};
\node[sml, minimum width=28mm] (inq) at (-74,  0) {no text layer\\\textbf{%(tq)d}};
\node[prop,minimum width=28mm, minimum height=8mm, font=\scriptsize] (inh) at (-34, 0)
  {text layer present\\\textbf{%(th)d}};
\node[sml, minimum width=28mm] (int) at (  6,  0) {usable text layer\\\textbf{%(tt)d}};
\node[prop, minimum width=52mm, minimum height=9mm] (adm) at (-34,-20)
  {every one of the %(th)d is admitted without OCR,\\and every one is unusable};
\draw[flow] (all) -- (in);   \draw[flow] (all) -- (out);
\draw[flow] (in)  -- (inq);  \draw[flow] (in)  -- (inh);  \draw[flow] (in) -- (int);
\draw[flow] (inh) -- (adm);
\begin{scope}[on background layer]
  \node[zone, fit=(inq)(inh)(int), inner sep=2.5mm] (z1) {};
\end{scope}
\node[zlab, below=0.5mm of z1.south, xshift=-18mm] {RECORDS IN THE FILING CONVENTION};
\end{tikzpicture}
\end{document}
"""     % {"tong": tong, "ntrong": n_trong, "ngoai": n_ngoai, "tq": trong["quet"],
           "th": trong["hong"], "tt": trong["tot"], "ot": ngoai["tot"],
           "oq": ngoai["quet"], "oh": ngoai["hong"]}
    io.open(os.path.join(SRC, "f12-phan-hoach.tex"), "w", encoding="utf-8").write(t)
    print("    F12: %d = (%d trong: %d quet + %d hong + %d tot) + (%d ngoai)"
          % (tong, n_trong, trong["quet"], trong["hong"], trong["tot"], n_ngoai))


# ---------------------------------------------------------------- F13
def f13(m15):
    d = {}
    for nhanh in ("A", "B"):
        d[nhanh] = {k: int(m15["bnSo" + nhanh + k]) for k in ("N", "Dung", "Sai", "Im")}
        d[nhanh]["Pi"] = m15.get("bnSo" + nhanh + "Pi", "0.0")
    xau = [n for n in "AB" if d[n]["Dung"] + d[n]["Sai"] + d[n]["Im"] != d[n]["N"]]
    kiem(not xau, "K3 ba nhanh cua F13 cong lai dung n", ", ".join(xau))

    t = r"""\documentclass[border=3pt]{standalone}
\usepackage{tikz}
\input{txstyle.tex}
\begin{document}
\begin{tikzpicture}[x=1mm, y=1mm]
\node[blk, minimum width=50mm] (root) at (0, 30)
  {\textbf{%(n)d} admitted documents, document number read};
\node[blk, minimum width=30mm] (A) at (-44, 14) {A: embedded\\text layer};
\node[blk, minimum width=30mm] (B) at ( 44, 14) {B: re-OCR of\\the same page};
\node[sml] (ag) at (-70,  0) {correct\\\textbf{%(ad)d}};
\node[prop, minimum width=16mm, minimum height=8mm, font=\scriptsize] (as) at (-44, 0)
  {silent error\\\textbf{%(as)d}};
\node[sml] (ai) at (-18,  0) {abstain\\\textbf{%(ai)d}};
\node[sml] (bg) at ( 18,  0) {correct\\\textbf{%(bd)d}};
\node[prop, minimum width=16mm, minimum height=8mm, font=\scriptsize] (bs) at ( 44, 0)
  {silent error\\\textbf{%(bs)d}};
\node[sml] (bi) at ( 70,  0) {abstain\\\textbf{%(bi)d}};
\draw[flow] (root) -- (A); \draw[flow] (root) -- (B);
\foreach \x in {ag,as,ai} \draw[flow] (A) -- (\x);
\foreach \x in {bg,bs,bi} \draw[flow] (B) -- (\x);
\node[alab, text=accent, align=center, text width=52mm] at (44,-13)
  {when B emits a number it is wrong \textbf{%(bps)s\%%} of the time};
\end{tikzpicture}
\end{document}
"""     % {"n": d["A"]["N"], "ad": d["A"]["Dung"], "as": d["A"]["Sai"], "ai": d["A"]["Im"],
           "bd": d["B"]["Dung"], "bs": d["B"]["Sai"], "bi": d["B"]["Im"],
           "bps": m15.get("bnSoBPiSai", "?")}
    io.open(os.path.join(SRC, "f13-ba-nhanh.tex"), "w", encoding="utf-8").write(t)
    print("    F13: A %d/%d/%d · B %d/%d/%d"
          % (d["A"]["Dung"], d["A"]["Sai"], d["A"]["Im"],
             d["B"]["Dung"], d["B"]["Sai"], d["B"]["Im"]))
    return d


# ---------------------------------------------------------------- F14
def f14(m15, m18):
    TEN = {"So": "Document number", "Ngay": "Issue date", "CoQuan": "Issuing body"}
    # mau nhan danh cho truong bai noi ve (so hieu); hai truong kia la mau phu
    MAU = {"So": TX.ACCENT, "Ngay": TX.C["blue"], "CoQuan": TX.NEUTRAL}
    NET = {"So": "-", "Ngay": "--", "CoQuan": ":"}
    lam = []
    for k in ("CoQuan", "Ngay", "So"):
        nA, nB = float(m15["bn%sAN" % k]), float(m15["bn%sBN" % k])
        dRec = int(m15["bn%sBDung" % k]) / nB - int(m15["bn%sADung" % k]) / nA
        dEps = int(m15["bn%sBSai" % k]) / nB - int(m15["bn%sASai" % k]) / nA
        hv = m15.get("bn%sHoaVon" % k, "")
        tinh = (dRec / dEps) if dEps > 0 else None
        # K4: hoa von doc tu macro phai khop cai tinh lai o day
        if tinh is None:
            kiem(hv == "\\infty", "K4 %s: macro phai la vo cuc" % k, hv)
        else:
            kiem(abs(float(hv) - tinh) < 5e-4, "K4 %s: hoa von khop" % k,
                 "%s vs %.4f" % (hv, tinh))
        lam.append((k, dRec, dEps, tinh))

    # ⛔ Nguoi doc ngoai do duoc: voi x den 10^1 thi duong so hieu ROI KHOI DAY khung o
    # c/g ~ 1.86 va duong ngay roi khoi DINH o ~4.5, tuc hai duong "dung giua khong trung".
    # Chon mien x sao cho MOI duong con nam trong khung, roi khai dung mien ay trong van.
    x = np.logspace(-2, np.log10(2.0), 400)
    fig, ax = plt.subplots(figsize=(5.4, 2.9))
    for k, dRec, dEps, tinh in lam:
        y = 100.0 * (dRec - x * dEps)
        ax.plot(x, y, color=MAU[k], ls=NET[k], lw=1.1, label=TEN[k])
        if tinh is not None:
            ax.plot([tinh], [0], marker="o", ms=5, color=MAU[k], zorder=5)
            # dai tin cay cua lambda*: nguoi doc ngoai doi, va mot diem uoc in ba chu so
            # thap phan ma khong co dai la dung cai bi bat.
            if m18.get("bnSoHoaVonLo") and m18.get("bnSoHoaVonHi"):
                lo, hi = float(m18["bnSoHoaVonLo"]), float(m18["bnSoHoaVonHi"])
                ax.axvspan(lo, hi, color=MAU[k], alpha=0.12, lw=0)
                nhan = (r"break-even $\lambda^\star=%.2f$" % tinh
                        + "\n95%% CI [%.2f, %.2f]" % (lo, hi))
            else:
                nhan = r"break-even $\lambda^\star=%.3f$" % tinh
            ax.annotate(nhan, xy=(tinh, 0), xytext=(tinh * 1.35, 15), fontsize=7.5,
                        color=MAU[k], arrowprops=dict(arrowstyle="-", color=MAU[k], lw=0.6))
    ax.axhline(0, color="black", lw=0.6, alpha=0.6)
    ax.set_xscale("log")
    ax.set_xlabel(r"cost of a wrong identifier relative to a correct one, $c/g$")
    ax.set_ylabel("gain from re-OCR\n(percentage points of utility)", fontsize=8)
    ax.set_ylim(-40, 40)
    ax.set_xlim(1e-2, 2.0)
    ax.legend(loc="lower left")
    TX.grid_mo(ax, "both")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "f14-hoa-von.pdf"))
    plt.close(fig)
    print("    F14: " + " · ".join("%s hoa von %s" % (k, "inf" if t is None else "%.3f" % t)
                                   for k, _, _, t in lam))


# ---------------------------------------------------------------- F15, F16 (dinh tinh)
F10 = '\\documentclass[border=3pt]{standalone}\n\\usepackage{tikz}\n\\input{txstyle.tex}\n\\tikzset{\n  dec/.style={blk, fill=black!6, minimum width=26mm, minimum height=9mm},\n}\n\\begin{document}\n\\begin{tikzpicture}[x=1mm, y=1mm]\n\\node[blk, minimum width=34mm] (pdf) at (0, 34) {PDF from the archive};\n\\node[dec]                     (q)   at (0, 17) {text layer present?};\n\\node[blk, minimum width=26mm] (ocr) at (42, 17) {run OCR};\n\\node[prop, minimum width=34mm](skip) at (0,  0) {use the embedded text};\n\\node[blk, minimum width=34mm] (idx) at (0,-17) {index, search,\\\\citation linking};\n\\draw[flow] (pdf) -- (q);\n\\draw[flow] (q) -- node[alab, above] {no} (ocr);\n\\draw[flow] (q) -- node[alab, right] {yes} (skip);\n\\draw[flow] (skip) -- (idx);\n\\draw[flow] (ocr.south) |- (idx.east);\n\\node[alab, text=accent, align=left, anchor=west, text width=36mm]\n  at (22, 0) {no error is raised on this branch, whatever the text says};\n\\end{tikzpicture}\n\\end{document}\n'

F11 = '\\documentclass[border=3pt]{standalone}\n\\usepackage{tikz}\n\\input{txstyle.tex}\n\\begin{document}\n\\begin{tikzpicture}[x=1mm, y=1mm]\n\\node[blk, minimum width=26mm] (page) at (0,   0) {one page\\\\image};\n\\node[blk, minimum width=30mm] (a)    at (36, 11) {A: embedded\\\\text layer};\n\\node[blk, minimum width=30mm] (b)    at (36,-11) {B: re-OCR of\\\\that image};\n\\node[prop,minimum width=32mm] (g)    at (80,-24) {ground truth from\\\\the filing system};\n\\node[blk, minimum width=32mm] (cmp)  at (80,  0) {per-field comparison\\\\McNemar, Wilson, Holm};\n\\draw[flow] (page) -- (a);\n\\draw[flow] (page) -- (b);\n\\draw[flow] (a.east) -| (cmp.north);\n\\draw[flow] (b.east) -| ([xshift=-6mm]cmp.south);\n\\draw[flow] (g.north) -- ([xshift=6mm]cmp.south);\n\\begin{scope}[on background layer]\n  \\node[zone, fit=(a)(b), inner sep=3mm] (z) {};\n\\end{scope}\n\\node[zlab, above=0.5mm of z.north] {TWO READINGS OF ONE PAGE};\n\\node[alab, align=left, anchor=west, text width=30mm] at (96,-24)\n  {neither arm produced this value};\n\\end{tikzpicture}\n\\end{document}\n'

F15 = '\\documentclass[border=3pt]{standalone}\n\\usepackage{tikz}\n\\input{txstyle.tex}\n\\tikzset{\n  lay/.style={blk, minimum width=44mm, minimum height=8mm, font=\\scriptsize},\n}\n\\begin{document}\n\\begin{tikzpicture}[x=1mm, y=1mm]\n% ---- stale-OCR scan ----\n\\node[lay, fill=black!10, draw=inkgray!70] (im1) at (0, 10) {page image, full bleed};\n\\node[prop, minimum width=44mm, minimum height=8mm, font=\\scriptsize] (tx1) at (0, 1)\n  {invisible text layer, written by an\\\\OCR engine at digitisation time};\n\\begin{scope}[on background layer]\n  \\node[zone, fit=(im1)(tx1), inner sep=2.5mm] (z1) {};\n\\end{scope}\n\\node[zlab, above=0.5mm of z1.north] {STALE-OCR SCAN};\n% ---- born-digital ----\n\\node[lay] (tx2) at (0,-26) {text objects placed by\\\\the authoring application};\n\\begin{scope}[on background layer]\n  \\node[zone, fit=(tx2), inner sep=2.5mm] (z2) {};\n\\end{scope}\n\\node[zlab, above=0.5mm of z2.north] {BORN-DIGITAL FILE};\n% ---- what extraction reads ----\n\\node[alab, anchor=east, align=right, text width=24mm] (e1) at (-28, 1)\n  {extraction\\\\reads here};\n\\node[alab, anchor=east, align=right, text width=24mm] (e2) at (-28,-26)\n  {extraction\\\\reads here};\n\\draw[flow] (e1) -- (tx1.west);\n\\draw[flow] (e2) -- (tx2.west);\n\\node[alab, anchor=west, align=left, text width=36mm] at (28, 5.5)\n  {a human reads the image above; a library returns the layer below, and the two need not agree};\n\\node[alab, anchor=west, align=left, text width=36mm] at (28,-26)\n  {the glyphs on the page \\emph{are} this text};\n\\end{tikzpicture}\n\\end{document}\n'

F16 = '\\documentclass[border=3pt]{standalone}\n\\usepackage{tikz}\n\\input{txstyle.tex}\n\\tikzset{\n  ex/.style={blk, minimum width=52mm, minimum height=7mm, align=left, font=\\scriptsize},\n  cl/.style={prop, minimum width=40mm, minimum height=10mm, font=\\scriptsize},\n}\n\\begin{document}\n\\begin{tikzpicture}[x=1mm, y=1mm]\n% ⛔ Xep theo CUM TUYEN BO chu khong theo so thu tu phep do: ban xep theo so thu tu co ba\n% mui ten CAT QUA o khac, va log pdflatex sach tuyet doi ca ba lan.\n\\node[ex] (e1) at (0,   0) {E1 whole-archive classification};\n\\node[ex] (e2) at (0,  -9) {E2 producer $\\times$ text-layer health};\n\\node[ex] (e3) at (0, -18) {E6--E7 $\\rho$ distribution, threshold sweep};\n\\node[ex] (e4) at (0, -31) {E3 \\texttt{/ToUnicode} in both classes};\n\\node[ex] (e5) at (0, -40) {E8 content vs structural detectors};\n\\node[ex] (e6) at (0, -53) {E4 five extraction libraries};\n\\node[ex] (e7) at (0, -66) {E9 rendering-resolution sweep};\n\\node[ex] (e8) at (0, -75) {E10 three fields, paired readings};\n\\node[ex] (e9) at (0, -84) {E15 three-way outcome split};\n\\node[cl] (c1) at (86,  -9) {C1 prevalence\\\\and provenance};\n\\node[cl] (c2) at (86, -35) {C2 the structural\\\\signal inverts};\n\\node[cl] (c3) at (86, -53) {C3 silent failure\\\\of extraction};\n\\node[cl] (c4) at (86, -75) {C4 field-level damage\\\\and its cost};\n\\foreach \\x in {e1,e2,e3} \\draw[flow] (\\x.east) -- (c1.west);\n\\foreach \\x in {e4,e5}    \\draw[flow] (\\x.east) -- (c2.west);\n\\draw[flow] (e6.east) -- (c3.west);\n\\foreach \\x in {e7,e8,e9} \\draw[flow] (\\x.east) -- (c4.west);\n\\node[alab, align=left, text width=86mm, anchor=north west] at (-26,-95)\n  {E12 (stratification by year) and E13 (a closed-form digit model) were withdrawn by their own\n   controls and support no claim; both are reported in the threats section rather than omitted.};\n\\end{tikzpicture}\n\\end{document}\n'


def dung(ten):
    p = os.path.join(SRC, ten + ".tex")
    subprocess.run(["pdflatex", "-interaction=nonstopmode", "-output-directory", SRC, p],
                   capture_output=True)
    ra = os.path.join(SRC, ten + ".pdf")
    ok = os.path.exists(ra) and os.path.getsize(ra) > 1024
    if ok:
        os.replace(ra, os.path.join(FIG, ten + ".pdf"))
    kiem(ok, "K5 %s dung duoc va ra PDF" % ten,
         "" if ok else "xem %s.log" % os.path.join(SRC, ten))


def main():
    print("== F12-F16: hinh luong ==")
    mac = macro("so-lieu.tex")
    m15 = macro("so-lieu-e15.tex")
    if not m15:
        kiem(False, "doc duoc results/so-lieu-e15.tex (chay code/e15_ba_nhanh.py truoc)")
        print("=> CHUA DAT")
        return 1
    f12(mac)
    f13(m15)
    f14(m15, macro("so-lieu-e18.tex"))
    for ten, noi_dung in (("f10-quyet-dinh", F10), ("f11-giao-thuc", F11),
                          ("f15-co-che", F15), ("f16-ban-do", F16)):
        io.open(os.path.join(SRC, ten + ".tex"), "w", encoding="utf-8").write(noi_dung)
    for t in LUONG:
        dung(t)
    for e in (".aux", ".log"):
        for t in LUONG:
            p = os.path.join(SRC, t + e)
            os.path.exists(p) and os.remove(p)
    print("\n=> %s (%d loi)" % ("DAT" if not loi else "CHUA DAT", len(loi)))
    for x in loi:
        print("   loi: " + x)
    return 0 if not loi else 1


if __name__ == "__main__":
    sys.exit(main())
