#!/usr/bin/env python3
"""Cong tong cho ban thao:  python3 code/cong_bai.py

Chay lai duoc moi lan sua. Kiem 12 phep. Tam phep trong so do sinh ra tu mot nhan xet THAT cua
nguoi doc ngoai vong 1, nen chung khong phai phong doan ve cai gi co the hong.

  B1  dung lai SACH (xoa moi ban trung gian truoc khi dung)
  B2  0 loi LaTeX · 0 macro thieu · 0 tham chieu treo · 0 trich dan treo · 0 Overfull
  B3  moi tep hinh duoc chen vao bai, va moi hinh duoc chen deu ton tai
  B4  moi bang da sinh duoc dua vao bai
  B5  trich dan va bib khop hai chieu
  B6  0 em-dash                                    (luat nha)
  B7  khong con so GO TAY trong than bai           (phai la macro)
  B8  thuat ngu dan so nhat quan                   <- tu doc ngoai vong 1
  B9  san journal: trang, hinh, bang, ref, phuong trinh, thuat toan
  B10 moi ti le phan tram trong bai deu la macro   <- tu doc ngoai vong 1
  B11 bo sinh so chay lai van xanh
  B12 khong con ten tac gia da bo
  B13 moi HINH va moi BANG deu duoc nhac trong van      <- 9/10 hinh tung mo coi ma cong cu khong thay
  B14 tran trang cua venue (<= 30)                      <- cong cu chi co san DUOI, khong co TREN
  B15 macro do xong ma khong dung phai duoc KHAI o code/macro-khong-dung.txt
  B16 khong co muc o LE TRAI/PHAI/TREN cua trang in     <- do tren ANH RENDER, khong tin log
  B17 tinh LAI dai so cua cac menh de, so voi macro     <- cong so HAI NGUON

⛔ B13-B17 sinh ra ngay 08/10 sau khi cong 23 phep cu bao XANH TOAN BO trong khi bai dang co
9/10 hinh va 2/8 bang khong he duoc nhac den trong van. Cong xanh lan dau khong chung minh gi;
xem code/tiem_loi.py, no tiem loi that de kiem tra tung phep co can hay khong.
"""
import glob, io, os, re, subprocess, sys

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(GOC, "paper")
loi, canh = [], []


def kiem(dk, ten, ct=""):
    (loi if not dk else canh).append(ten) if not dk else None
    print("  %s %s%s" % ("DAT " if dk else "HONG", ten, ("  [" + ct + "]") if ct else ""))


