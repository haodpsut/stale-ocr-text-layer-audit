#!/usr/bin/env python3
"""TIEM LOI vao ban thao de thu CONG.  python3 code/tiem_loi.py [--ca B13]

Cong `code/cong_bai.py` bao XANH toan bo ngay lan chay dau, ca truoc va sau khi them nam phep
moi. Dieu do KHONG chung minh cong hoat dong. Tep nay tiem tung loi THAT vao ban thao, chay lai
cong, va doi dung cai phep dang le phai bat duoc no phai HONG. Phep nao khong bat duoc loi cua
chinh no thi phep ay la trang tri.

Moi ca:  (ten, tep, vieclam, phep_phai_hong)

⛔ AN TOAN TEP. Lop loi da tung lam mat trang app.js: tu kiem be hien vat that roi bi giet giua
luc ghi. Nen o day:
  1. chep SAO LUU ra thu muc tam va XAC MINH noi dung sao luu TRUOC khi sua bat cu gi;
  2. moi thay doi deu nam trong try/finally, phuc hoi ca khi Ctrl-C;
  3. cuoi lan chay doi chieu bam noi dung tung tep voi bam ban dau, lech mot tep la bao HONG.
"""
import argparse, glob, hashlib, io, os, shutil, subprocess, sys, tempfile

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(GOC, "paper")
RES = os.path.join(GOC, "results")
FIG = os.path.join(GOC, "figures")


def bam(p):
    return hashlib.sha256(io.open(p, "rb").read()).hexdigest()


# ---- cac phep bien doi, moi cai nhan noi dung tra ve noi dung
def chen_sau(moc, them):
    def f(t):
        assert t.count(moc) >= 1, "khong tim thay moc"
        return t.replace(moc, moc + them, 1)
    return f


def doi(cu, moi):
    def f(t):
        assert t.count(cu) >= 1, "khong tim thay %r" % cu[:40]
        return t.replace(cu, moi, 1)
    return f


S = os.path.join("paper", "sections")
CA = [
    ("B6 em-dash", os.path.join(S, "01-intro.tex"),
     chen_sau("\\section{Introduction}", "\n\nA sentence with an em\u2014dash in it.\n"),
     "B6"),
    ("B10 ti le go tay", os.path.join(S, "01-intro.tex"),
     chen_sau("\\section{Introduction}", "\n\nRecovery was 47.3\\% in our sample.\n"), "B10"),
    ("B7 so bon chu so go tay", os.path.join(S, "01-intro.tex"),
     chen_sau("\\section{Introduction}", "\n\nThe archive holds 4821 records.\n"), "B7"),
    ("B2 tham chieu treo", os.path.join(S, "01-intro.tex"),
     chen_sau("\\section{Introduction}", "\n\nSee Figure~\\ref{fig:khong-he-co}.\n"),
     "B2 0 tham chieu treo"),
    ("B2/B5 trich dan treo", os.path.join(S, "01-intro.tex"),
     chen_sau("\\section{Introduction}", "\n\nAs shown by \\cite{khongcotrongbib}.\n"),
     "B5 khong trich muc ngoai bib"),
    ("B2 macro thieu", os.path.join(S, "01-intro.tex"),
     chen_sau("\\section{Introduction}", "\n\nThe value is \\khongCoMacroNay{}.\n"),
     "B2 0 macro thieu"),
    ("B13 hinh mo coi", os.path.join(S, "05-threats.tex"),
     doi("Table~\\ref{tab:bodo} and Figure~\\ref{fig:roc} appear", "Table~\\ref{tab:bodo} appears"),
     "B13 moi hinh"),
    ("B13 bang mo coi", os.path.join(S, "04-results.tex"),
     doi("A separate and larger draw of \\cBonN{} documents (Table~\\ref{tab:sohieu}),",
         "A separate and larger draw of \\cBonN{} documents,"),
     "B13 moi bang"),
    ("B8 thuat ngu dan so", os.path.join(S, "01-intro.tex"),
     chen_sau("\\section{Introduction}", "\n\nWe study the scanned corpus here.\n"), "B8"),
    ("B12 ten tac gia da bo", os.path.join(S, "01-intro.tex"),
     chen_sau("\\section{Introduction}", "\n\nThanks to Nam Hoang for comments.\n"), "B12"),
    ("B16 muc tran ra le", os.path.join(S, "01-intro.tex"),
     chen_sau("\\section{Introduction}",
              "\n\n\\noindent\\hspace*{-25mm}\\rule{30mm}{4pt}\n"), "B16"),
    ("B14 vuot tran trang", os.path.join(S, "07-conclusion.tex"),
     lambda t: t + "\n" + "\\clearpage\\mbox{}\n" * 4, "B14"),
    ("B4 bang sinh ra ma khong dua vao", os.path.join(S, "04-results.tex"),
     doi("\\input{../results/tables/tab-banhanh}", "\\mbox{}"), "B4"),
    ("B15 macro moi chua khai", os.path.join("results", "so-lieu-e15.tex"),
     lambda t: t + "\\newcommand{\\macroThuNghiemChuaKhai}{1}\n", "B15"),
    ("B17 ba nhanh khong cong dung n", os.path.join("results", "so-lieu-e15.tex"),
     doi("\\newcommand{\\bnSoBIm}{139}", "\\newcommand{\\bnSoBIm}{140}"),
     "B17 bnSoB"),
    ("B17 hoa von sai", os.path.join("results", "so-lieu-e15.tex"),
     doi("\\newcommand{\\bnSoHoaVon}{0.224}", "\\newcommand{\\bnSoHoaVon}{0.500}"),
     "B17 hoa von"),
    ("B18 tu dat mau rieng", os.path.join("code", "f6_hinh_truong.py"),
     doi('color=mauA, hatch="/"', 'color="#3b6ea5", hatch="/"'),
     "B18 bo sinh hinh khong tu dat mau rieng"),
    ("B18 hinh khong nap txstyle", os.path.join("figures", "src", "f13-ba-nhanh.tex"),
     doi("\\input{txstyle.tex}", "\\usetikzlibrary{arrows.meta,positioning,fit,backgrounds}"),
     "B18 moi hinh TikZ deu nap txstyle.tex"),
]


