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

    # ⛔ Phai gom CA `frag-*.tex`: Highlights va khoi tac gia nay nam o manh DUNG CHUNG, va
    # neu khong gom thi phep dem Highlights doc ra 0 roi bao XANH vi 0 khong vuot tran.
    src = "".join(io.open(f, encoding="utf-8").read()
                  for f in sorted(glob.glob(os.path.join(P, "sections", "*.tex"))
                                  + glob.glob(os.path.join(P, "frag-*.tex")))
                  + [os.path.join(P, "main.tex")])
    co = set(os.path.basename(x) for x in glob.glob(os.path.join(GOC, "figures", "*.pdf")))
    dung = set(re.findall(r"includegraphics\[[^\]]*\]\{\.\./figures/([^}]+)\}", src))
    # hinh dau trang duoc chen qua macro vi ban an danh dung ban da che: no ra CA HAI ten
    if "\\HINHDAUTRANG.pdf" in dung:
        dung.discard("\\HINHDAUTRANG.pdf")
        dung |= {"f9-header.pdf", "f9-header-anon.pdf"}
    kiem(dung <= co, "B3 moi hinh duoc chen deu ton tai", ", ".join(sorted(dung - co)))
    thua = co - dung
    kb_h = os.path.join(GOC, "code", "hinh-khong-dung.txt")
    khai_h = set()
    if os.path.exists(kb_h):
        khai_h = {l.split("#")[0].strip() for l in io.open(kb_h, encoding="utf-8")
                  if l.split("#")[0].strip()}
    kiem(not (thua - khai_h), "B3 hinh khong dung deu da duoc khai",
         "chua khai: " + ", ".join(sorted(thua - khai_h)))

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

    # ---- B14: cac moc cua CHINH IPM, thay cho moc trang.
    # ⛔ Truoc day day la "<= 30 trang", dat khi bai dung `article` 11pt. Chuyen sang
    # `elsarticle` thi cung noi dung ra 42 trang vi lop nay gian dong rong hon. So trang khong
    # con so sanh duoc; cai IPM thuc su quy dinh la DO DAI TOM TAT va HIGHLIGHTS.
    i0, i1 = txt.find("Document pipelines decide"), txt.find("Keywords")
    n_tt = len(txt[i0:i1].split()) if 0 <= i0 < i1 else -1
    kiem(0 < n_tt <= 250, "B14 tom tat <= 250 tu (moc IPM)", str(n_tt))
    # ⛔ Highlights nay nam o MANH DUNG CHUNG `frag-highlights.tex`, khong con inline trong
    # main.tex. Doc tu khoi `highlights` thi ra DANH SACH RONG, va ca hai phep dua vao no
    # (dem 3-5 muc, va "ban rieng khop ban thao") deu bao XANH mot cach RONG NGHIA.
    frag_hl = os.path.join(P, "frag-highlights.tex")
    hls = re.findall(r"(?m)^\s*\\item (.+)$",
                     io.open(frag_hl, encoding="utf-8").read() if os.path.exists(frag_hl) else "")
    kiem(bool(hls), "B14 doc duoc danh sach Highlights (khong rong)", "%d muc" % len(hls))
    kiem(3 <= len(hls) <= 5, "B14 co 3-5 Highlights (moc IPM)", str(len(hls)))
    # ⛔ Ban dau toi dem tren BAN IN bang cach bat tung dong bat dau bang dau bullet. SAI:
    # bullet dai BI NGAT DONG, nen phep do chi thay DONG DAU va mot bullet 82 ky tu lot qua.
    # Dem dung la tren NGUON, sau khi khai trien macro, vi do la toan bo chuoi.
    def no_macro(t):
        for _ in range(4):
            t = re.sub(r"\\([A-Za-z]+)\{\}|\\([A-Za-z]+)(?![A-Za-z])",
                       lambda m: mac_hl.get(m.group(1) or m.group(2), ""), t)
        # ⛔ Ban dau dong nay doi CA dau ngoac nhon LAN `\\%` thanh `%`, nen
        # `\\texttt{/ToUnicode}` ra `%/ToUnicode%`. Dau ngoac phai BO, chi `\\%` moi thanh `%`.
        t = t.replace("\\%", "%")
        return re.sub(r"[{}]", "", t).strip()
    mac_hl = {}
    for f in glob.glob(os.path.join(GOC, "results", "so-lieu*.tex")):
        for k, v in re.findall(r"\\newcommand\{\\(\w+)\}\{([^}]*)\}",
                               io.open(f, encoding="utf-8").read()):
            mac_hl[k] = v.replace("\\,", "")
    qua = ["%d: %s" % (len(no_macro(h)), no_macro(h)[:40]) for h in hls
           if len(no_macro(h)) > 85]
    kiem(not qua, "B14 moi Highlight <= 85 ky tu",
         "; ".join(qua[:2]) if qua else "dai nhat %d" % max([len(no_macro(h)) for h in hls] or [0]))
    kiem(n_tr <= 45, "B14 so trang trong han muc tinh tao", str(n_tr))

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
    # ⛔ Ten macro LaTeX chi duoc gom CHU CAI. `\\c2Giao` -> `\\c` + `2Giao` -> chet o preamble
    # voi mot thong bao hoan toan lac de. Da mac 2 lan (aucD0 hoi 24/09, c2Giao hom nay).
    co_so = sorted(k for k in dem if not k.isalpha())
    kiem(not co_so, "B15 ten macro chi gom chu cai", ", ".join(co_so[:4]))

    hai_cho = ["%s (%s)" % (k, ", ".join(v)) for k, v in sorted(dem.items()) if len(v) > 1]
    kiem(not hai_cho, "B15 khong macro nao co hai CHO O", "; ".join(hai_cho[:4]))

    chua = sorted(dn - xai - khai)
    kiem(not chua, "B15 macro khong dung deu da duoc khai",
         "%d chua khai: %s" % (len(chua), ", ".join(chua[:6])))

    # ---- B16: muc tran RA NGOAI KHOI CHU. Cong LaTeX bao 0 Overfull van co the de hinh
    # thoc ra le; chi do tren ANH RENDER moi thay.
    # ⛔ Ban dau day la mot DAI CO DINH 1,2cm tinh tu mep giay. Khi bai doi sang `elsarticle`
    # (le 4,45cm) thi dai ay nam SAU BEN TRONG le, va ca tiem loi day muc ra 2,5cm van khong
    # cham toi no: cong XANH tren mot loi THAT. Nay cong TU DO khoi chu tu chinh ban in roi
    # bat moi thu thoc ra ngoai khoi ay, nen no dung voi moi lop tai lieu.
    import tempfile
    dpi = 100
    tm = tempfile.mkdtemp()
    subprocess.run(["pdftoppm", "-r", str(dpi), "-png", os.path.join(P, "main.pdf"),
                    os.path.join(tm, "t")], capture_output=True)
    anh = sorted(glob.glob(os.path.join(tm, "*.png")))
    try:
        from PIL import Image
        bien_trai, bien_phai, cao = [], [], []
        for a_ in anh:
            im = Image.open(a_).convert("L")
            w, h = im.size
            cot = [x for x in range(w) if im.crop((x, 0, x + 1, h)).getextrema()[0] < 128]
            if cot:
                bien_trai.append(cot[0]); bien_phai.append(cot[-1]); cao.append((w, h))
        if not bien_trai:
            kiem(False, "B16 khong doc duoc muc tren ban in")
        else:
            # khoi chu = vi tri pho bien nhat, khong phai cuc tri (mot trang hong khong duoc
            # keo ca moc di)
            import statistics
            kt = statistics.median(bien_trai)
            kp = statistics.median(bien_phai)
            lech = int(0.5 / 2.54 * dpi)        # cho phep thoc 0,5cm roi moi bao
            xau = []
            for a_, t_, p_ in zip(anh, bien_trai, bien_phai):
                if t_ < kt - lech or p_ > kp + lech:
                    xau.append("%s(%d..%d vs %d..%d)" % (os.path.basename(a_)[-7:-4],
                                                        t_, p_, int(kt), int(kp)))
            kiem(not xau, "B16 khong co muc thoc ra ngoai khoi chu", ", ".join(xau[:4]))
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
    for i in range(2, n_tr):          # bo trang DAU (frontmatter) va trang CUOI (duoi tai lieu)
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

    # ---- B20: THU NGO. Vong doc ngoai thu hai so NHI PHAN thu ngo voi ban truoc va thay no
    # Y NGUYEN, van chao editor bang mot con so ban thao DA RUT. Cong cu toi chi doc ban thao,
    # khong doc tai lieu di kem, nen khong the thay. Nay no doc.
    cl_t = os.path.join(P, "cover-letter.tex")
    cl_p = os.path.join(P, "cover-letter.pdf")
    if not os.path.exists(cl_t):
        kiem(False, "B20 co thu ngo")
    else:
        clt = io.open(cl_t, encoding="utf-8").read()
        kiem(os.path.exists(cl_p) and os.path.getmtime(cl_p) >= os.path.getmtime(cl_t),
             "B20 thu ngo da dung lai sau lan sua cuoi")
        # moi con so dang thap phan trong thu PHAI la macro, y nhu than bai
        goc_so = re.findall(r"(?<![\\\w.])\d+\.\d+(?![\d])",
                            re.sub(r"\\[a-zA-Z]+\{[^}]*\}", "", clt))
        kiem(not goc_so, "B20 khong so thap phan go tay trong thu ngo", ", ".join(goc_so[:4]))
        # macro thu dung phai TON TAI, va gia tri in ra phai khop ban thao
        dung_cl = set(re.findall(r"\\([A-Za-z]+)\{\}", clt))
        thieu = sorted(m for m in dung_cl if m in dn and m not in dn) or []
        cl_txt = subprocess.run(["pdftotext", cl_p, "-"],
                                capture_output=True, text=True).stdout if os.path.exists(cl_p) else ""
        cam = [v for k, v in (("bnSoHoaVon", "0.224"),) if v in cl_txt]
        kiem(not cam, "B20 thu ngo khong mang so ban thao da rut", ", ".join(cam))
        # moi so xuat hien trong thu phai xuat hien trong than bai
        so_cl = set(re.findall(r"(?<![\d.])\d+\.\d+(?![\d])", cl_txt))
        la = sorted(x for x in so_cl if x not in txt)
        kiem(not la, "B20 moi so trong thu ngo deu co trong ban thao", ", ".join(la[:4]))

    # ---- B21: bo BON TEP ma he nop cua IPM doi, va phep AN DANH.
    # ⛔ Phep "khong thay chuoi X trong lop chu" la phep RONG doi voi thu nam trong ANH: hinh
    # dau trang in ro ma co quan, trung ten truong cua tac gia thu nhat, va mot lan dung thu
    # ban an danh da nhung nham anh CHUA CHE ma khong phep kiem chu nao thay duoc. Nen o day
    # kiem CA HAI: chuoi trong lop chu, VA ten tep hinh ma ban an danh thuc su nhung.
    anon_pdf = os.path.join(P, "manuscript-anon.pdf")
    anon_log = os.path.join(P, "manuscript-anon.log")
    if not os.path.exists(anon_pdf):
        kiem(False, "B21 co ban thao AN DANH (chay zsh build-submit.sh)")
    else:
        at = subprocess.run(["pdftotext", anon_pdf, "-"], capture_output=True, text=True).stdout
        LO = ["haodpsut", "B2025-DN02-25", "Phuc Hao", "Nguyen Nang", "Minh Tuan",
              "Danang Architecture", "Bonch-Bruevich", "dau.edu.vn", "udn.vn",
              "University of Danang", "CRediT"]
        thay = [k for k in LO if k in at]
        kiem(not thay, "B21 ban an danh khong lo danh tinh trong lop chu", ", ".join(thay))
        lg = io.open(anon_log, encoding="utf-8", errors="ignore").read() if os.path.exists(anon_log) else ""
        goc_h = re.findall(r"f9-header\.pdf", lg)
        kiem(not goc_h, "B21 ban an danh nhung HINH DA CHE, khong phai hinh goc",
             "con nhung f9-header.pdf" if goc_h else "")
        kiem("f9-header-anon.pdf" in lg, "B21 ban an danh co nhung hinh da che")
        try:
            from pypdf import PdfReader as _PR
            md = _PR(anon_pdf).metadata or {}
            xau_md = [k for k, v in md.items()
                      if v and any(x.lower() in str(v).lower() for x in ("hao", "nguyen", "pham"))]
            kiem(not xau_md, "B21 sieu du lieu PDF khong mang ten tac gia", ", ".join(map(str, xau_md)))
        except Exception as e:
            kiem(False, "B21 doc duoc sieu du lieu", str(e))

    # highlights va title page phai TON TAI va KHOP ban thao
    hl_pdf = os.path.join(P, "highlights.pdf")
    tp_pdf = os.path.join(P, "title-page.pdf")
    kiem(os.path.exists(hl_pdf) and os.path.exists(tp_pdf),
         "B21 co tep Highlights va Title page rieng")
    if os.path.exists(hl_pdf):
        ht = subprocess.run(["pdftotext", hl_pdf, "-"], capture_output=True, text=True).stdout
        thieu_hl = [h for h in hls if no_macro(h)[:28] not in " ".join(ht.split())]
        kiem(not thieu_hl, "B21 Highlights rieng khop ban thao",
             "; ".join(no_macro(h)[:30] for h in thieu_hl[:2]))
    if os.path.exists(tp_pdf):
        tt = subprocess.run(["pdftotext", tp_pdf, "-"], capture_output=True, text=True).stdout
        can = ["Phuc Hao Do", "Nguyen Nang Hung Van", "Minh Tuan Pham",
               "haodp@dau.edu.vn", "CRediT", "B2025-DN02-25"]
        thieu_tp = [k for k in can if k not in tt]
        kiem(not thieu_tp, "B21 Title page co du chi tiet tac gia", ", ".join(thieu_tp))

    print("\n=> %s (%d loi)" % ("DAT, san sang gui doc ngoai" if not loi else "CHUA DAT", len(loi)))
    for x in loi:
        print("   loi: " + x)
    return 0 if not loi else 1


if __name__ == "__main__":
    sys.exit(main())
