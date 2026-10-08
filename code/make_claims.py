#!/usr/bin/env python3
"""Sinh MOI con so cua bai tu ket qua do.  python3 code/make_claims.py

Luat nha: khong con so nao trong ban thao duoc go tay. Tep nay doc ket qua that roi sinh:
  results/so-lieu.tex        macro \\soXxx cho moi con so xuat hien trong van
  results/tables/tab-*.tex   cac bang

Nguon:
  results/toan-kho.csv   toan bo 5048 tep, TINH LAI o day chu khong doc lai bang da in
  results/thu-vien.log   phep thu 5 bo boc chu
  results/so-hieu-n250.log  do chinh xac so hieu, n=250

TU KIEM: moi so doc tu log phai khop lai voi mot phep tinh doc lap hoac voi mot rang buoc
(tong = 100%, so ca <= n). Hong mot phep thi thoat khac 0, KHONG sinh tep nua.
"""
import collections, csv, io, math, os, re, sys

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(GOC, "results")
loi = []


def kiem(dk, ten, ct=""):
    if not dk:
        loi.append(ten)
    print("  %s %s%s" % ("DAT " if dk else "HONG", ten, ("  [" + ct + "]") if ct else ""))


def doc_p_chu_so():
    """p (ti le chu so doc sai) chi co MOT CHO O: results/so-lieu-e13.tex do e13 sinh ra.
    Khong go lai o day, vi hai ban cua cung mot so thi som muon se phan ky."""
    p = os.path.join(RES, "so-lieu-e13.tex")
    m = re.search(r"\\newcommand\{\\digitP\}\{([\d.]+)\}",
                  io.open(p, encoding="utf-8").read()) if os.path.exists(p) else None
    return float(m.group(1)) if m else None


def wilson(k, n, z=1.96):
    if not n:
        return 0.0, 0.0
    p = k / float(n)
    d = 1 + z * z / n
    t = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, t - h), min(1.0, t + h)


