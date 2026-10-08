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
    # ⛔ Ca nay tung KHONG bat duoc, va ly do la ca tiem CU chu khong phai cong hong:
    # tab:sohieu nay duoc nhac HAI lan, nen bo mot cho van con mot. Phai bo HET.
    # ⛔ Ca nay da hong HAI lan vi cung mot ly do: no go tham chieu o MOT tep, ma so tham
    # chieu toi tab:sohieu cu tang len theo cac vong sua. Nay no go o MOI tep muc, nen no
    # khong the cu nua.
    ("B13 bang mo coi", "__MOI_MUC__",
     lambda t: t.replace("(Table~\\ref{tab:sohieu})", "").replace(
         "Table~\\ref{tab:sohieu}", "that table"),
     "B13 moi bang"),
    ("B8 thuat ngu dan so", os.path.join(S, "01-intro.tex"),
     chen_sau("\\section{Introduction}", "\n\nWe study the scanned corpus here.\n"), "B8"),
    ("B12 ten tac gia da bo", os.path.join(S, "01-intro.tex"),
     chen_sau("\\section{Introduction}", "\n\nThanks to Nam Hoang for comments.\n"), "B12"),
    # ⛔ Day phai du MANH de thoc ra NGOAI khoi chu cua lop tai lieu dang dung. Ban cu day
    # 25mm, dung voi `article` le 2,5cm nhung KHONG dung voi `elsarticle` le 4,45cm.
    ("B16 muc tran ra le", os.path.join(S, "01-intro.tex"),
     chen_sau("\\section{Introduction}",
              "\n\n\\noindent\\hspace*{-40mm}\\rule{45mm}{4pt}\n"),
     "B16 khong co muc thoc ra ngoai khoi chu"),
    ("B14 vuot han muc trang", os.path.join(S, "07-conclusion.tex"),
     lambda t: t + "\n" + "\\clearpage\\mbox{}\\vfill\\mbox{}\n" * 8,
     "B14 so trang trong han muc"),
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
    ("B14 tom tat qua 250 tu", "paper/main.tex",
     doi("We propose no fix;",
         "We note that the rule examined here is applied by essentially every document "
         "processing stack in production use today, that the archive studied was assembled "
         "over roughly two decades of ordinary institutional practice without any intent to "
         "serve as a research corpus, and that the measurements reported below were therefore "
         "taken on a collection whose composition nobody designed. We propose no fix;"),
     "B14 tom tat <= 250 tu"),
    ("B14 Highlight qua 85 ky tu", "paper/main.tex",
     doi("\\item A complete \\texttt{/ToUnicode} CMap halves the odds that a text layer is usable.",
         "\\item A complete \\texttt{/ToUnicode} CMap halves the odds that a given text layer "
         "turns out to be usable in practice."),
     "B14 moi Highlight <= 85 ky tu"),
    ("B3 hinh moi chua khai", os.path.join("code", "hinh-khong-dung.txt"),
     doi("f7-mo-hinh-chu-so.pdf", "#f7-mo-hinh-chu-so.pdf"),
     "B3 hinh khong dung deu da duoc khai"),
    ("B15 ten macro co chu so", os.path.join("results", "so-lieu-e17.tex"),
     lambda t: t + "\\newcommand{\\thuNghiem2}{1}\n", "B15 ten macro chi gom chu cai"),
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

    # muc tieu dac biet: ap phep bien doi len MOI tep muc
    no_rong = []
    for ten, t, bien, cho in cases:
        if t == "__MOI_MUC__":
            no_rong.append((ten, sorted(os.path.relpath(x, GOC) for x in
                                        glob.glob(os.path.join(GOC, S, "*.tex"))), bien, cho))
        else:
            no_rong.append((ten, [t], bien, cho))
    cases = no_rong

    # --- sao luu TRUOC, va xac minh ban sao
    tep = sorted({x for c in cases for x in c[1]})
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
        for ten, ts, bien, cho in cases:
            cu = {t: io.open(os.path.join(GOC, t), encoding="utf-8").read() for t in ts}
            try:
                for t in ts:
                    io.open(os.path.join(GOC, t), "w", encoding="utf-8").write(bien(cu[t]))
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
                for t in ts:
                    io.open(os.path.join(GOC, t), "w", encoding="utf-8").write(cu[t])
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