def chay_cong():
    r = subprocess.run([sys.executable, os.path.join(GOC, "code", "cong_bai.py")],
                       capture_output=True, text=True)
    return r.returncode, r.stdout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ca", default=None, help="chi chay nhung ca co ten chua chuoi nay")
    a = ap.parse_args()
    cases = [c for c in CA if not a.ca or a.ca in c[0]]

    # --- sao luu TRUOC, va xac minh ban sao
    tep = sorted(set(c[1] for c in cases))
    kho = tempfile.mkdtemp(prefix="tiem-loi-")
    goc_bam = {}
    for t in tep:
        src = os.path.join(GOC, t)
        dst = os.path.join(kho, t.replace(os.sep, "__"))
        shutil.copy2(src, dst)
        assert bam(src) == bam(dst), "ban sao luu KHONG khop: " + t
        goc_bam[t] = bam(src)
    print("== TIEM LOI THU CONG ==")
    print("  sao luu %d tep vao %s, da xac minh bam\n" % (len(tep), kho))

    print("  kiem cong tren ban SACH truoc...")
    ma, ra = chay_cong()
    if ma != 0:
        print("  ⛔ cong da HONG san tren ban sach, khong the thu tiem loi:")
        print("\n".join(l for l in ra.splitlines() if l.startswith("   loi")))
        return 2
    print("  ban sach: cong XANH\n")

    ketqua = []
    try:
        for ten, t, bien, cho in cases:
            p = os.path.join(GOC, t)
            cu = io.open(p, encoding="utf-8").read()
            try:
                io.open(p, "w", encoding="utf-8").write(bien(cu))
                ma, ra = chay_cong()
                hong = [l.strip()[5:] for l in ra.splitlines() if l.strip().startswith("loi:")]
                bat = any(cho in h for h in hong)
                ketqua.append((ten, cho, ma != 0, bat, hong))
                print("  %s %-34s  cong %s · phep '%s' %s"
                      % ("DAT " if bat else "HONG", ten,
                         "HONG" if ma != 0 else "van XANH", cho,
                         "da bat" if bat else "KHONG bat"))
                if ma != 0 and not bat:
                    print("       (cong hong, nhung vi phep khac: %s)" % "; ".join(hong[:3]))
            finally:
                io.open(p, "w", encoding="utf-8").write(cu)
    finally:
        for t in tep:
            src = os.path.join(GOC, t)
            dst = os.path.join(kho, t.replace(os.sep, "__"))
            shutil.copy2(dst, src)
        lech = [t for t in tep if bam(os.path.join(GOC, t)) != goc_bam[t]]
        print("\n  phuc hoi: %d tep, %s"
              % (len(tep), "bam khop het" if not lech else "⛔ LECH: " + ", ".join(lech)))
        if lech:
            print("  ⛔ ban goc o: " + kho)
            return 3

    sot = [k for k in ketqua if not k[3]]
    print("\n=> %d/%d ca bi bat dung phep" % (len(ketqua) - len(sot), len(ketqua)))
    for ten, cho, _, _, hong in sot:
        print("   SOT: %s  (cho '%s', cong bao: %s)" % (ten, cho, "; ".join(hong) or "khong gi"))
    shutil.rmtree(kho, ignore_errors=True)
    return 0 if not sot else 1


if __name__ == "__main__":
    sys.exit(main())