def main():
    print("== CONG TONG CHO BAN THAO ==")
    for e in (".pdf", ".aux", ".bbl", ".blg", ".out", ".log"):
        p = os.path.join(P, "main" + e)
        if os.path.exists(p):
            os.remove(p)
    for c in (["pdflatex", "-interaction=nonstopmode", "main.tex"], ["bibtex", "main"],
              ["pdflatex", "-interaction=nonstopmode", "main.tex"],
              ["pdflatex", "-interaction=nonstopmode", "main.tex"]):
        subprocess.run(c, cwd=P, capture_output=True)
    log = io.open(os.path.join(P, "main.log"), encoding="utf-8", errors="ignore").read()
    kiem(os.path.exists(os.path.join(P, "main.pdf")), "B1 dung lai sach thanh cong")

    for ten, mau in (("0 loi LaTeX", r"(?m)^!"), ("0 macro thieu", "Undefined control sequence"),
                     ("0 tham chieu treo", "LaTeX Warning: Reference"),
                     ("0 trich dan treo", r"Citation.*undefined"), ("0 Overfull", "Overfull")):
        n = len(re.findall(mau, log))
        kiem(n == 0, "B2 " + ten, str(n))

    src = "".join(io.open(f, encoding="utf-8").read()
                  for f in glob.glob(os.path.join(P, "sections", "*.tex"))
                  + [os.path.join(P, "main.tex")])
    co = set(os.path.basename(x) for x in glob.glob(os.path.join(GOC, "figures", "*.pdf")))
    dung = set(re.findall(r"includegraphics\[[^\]]*\]\{\.\./figures/([^}]+)\}", src))
    kiem(dung <= co, "B3 moi hinh duoc chen deu ton tai", ", ".join(sorted(dung - co)))
    thua = co - dung
    kiem(len(thua) <= 1, "B3 khong bo quen tep hinh",
         "chua dung: " + ", ".join(sorted(thua)) if thua else "")

    bang_co = set(os.path.basename(x)[:-4]
                  for x in glob.glob(os.path.join(GOC, "results", "tables", "*.tex")))
    bang_dung = set(re.findall(r"input\{\.\./results/tables/([a-z-]+)\}", src))
    kiem(bang_co == bang_dung, "B4 moi bang da sinh deu duoc dua vao bai",
         "thua: " + ", ".join(sorted(bang_co - bang_dung)))

    bib = set(re.findall(r"^@[a-z]*\{([a-z0-9]+),",
                         io.open(os.path.join(P, "refs.bib"), encoding="utf-8").read(), re.M))
    trich = {k.strip() for c in re.findall(r"\\cite\{([^}]*)\}", src) for k in c.split(",")}
    kiem(not (trich - bib), "B5 khong trich muc ngoai bib", ", ".join(sorted(trich - bib)))
    kiem(not (bib - trich), "B5 khong muc bib nao bi bo quen", ", ".join(sorted(bib - trich)))

    kiem("\u2014" not in src, "B6 khong em-dash")

    # B7/B10: so trong than bai phai la macro. Bo qua so mu, so phuong trinh, nam, cau hinh.
    than = re.sub(r"\\(label|ref|eqref|cite|includegraphics|input)\{[^}]*\}", "", src)
    than = re.sub(r"\$[^$]*\$", "", than)
    pc = re.findall(r"(?<!\\)\b\d+\.\d+\\%", than)
    kiem(not pc, "B10 moi ti le phan tram la macro", ", ".join(pc[:4]))
    so = [x for x in re.findall(r"(?<![\\\w.])\d{3,4}(?![\d.])", than)
          if x not in ("200", "100", "150", "300", "400", "2017", "2016", "1989", "2002")]
    kiem(not so, "B7 khong so ba bon chu so go tay trong than bai", ", ".join(so[:5]))

    cam = ["scanned sub-collection", "scanned administrative sub-collection", "scanned corpus"]
    xau = [c for c in cam if c in src]
    kiem(not xau, "B8 thuat ngu dan so nhat quan", ", ".join(xau))

    from pypdf import PdfReader
    txt = subprocess.run(["pdftotext", os.path.join(P, "main.pdf"), "-"],
                         capture_output=True, text=True).stdout
    n_tr = len(PdfReader(os.path.join(P, "main.pdf")).pages)
    # ⛔ Hai bo dem nay da SAI o lan chay dau, va ca hai deu bao bai thieu trong khi bai du:
    #   - neo "^Table" vao dau dong: pdftotext thut le mot so caption nen chi dem duoc 4/8;
    #   - tim "Algorithm N" trong MA NGUON: chuoi ay chi xuat hien trong BAN IN, nguon chi co
    #     \begin{algorithm} va \ref, nen dem ra 0 trong khi bai co 2.
    # Bai hoc lap lai: dem tren BAN IN va KHONG neo dau dong.
    n_h = len(set(re.findall(r"Figure (\d+):", txt)))
    n_b = len(set(re.findall(r"Table (\d+):", txt)))
    n_pt = len(re.findall(r"(?m)^\(\d+\)$", txt))
    n_tt = len(set(re.findall(r"Algorithm (\d+)", txt)))
    for ten, v, san in (("trang", n_tr, 10), ("hinh", n_h, 10), ("bang", n_b, 8),
                        ("tham khao", len(bib), 36), ("phuong trinh", n_pt, 8)):
        kiem(v >= san, "B9 %s >= %d" % (ten, san), str(v))
    kiem(n_tt >= 2, "B9 khoi thuat toan >= 2", str(n_tt))

    r = subprocess.run([sys.executable, os.path.join(GOC, "code", "make_claims.py")],
                       capture_output=True, text=True)
    kiem(r.returncode == 0, "B11 bo sinh so chay lai van xanh")

    bo = [x for x in ("Nam Hoang", "Dong A", "hoangvannamai", "do.hf@sut.ru") if x in txt]
    kiem(not bo, "B12 khong con ten hoac email da bo", ", ".join(bo))

    # ---- B13: nhan mo coi. Hinh/bang co trong bai ma khong cau nao nhac den.
    for ky, ten in (("fig", "hinh"), ("tab", "bang")):
        nhan = set(re.findall(r"\\label\{%s:([^}]+)\}" % ky, src))
        nhac = set(re.findall(r"\\ref\{%s:([^}]+)\}" % ky, src))
        mc = sorted(nhan - nhac)
        kiem(not mc, "B13 moi %s deu duoc nhac trong van" % ten,
             "mo coi: " + ", ".join(mc) if mc else "")

    # ---- B14: tran tren. Bai mot cot de no ra, nen phai co MOC TREN chu khong chi moc duoi.
    kiem(n_tr <= 30, "B14 khong vuot tran 30 trang", str(n_tr))

    # ---- B15: macro do duoc ma khong dua vao bai. Khong tu dong la loi, nhung phai co NGUOI
    # quyet dinh: hoac dung no, hoac khai vao tep duoi kem ly do.
    dn = set()
    for f in glob.glob(os.path.join(GOC, "results", "so-lieu*.tex")):
        dn |= set(re.findall(r"\\newcommand\{\\(\w+)\}", io.open(f, encoding="utf-8").read()))
    xai = set(re.findall(r"\\([A-Za-z]+)", src))
    kb = os.path.join(GOC, "code", "macro-khong-dung.txt")
    khai = set()
    if os.path.exists(kb):
        khai = {l.split("#")[0].strip() for l in io.open(kb, encoding="utf-8")
                if l.split("#")[0].strip()}
    # ⛔ 08/10: `aucDone` duoc sinh CA O make_claims.py lan e8_bo_do.py. LaTeX chet voi
    # "Command \\aucDone already defined" va cong cu KHONG co phep nao hoi cau "mot con so
    # co may CHO O". Nay co.
    dem = {}
    for f in sorted(glob.glob(os.path.join(GOC, "results", "so-lieu*.tex"))):
        for k in re.findall(r"\\newcommand\{\\(\w+)\}", io.open(f, encoding="utf-8").read()):
            dem.setdefault(k, []).append(os.path.basename(f))
    hai_cho = ["%s (%s)" % (k, ", ".join(v)) for k, v in sorted(dem.items()) if len(v) > 1]
    kiem(not hai_cho, "B15 khong macro nao co hai CHO O", "; ".join(hai_cho[:4]))

    chua = sorted(dn - xai - khai)
    kiem(not chua, "B15 macro khong dung deu da duoc khai",
         "%d chua khai: %s" % (len(chua), ", ".join(chua[:6])))

    # ---- B16: muc o LE trang. Cong LaTeX bao 0 Overfull van co the de hinh thoc ra le;
    # chi do tren ANH RENDER moi thay. Chi do le TRAI/PHAI/TREN: so trang nam o le DUOI.
    import tempfile
    dpi, le_cm, margin_cm = 100, 1.2, 2.5
    tm = tempfile.mkdtemp()
    subprocess.run(["pdftoppm", "-r", str(dpi), "-png", os.path.join(P, "main.pdf"),
                    os.path.join(tm, "t")], capture_output=True)
    anh = sorted(glob.glob(os.path.join(tm, "*.png")))
    bien = int(le_cm / 2.54 * dpi)
    try:
        from PIL import Image
        xau = []
        for a in anh:
            im = Image.open(a).convert("L")
            w, h = im.size
            for ten_vung, hop in (("trai", (0, 0, bien, h)), ("phai", (w - bien, 0, w, h)),
                                  ("tren", (0, 0, w, bien))):
                if im.crop(hop).getextrema()[0] < 128:
                    xau.append("%s:%s" % (os.path.basename(a)[-7:-4], ten_vung))
        kiem(not xau, "B16 khong co muc o le trai/phai/tren cua trang in",
             ", ".join(xau[:6]))
    except ImportError:
        kiem(False, "B16 can Pillow de do tren anh render")

    # ---- B17: tinh LAI dai so cua cac menh de tu macro NGUON, so voi macro DA IN.
    mac = {}
    for f in glob.glob(os.path.join(GOC, "results", "so-lieu*.tex")):
        for k, v in re.findall(r"\\newcommand\{\\(\w+)\}\{([^}]*)\}",
                               io.open(f, encoding="utf-8").read()):
            mac[k] = v
    def fs(k):
        return float(mac[k])
    try:
        u, b_ = fs("probU"), fs("probB")
        kiem(abs(0.5 * (1 + u - b_) - fs("aucDuBao")) < 5e-4,
             "B17 AUC = (1+u-b)/2 khop macro", "%.4f vs %s" % (0.5 * (1 + u - b_), mac["aucDuBao"]))
        kiem(abs(u / b_ - fs("lrLambda")) < 5e-4, "B17 Lambda = u/b khop macro",
             "%.4f vs %s" % (u / b_, mac["lrLambda"]))
        kiem(abs(100 * (1 - fs("digitP")) - fs("tranCao")) < 5e-2,
             "B17 tran 1-p khop macro", "%.2f vs %s" % (100 * (1 - fs("digitP")), mac["tranCao"]))
        for t in ("bnSoA", "bnSoB", "bnNgayA", "bnNgayB", "bnCoQuanA", "bnCoQuanB"):
            tong = int(mac[t + "Dung"]) + int(mac[t + "Sai"]) + int(mac[t + "Im"])
            kiem(tong == int(mac[t + "N"]), "B17 %s: ba nhanh cong lai dung n" % t,
                 "%d vs %s" % (tong, mac[t + "N"]))
        dR = int(mac["bnSoBDung"]) / fs("bnSoBN") - int(mac["bnSoADung"]) / fs("bnSoAN")
        dE = int(mac["bnSoBSai"]) / fs("bnSoBN") - int(mac["bnSoASai"]) / fs("bnSoAN")
        kiem(abs(dR / dE - fs("bnSoHoaVon")) < 5e-4, "B17 hoa von = dRec/dEps khop macro",
             "%.4f vs %s" % (dR / dE, mac["bnSoHoaVon"]))
    except KeyError as e:
        kiem(False, "B17 thieu macro de tinh lai", str(e))

    # ---- B18: bo style cua nha. Lan 27/08 va lan 08/10 toi deu tu che quy uoc ve hinh
    # trong khi `paper-lab/transaction-figure-kit/` da co san. Nay la cong, khong la tri nho.
    src_fig = glob.glob(os.path.join(GOC, "figures", "src", "*.tex"))
    thieu = [os.path.basename(f) for f in src_fig
             if os.path.basename(f) != "txstyle.tex"
             and "f9-header" not in f
             and "\\input{txstyle.tex}" not in io.open(f, encoding="utf-8").read()]
    kiem(not thieu, "B18 moi hinh TikZ deu nap txstyle.tex cua nha", ", ".join(thieu))
    kiem(os.path.exists(os.path.join(GOC, "figures", "src", "txstyle.tex")),
         "B18 co ban txstyle.tex trong thu muc bai")
    ve = [os.path.join(GOC, "code", x) for x in
          ("e6_e7_nguong.py", "e8_bo_do.py", "e9_quet_dpi.py", "e11_e12_phan_tang.py",
           "f6_hinh_truong.py", "f12_f16_hinh_luong.py")]
    tu_che = []
    for f in ve:
        if not os.path.exists(f):
            continue
        t = io.open(f, encoding="utf-8").read()
        hex_ = set(re.findall(r'"#[0-9a-fA-F]{6}"', t))
        if hex_:
            tu_che.append("%s: %s" % (os.path.basename(f), ", ".join(sorted(hex_))))
        if "import txstyle" not in t:
            tu_che.append("%s: khong nap txstyle.py" % os.path.basename(f))
    kiem(not tu_che, "B18 bo sinh hinh khong tu dat mau rieng", "; ".join(tu_che))

    # ---- B19a: khong trang nao chi co hinh/bang. Hao bat 08/10: dat float la [tbp] thi
    # LaTeX dung TRANG FLOAT THUAN. Dem TONG so tu moi trang, KHONG cat caption: ban dau toi
    # cat caption roi dem, bo do ay cat nham ca than bai va bao trang 2 chi co 30 tu trong
    # khi no day chu. Dem tho thi khong the cat nham.
    thua = []
    for i in range(1, n_tr):          # bo trang CUOI: do la duoi danh muc tham khao
        tt = subprocess.run(["pdftotext", "-f", str(i), "-l", str(i),
                             os.path.join(P, "main.pdf"), "-"],
                            capture_output=True, text=True).stdout
        if len(tt.split()) < 150:
            thua.append("tr%d (%d tu)" % (i, len(tt.split())))
    kiem(not thua, "B19 khong trang nao chi co hinh/bang", ", ".join(thua))

    # ---- B19b: chu TRONG hinh phai >= 6pt sau khi thu phong. Luat cua
    # paper-lab/transaction-figure-kit: do kho TU NHIEN bang pdfinfo roi tinh
    # co_chu_goc * be_rong_dich / be_rong_tu_nhien. Duoi ~6pt la hong.
    LINE = 453.5     # \linewidth do duoc: A4 21cm tru hai le 2,5cm
    rong = dict((b_, float(a_)) for a_, b_ in re.findall(
        r"includegraphics\[width=([\d.]+)\\linewidth\]\{\.\./figures/([^}]+)\}", src))
    rong.update(dict((b_, 1.0) for b_ in re.findall(
        r"includegraphics\[width=\\linewidth\]\{\.\./figures/([^}]+)\}", src)))
    nho = []
    for ten, frac in sorted(rong.items()):
        ra = subprocess.run(["pdfinfo", os.path.join(GOC, "figures", ten)],
                            capture_output=True, text=True).stdout
        m = re.search(r"Page size:\s+([\d.]+) x ([\d.]+)", ra)
        if not m:
            continue
        tu_nhien = float(m.group(1))
        goc = 8.0 if re.match(r"f(10|11|12|13|15|16)-", ten) else 9.0   # TikZ vs matplotlib
        pt = goc * frac * LINE / tu_nhien
        if pt < 6.0:
            nho.append("%s %.1fpt" % (ten, pt))
    kiem(not nho, "B19 chu trong hinh >= 6pt sau khi thu phong", ", ".join(nho))

    print("\n=> %s (%d loi)" % ("DAT, san sang gui doc ngoai" if not loi else "CHUA DAT", len(loi)))
    for x in loi:
        print("   loi: " + x)
    return 0 if not loi else 1


if __name__ == "__main__":
    sys.exit(main())