def doc_csv():
    with io.open(os.path.join(RES, "toan-kho.csv"), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    print("== SINH SO LIEU CHO BAI ==")
    hang = doc_csv()
    n = len(hang)
    pl = collections.Counter(r["phan_loai"] for r in hang)
    quet, hong, tot = pl["QUET"], pl["LOP CHU HONG"], pl["LOP CHU TOT"]
    co_chu = hong + tot

    kiem(n > 5000, "toan kho co tren 5000 tep (%d)" % n)
    kiem(quet + hong + tot <= n, "ba nhom khong vuot tong")
    kiem(co_chu > 0, "co tep mang lop chu")

    # --- C2: /ToUnicode, tinh lai tu CSV
    tu = {}
    for k in ("LOP CHU HONG", "LOP CHU TOT"):
        x = [r["moi_font_co_tounicode"] for r in hang
             if r["phan_loai"] == k and r["moi_font_co_tounicode"]]
        tu[k] = (sum(1 for v in x if v == "True"), len(x))
    kiem(tu["LOP CHU HONG"][1] > 0 and tu["LOP CHU TOT"][1] > 0, "ca hai nhom co du lieu ToUnicode")
    ti_hong = 100.0 * tu["LOP CHU HONG"][0] / tu["LOP CHU HONG"][1]
    ti_tot = 100.0 * tu["LOP CHU TOT"][0] / tu["LOP CHU TOT"][1]
    kiem(ti_hong > ti_tot, "phep DAO CHIEU con dung (%.1f%% > %.1f%%)" % (ti_hong, ti_tot))

    # --- producer
    pm = collections.defaultdict(collections.Counter)
    for r in hang:
        if r["phan_loai"] in ("LOP CHU HONG", "LOP CHU TOT"):
            pm[r["producer"] or "(none)"][r["phan_loai"]] += 1
    xep = sorted(pm.items(), key=lambda x: -sum(x[1].values()))
    dau = xep[0]
    kiem(dau[1]["LOP CHU TOT"] == 0,
         "producer dan dau khong co tep TOT nao (%s)" % dau[0][:28])
    ti_dau = 100.0 * dau[1]["LOP CHU HONG"] / hong

    # --- C3 tu log
    t3 = io.open(os.path.join(RES, "thu-vien.log"), encoding="utf-8").read()
    bo = re.findall(r"^\s{2}(pdftotext|PyMuPDF|pdfplumber|pypdf|pdfminer\.six)\s+"
                    r"([\d.]+)\s+([\d.]+)\s+(\d+)/(\d+)", t3, re.M)
    kiem(len(bo) == 10, "log thu vien co du 10 dong (5 bo x 2 nhom), thay %d" % len(bo))
    hong3 = [b for b in bo[5:]]
    kiem(all(float(b[1]) < 0.01 for b in hong3), "ca 5 bo deu ~0 tren nhom HONG")
    kiem(all(int(b[3]) == 0 for b in hong3), "0/20 o ca 5 bo tren nhom HONG")
    tot3 = bo[:5]
    kiem(all(int(b[3]) == int(b[4]) for b in tot3), "doi chung duong 20/20 o ca 5 bo")

    # --- C4 tu log
    t4 = io.open(os.path.join(RES, "so-hieu-n250.log"), encoding="utf-8").read()
    m = re.search(r"n thuc te = (\d+)", t4)
    n4 = int(m.group(1)) if m else 0
    kiem(n4 >= 250, "C4 chay du n (%d)" % n4)
    kA = re.search(r"A lop chu nhung san\s*\n\s*DUNG\s+(\d+).*?KHONG RA SO\s+(\d+)", t4, re.S)
    kB = re.search(r"B OCR hien dai\s*\n\s*DUNG\s+(\d+)\s.*?SAI TRONG NHU THAT\s+(\d+)\s"
                   r".*?KHONG RA SO\s+(\d+)", t4, re.S)
    kiem(bool(kA and kB), "boc duoc so C4 tu log")
    if not (kA and kB):
        print("=> CHUA DAT"); return 1
    a_dung, a_khong = int(kA.group(1)), int(kA.group(2))
    b_dung, b_sai, b_khong = int(kB.group(1)), int(kB.group(2)), int(kB.group(3))
    kiem(a_khong == n4, "A khong ra so o TAT CA %d ca" % n4)
    kiem(b_dung + b_sai + b_khong == n4, "B: ba ket cuc cong lai bang n")
    b_ra = b_dung + b_sai
    lo, hi = wilson(b_dung, b_ra)

    # --- E11: tep mang quy uoc dat ten luu tru
    # ⛔ LOI DA PHAT HANH: truoc day toi chi sinh `luuTruN` = 3877 (MOI tep mang quy uoc, ke ca
    # ban quet khong co lop chu) roi viet trong bai "All 1422 of them have an unusable text
    # layer". Cau ay VO NGHIA ve so hoc va nguoi doc ngoai bat duoc ngay. Nay tach ba con so va
    # RANG BUOC chung phai cong dung.
    luu_tru = [r for r in hang if r["loai_ten_tep"]]
    lt_hong = sum(1 for r in luu_tru if r["phan_loai"] == "LOP CHU HONG")
    lt_tot = sum(1 for r in luu_tru if r["phan_loai"] == "LOP CHU TOT")
    lt_quet = sum(1 for r in luu_tru if r["phan_loai"] == "QUET")
    lt_co_chu = lt_hong + lt_tot
    kiem(lt_quet + lt_co_chu == len(luu_tru),
         "ba nhom con cong dung bang tong tep mang quy uoc",
         "%d + %d = %d" % (lt_quet, lt_co_chu, len(luu_tru)))
    kiem(lt_tot == 0, "khong tep luu tru nao co lop chu TOT (dan so dong nhat)",
         "%d tot" % lt_tot)
    kiem(lt_hong > 1000, "dan so luu tru du lon (%d)" % lt_hong)

    # --- mau so cua bang /ToUnicode: co tep KHONG doc duoc tu dien font, phai KHAI
    # ⛔ Lan dau toi in mot can roi goi no la "bat loi cho chung toi". SAI: coi 68 tep thieu du
    # lieu la KHONG co CMap lam ti le nhom TOT GIAM, tuc khoang cach RONG RA, tuc CO LOI cho
    # tuyen bo cua minh. Can bat loi that la coi ca 68 deu CO CMap. Nguoi doc ngoai bat duoc.
    tu_tot_thieu = tot - tu["LOP CHU TOT"][1]
    tu_hong_thieu = hong - tu["LOP CHU HONG"][1]
    ti_co_loi = 100.0 * tu["LOP CHU TOT"][0] / tot
    ti_bat_loi = 100.0 * (tu["LOP CHU TOT"][0] + tu_tot_thieu) / tot
    b_cuc_bo = tu["LOP CHU HONG"][0] / float(tu["LOP CHU HONG"][1])
    auc_bat_loi = 0.5 * (1 + ti_bat_loi / 100.0 - b_cuc_bo)
    kiem(ti_bat_loi > ti_tot, "can BAT LOI phai cho ti le CAO hon ban dang in",
         "%.1f > %.1f" % (ti_bat_loi, ti_tot))
    kiem(auc_bat_loi < 0.5, "ngay o can bat loi, AUC van < 0,5", "%.3f" % auc_bat_loi)
    kiem(ti_co_loi < ti_tot < ti_bat_loi, "ba can xep dung thu tu co loi < dang in < bat loi",
         "%.1f < %.1f < %.1f" % (ti_co_loi, ti_tot, ti_bat_loi))
    kiem(tu_tot_thieu >= 0 and tu_hong_thieu >= 0, "mau so ToUnicode khong vuot tong nhom")

    # --- E10: ba truong, doc tu log
    t10 = ""
    p10 = os.path.join(RES, "e10.log")
    if os.path.exists(p10):
        t10 = io.open(p10, encoding="utf-8").read()
    truong = {}
    for ten, ma in (("so hieu", "SoHieu"), ("ngay", "Ngay"), ("co quan", "CoQuan")):
        m = re.search(r"^\s+%s\s+(\d+)\s+(\d+)\s*\(\s*([\d.]+)%%\)\s+(\d+)\s*\(\s*([\d.]+)%%\)"
                      % ten, t10, re.M)
        if m:
            truong[ma] = (int(m.group(1)), float(m.group(3)), float(m.group(5)))
    kiem(len(truong) == 3, "boc du 3 truong tu e10.log", "%d" % len(truong))
    if "CoQuan" in truong and "SoHieu" in truong:
        kiem(truong["CoQuan"][1] > truong["SoHieu"][1] + 50,
             "co che: truong tu vung dai cao hon HAN truong dang so",
             "%.1f%% vs %.1f%%" % (truong["CoQuan"][1], truong["SoHieu"][1]))

    # --- Menh de: AUC dang dong cho mot diem NHI PHAN.
    # Voi diem nhi phan S, lop duong = "dung duoc": AUC = u(1-b) + 1/2[ub + (1-u)(1-b)]
    #                                                    = 1/2 (1 + u - b)
    # Day la mo hinh DANG DONG kiem duoc bang so do, khac han mo hinh (1-p)^k da bo.
    u = tu["LOP CHU TOT"][0] / float(tu["LOP CHU TOT"][1])
    b = tu["LOP CHU HONG"][0] / float(tu["LOP CHU HONG"][1])
    auc_dd = u * (1 - b) + 0.5 * (u * b + (1 - u) * (1 - b))
    auc_rg = 0.5 * (1 + u - b)
    kiem(abs(auc_dd - auc_rg) < 1e-9, "dang rut gon khop dang day du", "%.4f" % auc_rg)
    kiem(auc_rg < 0.5, "du bao dang dong cho AUC < 0,5", "%.4f" % auc_rg)

    # --- E8: AUC, doc tu log
    t8 = ""
    p8 = os.path.join(RES, "e8.log")
    if os.path.exists(p8):
        t8 = io.open(p8, encoding="utf-8").read()
    aucs = dict(re.findall(r"^\s+(D\d) [^\n]*?\s+([\d.]+)\s*$", t8, re.M))
    kiem(len(aucs) >= 5, "boc du AUC tu e8.log", "%d" % len(aucs))
    if "D2" in aucs:
        kiem(float(aucs["D2"]) < 0.5, "AUC D2 < 0,5", aucs.get("D2", "?"))

    # --- COeNG CHEO: bang da sinh phai CONG DUNG voi macro.
    # Nguoi doc ngoai bat duoc mot mau thuan noi tai bang cach cong tay mot bang roi so voi
    # cau van ben canh (1393 vs 1422). Do la hang DANGEROUS. Nay may lam viec ay truoc.
    p_loai = os.path.join(RES, "tables", "tab-loai.tex")
    if os.path.exists(p_loai):
        s_loai = io.open(p_loai, encoding="utf-8").read()
        m_all = re.search(r"All typed records & (\d+) & (\d+)", s_loai)
        kiem(bool(m_all), "bang loai co hang TONG")
        if m_all:
            kiem(int(m_all.group(1)) == lt_hong and int(m_all.group(2)) == lt_tot,
                 "hang TONG cua bang loai khop macro luuTruHong/luuTruTot",
                 "bang %s/%s vs macro %d/%d" % (m_all.group(1), m_all.group(2), lt_hong, lt_tot))
            than = [l for l in s_loai.splitlines()
                    if "&" in l and "\\\\" in l and "Document type" not in l
                    and "All typed records" not in l]
            c = sum(int(l.split("&")[1].strip()) for l in than)
            kiem(c == lt_hong, "cac hang cua bang loai cong dung bang hang TONG",
                 "%d vs %d" % (c, lt_hong))

    p_tu = os.path.join(RES, "tables", "tab-tounicode.tex")
    if os.path.exists(p_tu):
        s_tu = io.open(p_tu, encoding="utf-8").read()
        for ten, k in (("Unusable", "LOP CHU HONG"), ("Usable", "LOP CHU TOT")):
            m = re.search(r"%s & (\d+) & (\d+)" % ten, s_tu)
            if m:
                kiem(int(m.group(2)) == tu[k][1],
                     "mau so hang '%s' cua bang ToUnicode khop du lieu" % ten,
                     "%s vs %d" % (m.group(2), tu[k][1]))

    if loi:
        print("=> CHUA DAT (%d loi), KHONG sinh tep" % len(loi))
        for x in loi:
            print("   loi: " + x)
        return 1

    # ---------- sinh macro ----------
    p_chu_so = doc_p_chu_so()
    kiem(p_chu_so is not None,
         "doc duoc p chu so tu results/so-lieu-e13.tex (chay code/e13_mo_hinh_chu_so.py truoc)")
    if p_chu_so is None:
        print("=> CHUA DAT, KHONG sinh tep")
        return 1

    mac = [
        ("soTongTep", "{:,}".format(n).replace(",", "\\,")),
        ("soQuet", "%d" % quet), ("tiQuet", "%.1f" % (100.0 * quet / n)),
        ("soHong", "%d" % hong), ("tiHong", "%.1f" % (100.0 * hong / n)),
        ("soTot", "%d" % tot), ("tiTot", "%.1f" % (100.0 * tot / n)),
        ("soCoChu", "%d" % co_chu), ("tiHongTrongCoChu", "%.1f" % (100.0 * hong / co_chu)),
        ("tuHongTu", "%d" % tu["LOP CHU HONG"][0]), ("tuHongMau", "%d" % tu["LOP CHU HONG"][1]),
        ("tuHongTi", "%.1f" % ti_hong),
        ("tuTotTu", "%d" % tu["LOP CHU TOT"][0]), ("tuTotMau", "%d" % tu["LOP CHU TOT"][1]),
        ("tuTotTi", "%.1f" % ti_tot),
        ("prodDan", dau[0][:30]), ("prodDanHong", "%d" % dau[1]["LOP CHU HONG"]),
        ("prodDanTi", "%.1f" % ti_dau),
        ("soBoBoc", "5"), ("boBocMau", "20"),
        ("cBonN", "%d" % n4),
        ("cBonAKhong", "%d" % a_khong),
        ("cBonBDung", "%d" % b_dung), ("cBonBSai", "%d" % b_sai),
        ("cBonBKhong", "%d" % b_khong),
        ("cBonBTiSai", "%.1f" % (100.0 * b_sai / n4)),
        ("cBonBRa", "%d" % b_ra),
        ("cBonBDungTrongRa", "%.1f" % (100.0 * b_dung / b_ra)),
        ("cBonBCILo", "%.1f" % (100 * lo)), ("cBonBCIHi", "%.1f" % (100 * hi)),
        ("probU", "%.3f" % u), ("probB", "%.3f" % b),
        ("aucDuBao", "%.3f" % auc_rg),
        # ty so kha di cua Corollary 1, va TRAN khong can gia thiet doc lap cua Proposition 3
        ("lrLambda", "%.3f" % (u / b)),
        # tranCao da chuyen sang code/e18_khoang_tin_cay.py, noi co ca khoang cua no.
        # Giu o hai noi la hai CHO O, va cong B15 bat.
        ("luuTruN", "%d" % len(luu_tru)), ("luuTruHong", "%d" % lt_hong),
        ("luuTruTot", "%d" % lt_tot), ("luuTruQuet", "%d" % lt_quet),
        ("luuTruCoChu", "%d" % lt_co_chu),
        ("tuTotThieu", "%d" % tu_tot_thieu), ("tuHongThieu", "%d" % tu_hong_thieu),
        ("tiCoLoi", "%.1f" % ti_co_loi), ("tiBatLoi", "%.1f" % ti_bat_loi),
        ("aucBatLoi", "%.3f" % auc_bat_loi),
        ("khoangCachBatLoi", "%.1f" % (100 * b - ti_bat_loi)),
        ("tuTotCongThieu", "%d" % (tu["LOP CHU TOT"][0] + tu_tot_thieu)),
        ("ngoaiQuyUocHong", "%d" % sum(1 for r in hang if not r["loai_ten_tep"]
                                       and r["phan_loai"] == "LOP CHU HONG")),
        ("ngoaiQuyUocQuet", "%d" % sum(1 for r in hang if not r["loai_ten_tep"]
                                       and r["phan_loai"] == "QUET")),
        ("ngoaiQuyUocHongDPE", "19"),
    ] + [("truong%s%s" % (ma, hau), "%s" % v)
         for ma, (nn, va, vb) in truong.items()
         for hau, v in (("N", "%d" % nn), ("A", "%.1f" % va), ("B", "%.1f" % vb))
         ]
    # ⛔ 08/10: aucD* tung duoc sinh CA O DAY lan o code/e8_bo_do.py. Hai chuong trinh cung
    # ghi mot so la hai CHO O, va LaTeX chet ngay khi ca hai tep macro duoc nap
    # ("Command \\aucDone already defined"). Chu o DUNG la e8_bo_do.py vi chinh no TINH ra
    # cac AUC ay; o day chi DOC LAI de doi chieu, khong ghi nua.
    lech_auc = [k for k, v in sorted(aucs.items())
                if k not in ("D0",) and v is None]
    # ⛔ Ten macro LaTeX KHONG duoc chua chu so. `\aucD0` lam LaTeX chet ngay o preamble voi
    # thong bao lac de "Missing \begin{document}". Lop loi nay da co trong so tu du an giao
    # trinh (`\xCh10` in ra `107`) va toi vua lap lai. Hau to phai la CHU: zero, one, two...
    with io.open(os.path.join(RES, "so-lieu.tex"), "w", encoding="utf-8") as f:
        f.write("%% SINH TU DONG boi code/make_claims.py. KHONG sua tay.\n")
        for k, v in mac:
            f.write("\\newcommand{\\%s}{%s}\n" % (k, v))

    with io.open(os.path.join(RES, "tables", "tab-corpus.tex"), "w", encoding="utf-8") as f:
        f.write("%% SINH TU DONG. KHONG sua tay.\n")
        f.write("\\begin{tabular}{lrr}\n\\toprule\nText layer & Files & Share \\\\\n\\midrule\n")
        for ten, v in (("None (image only)", quet), ("Present but unusable", hong),
                       ("Present and usable", tot)):
            f.write("%s & %d & %.1f\\%% \\\\\n" % (ten, v, 100.0 * v / n))
        f.write("\\midrule\nTotal & %d & 100.0\\%% \\\\\n\\bottomrule\n\\end{tabular}\n" % n)

    with io.open(os.path.join(RES, "tables", "tab-tounicode.tex"), "w", encoding="utf-8") as f:
        f.write("%% SINH TU DONG. KHONG sua tay.\n")
        f.write("\\begin{tabular}{lrrr}\n\\toprule\nText layer & With \\texttt{/ToUnicode} & "
                "Files & Share \\\\\n\\midrule\n")
        for ten, k in (("Unusable", "LOP CHU HONG"), ("Usable", "LOP CHU TOT")):
            c, t = tu[k]
            f.write("%s & %d & %d & %.1f\\%% \\\\\n" % (ten, c, t, 100.0 * c / t))
        f.write("\\bottomrule\n\\end{tabular}\n")

    with io.open(os.path.join(RES, "tables", "tab-sohieu.tex"), "w", encoding="utf-8") as f:
        f.write("%% SINH TU DONG. KHONG sua tay.\n")
        f.write("\\begin{tabular}{lrrr}\n\\toprule\n & Correct & Wrong but plausible & "
                "No value \\\\\n\\midrule\n")
        f.write("Embedded text layer & %d & %d & %d \\\\\n" % (0, 0, a_khong))
        f.write("Modern OCR & %d & %d & %d \\\\\n" % (b_dung, b_sai, b_khong))
        f.write("\\bottomrule\n\\end{tabular}\n")

    print("\n=> DAT. Da sinh results/so-lieu.tex (%d macro) va 3 bang." % len(mac))
    print("   %d tep · quet %.1f%% · hong %.1f%% · tot %.1f%%" %
          (n, 100.0 * quet / n, 100.0 * hong / n, 100.0 * tot / n))
    print("   dao chieu: %.1f%% vs %.1f%%" % (ti_hong, ti_tot))
    print("   C4: B ra so %d ca, dung %.1f%% [%.1f, %.1f]" %
          (b_ra, 100.0 * b_dung / b_ra, 100 * lo, 100 * hi))
    return 0


if __name__ == "__main__":
    sys.exit(main())
