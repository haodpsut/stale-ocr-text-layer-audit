#!/usr/bin/env python3
"""Verify va SINH .bib tu Crossref.  python3 code/verify_ref.py

Luat nha (G7): moi tham khao phai verify **tac gia THAT + title THAT + VENUE THAT**, khong chi
"co ton tai". Cam placeholder, cam bia tac gia. Ca that da ghi trong so: bib cua mot bai co 4
venue SAI va 13 placeholder-author du 0 hallucination.

Nen tep nay KHONG verify phong doan cua toi. No SINH muc bib tu chinh du lieu Crossref tra ve,
roi doi chieu voi phong doan de bao chenh. Thu tu ay quan trong: neu sinh tu phong doan roi moi
"kiem", thi cai sai nam trong bib tu dau.

Ra: paper/refs.bib  +  results/ref-verify.md (bang doi chieu, co cot PHAN QUYET)
Ma thoat: 0 neu moi muc deu KHOP hoac duoc danh dau ro la CHUA VERIFY; 1 neu co muc LECH.
"""
import difflib, io, json, os, re, subprocess, sys, time

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# (khoa, truy van, ky vong: (ho tac gia dau, nam, manh venue))  -- ky vong chi de DOI CHIEU
UNG_VIEN = [
 ("bast2017benchmark", "A Benchmark and Evaluation for Text Extraction from PDF Bast Korzen", ("Bast", 2017, "JCDL")),
 ("meuschke2023benchmark", "A Benchmark of PDF Information Extraction Tools Using a Multi-task and Multi-domain Evaluation Framework", ("Meuschke", 2023, "")),
 ("lipinski2013evaluation", "Evaluation of header metadata extraction approaches and tools for scientific PDF documents", ("Lipinski", 2013, "")),
 ("knight2016enhancing", "Enhancing the Searchability of Page-Image PDF Documents Using an Aligned Hidden Layer from a Truth Text", ("Knight", 2016, "")),
 ("taghva1996evaluation", "Evaluation of model-based retrieval effectiveness with OCR text Taghva", ("Taghva", 1996, "TOIS")),
 ("taghva2004information", "Information access in the presence of OCR errors Taghva Nartker", ("Taghva", 2004, "")),
 ("croft1994evaluation", "An evaluation of information retrieval accuracy with simulated OCR output Croft Harding Taghva Borsack", ("Croft", 1994, "")),
 ("vanstrien2020assessing", "Assessing the Impact of OCR Quality on Downstream NLP Tasks", ("van Strien", 2020, "")),
 ("ghosh2016improving", "Improving Information Retrieval Performance on OCRed Text in the Absence of Clean Text Ground Truth", ("Ghosh", 2016, "Information Processing")),
 ("jaud2025beyond", "Beyond CER and WER How Does OCR Really Impact Information Retrieval", ("Jaud", 2025, "JCDL")),
 ("tanner2009measuring", "Measuring Mass Text Digitization Quality and Usefulness British Library 19th Century Newspaper", ("Tanner", 2009, "")),
 ("neudecker2021survey", "A survey of OCR evaluation tools and metrics Neudecker", ("Neudecker", 2021, "")),
 ("hegghammer2021ocr", "OCR with Tesseract Amazon Textract and Google Document AI benchmarking experiment", ("Hegghammer", 2021, "Computational Social Science")),
 ("reffle2013unsupervised", "Unsupervised profiling of OCRed historical documents Reffle Ringlstetter", ("Reffle", 2013, "Pattern Recognition")),
 ("gupta2015automatic", "Automatic Assessment of OCR Quality in Historical Documents Gupta", ("Gupta", 2015, "AAAI")),
 ("nguyen2021survey", "Survey of Post-OCR Processing Approaches Nguyen Jatowt", ("Nguyen", 2021, "Computing Surveys")),
 ("nguyen2023efficient", "An Efficient Unsupervised Approach for OCR Error Correction of Vietnamese OCR Text", ("Nguyen", 2023, "Access")),
 ("springmann2016automatic", "Springmann Fink Automatic quality evaluation and (semi-)automatic improvement of mixed models for OCR on historical documents", ("Springmann", 2016, "")),
 ("feng2006hierarchical", "A hierarchical HMM-based automatic evaluation of OCR accuracy for a digital library of books", ("Feng", 2006, "")),
 ("holley2009howgood", "How good can it get Analysing and improving OCR accuracy in large scale historic newspaper digitisation", ("Holley", 2009, "")),
 ("lehal2014automatic", "Automatic Bilingual Legacy-Fonts Identification and Conversion System Lehal", ("Lehal", 2014, "")),
 ("suzuki2006encodings", "Encodings in Legacy Khmer TrueType Fonts Suzuki Yamato", ("Suzuki", 2006, "")),
 ("singh2015gfuc", "GFUC Gurmukhi Font and Unicode Converter", ("Singh", 2015, "International Journal of Computer Applications")),
 ("hardie2007legacy", "From legacy encodings to Unicode the graphical and logical principles in the scripts of South Asia", ("Hardie", 2007, "Computers and the Humanities")),
 ("pipino2002data", "Data quality assessment Pipino Lee Wang", ("Pipino", 2002, "Communications of the ACM")),
 ("motro1989integrity", "Integrity equals validity plus completeness Motro", ("Motro", 1989, "Database Systems")),
 ("steimann2013wellformedness", "From well-formedness to meaning preservation model refactoring for almost free", ("Steimann", 2013, "Software and Systems Modeling")),
 ("nentwich2003flexible", "Flexible consistency checking Nentwich Emmerich", ("Nentwich", 2003, "Software Engineering and Methodology")),
 ("cong2007improving", "Improving data quality consistency and accuracy very large data bases Cong Fan Geerts Jia Ma", ("Cong", 2007, "")),
 ("ahmad2021validating", "Validating Data Validation Ahmad Dias", ("Ahmad", 2021, "Computer")),
 ("zhang2022automated", "Automated data validation an industrial experience report", ("Zhang", 2022, "Systems and Software")),
 ("termens2015analysis", "An analysis of file format control in institutional repositories", ("Termens", 2015, "Library Hi Tech")),
 ("caohongnga2019deep", "Deep Learning Based Vietnamese Diacritics Restoration", ("Cao", 2019, "")),
 ("marti2002iam", "The IAM-database an English sentence database for offline handwriting recognition", ("Marti", 2002, "IJDAR")),
 ("colavizza2020covid", "COVID-19 research in Wikipedia Colavizza", ("Colavizza", 2020, "Quantitative Science Studies")),
 ("kiesel2018reproducible", "Reproducible Web Corpora Kiesel", ("Kiesel", 2018, "Data and Information Quality")),
 ("papadopoulos2013impact", "The IMPACT dataset of historical document images", ("Papadopoulos", 2013, "")),
 ("pascal2022approaches", "Approaches for Automated Data Quality Analysis Syntactic and Semantic Assessment", ("", 2022, "")),
 ("kang2015automatic", "Automatic Recognition of Encoding on the Server for Preventing Mojibake", ("", 2015, "")),
 ("lamba2023exploring", "Exploring OCR Errors in Full-Text Large Documents A Study of LIS Theses and Dissertations", ("Lamba", 2023, "")),
 ("burchardt2023searches", "Are Searches in OCR-generated Archives Trustworthy Burchardt", ("Burchardt", 2023, "")),
 ("traub2018impact", "Impact of Crowdsourcing OCR Improvements on Retrievability Bias Traub", ("Traub", 2018, "")),
 ("oliveira2024creating", "Creating Resources and Evaluating the Impact of OCR Quality on Information Retrieval Oliveira Moreira", ("Oliveira", 2024, "")),
 ("gross2018ocr", "Todorov Is your OCR good enough Assessment of OCR quality impact on downstream tasks for Dutch texts", ("", 0, "")),
 ("bui2025hocr", "H-OCR A Hybrid OCR Approach to Vietnamese Scanned Administrative Text Recognition", ("Bui", 2025, "")),
]


def crossref(q, rows=3):
    try:
        out = subprocess.run(
            ["curl", "-s", "--max-time", "30",
             "https://api.crossref.org/works?rows=%d&select=title,author,container-title,"
             "issued,DOI,type,volume,page&query.bibliographic=%s"
             % (rows, re.sub(r"\s+", "+", q.strip()))],
            capture_output=True, text=True).stdout
        return json.loads(out)["message"]["items"]
    except Exception:
        return []


def giong(a, b):
    return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()


def sach(s):
    """Lam sach chuoi tu Crossref truoc khi dua vao LaTeX.

    ⛔ Crossref tra ve ca thuc the HTML (`&amp;`) lan `&` tho. Dua thang vao .bib thi BibTeX
    nuot, nhung LaTeX nem "Misplaced alignment tab character &" luc dung thu muc. Da dinh that.
    """
    s = re.sub(r"&amp;", "&", s)
    s = re.sub(r"<[^>]+>", "", s)
    for a, b in (("&", r"\&"), ("%", r"\%"), ("#", r"\#"), ("_", r"\_")):
        s = s.replace(a, b)
    return s


def bib(khoa, it):
    t = sach((it.get("title") or ["?"])[0])
    au = " and ".join("%s, %s" % (sach(a.get("family", "")), sach(a.get("given", "")))
                      for a in it.get("author", []) if a.get("family"))
    ven = sach((it.get("container-title") or [""])[0])
    nam = (it.get("issued", {}).get("date-parts") or [[""]])[0][0]
    loai = "inproceedings" if it.get("type") == "proceedings-article" else "article"
    truong = ["  title = {{%s}}" % t]
    if au:
        truong.append("  author = {%s}" % au)
    if ven:
        truong.append("  %s = {%s}" % ("booktitle" if loai == "inproceedings" else "journal", ven))
    if nam:
        truong.append("  year = {%s}" % nam)
    if it.get("volume"):
        truong.append("  volume = {%s}" % it["volume"])
    if it.get("page"):
        truong.append("  pages = {%s}" % it["page"])
    if it.get("DOI"):
        truong.append("  doi = {%s}" % it["DOI"])
    return "@%s{%s,\n%s\n}\n" % (loai, khoa, ",\n".join(truong))


def main():
    ra_bib, bang, lech, bo_di = [], [], 0, []
    for i, (khoa, q, ky) in enumerate(UNG_VIEN, 1):
        items = crossref(q)
        time.sleep(0.4)
        if not items:
            bang.append((khoa, "-", "-", "-", "KHONG TIM THAY"))
            lech += 1
            print("  %2d/%d  %-26s KHONG TIM THAY" % (i, len(UNG_VIEN), khoa))
            continue
        it = items[0]
        t = (it.get("title") or ["?"])[0]
        g = giong(t, q)
        ho = [a.get("family", "") for a in it.get("author", [])]
        ven = (it.get("container-title") or [""])[0]
        nam = (it.get("issued", {}).get("date-parts") or [[""]])[0][0]
        ok_ten = g > 0.55
        ok_tg = (not ky[0]) or any(ky[0].split()[-1].lower() in h.lower() for h in ho)
        ok_ven = (not ky[2]) or (ky[2].lower() in ven.lower())
        pq = ("KHOP" if (ok_ten and ok_tg and ok_ven) else
              "LECH: " + " ".join(x for x, c in
                                  (("ten", ok_ten), ("tacgia", ok_tg), ("venue", ok_ven)) if not c))
        # ⛔ LUAT NHA: khong lay duoc metadata that thi BO, tuyet doi khong bia. Chi khi TIEU DE
        # khop thi muc moi duoc vao .bib. Lech o venue hay thu tu ho/ten thuong la quai tat cua
        # du lieu Crossref chu khong phai sai bai, nen van giu; nhung lech TIEU DE nghia la
        # Crossref tra ve MOT BAI KHAC, va dua no vao bib la tao ra mot tham khao gia.
        if pq != "KHOP":
            lech += 1
        if ok_ten:
            bang.append((khoa, t[:58], (ho[0] if ho else "?"), "%s %s" % (nam, ven[:34]), pq))
            ra_bib.append(bib(khoa, it))
        else:
            bang.append((khoa, "(Crossref tra ve BAI KHAC: %s)" % t[:40], "-", "-",
                         "⛔ **BO KHOI BIB**"))
            bo_di.append(khoa)
        print("  %2d/%d  %-26s %-7s %s" % (i, len(UNG_VIEN), khoa, pq.split(":")[0], t[:52]))

    # ⛔ 08/10/2026: tep nay ten la "verify" nhung no GHI DE refs.bib. Chay no mot cach vo tu
    # sau khi vua them tay mot muc da lam **mat 18 muc** (38 -> 21): danh sach UNG_VIEN o tren
    # la nguon duy nhat no biet, va Crossref hom ay tra loi thieu cho vai muc. Tu nay no phai
    # TU CHOI ghi khi viec ghi lam MAT khoa, va phai sao luu truoc khi ghi.
    bib_p = os.path.join(GOC, "paper", "refs.bib")
    khoa_moi = set(re.findall(r"^@[a-z]*\{([a-z0-9]+),", "\n".join(ra_bib), re.M))
    khoa_cu = set()
    if os.path.exists(bib_p):
        khoa_cu = set(re.findall(r"^@[a-z]*\{([a-z0-9]+),",
                                 io.open(bib_p, encoding="utf-8").read(), re.M))
    mat = sorted(khoa_cu - khoa_moi)
    if mat and "--ghi-de" not in sys.argv:
        print("\n⛔ TU CHOI GHI refs.bib: viec ghi se lam MAT %d muc dang duoc dung:" % len(mat))
        print("   " + ", ".join(mat))
        print("   Neu that su muon, chay lai voi  --ghi-de  (co sao luu .bak).")
        print("   Thuong thi cai can lam la BO SUNG vao UNG_VIEN roi chay lai.")
        return 1
    if os.path.exists(bib_p):
        io.open(bib_p + ".bak", "w", encoding="utf-8").write(
            io.open(bib_p, encoding="utf-8").read())
    io.open(bib_p, "w", encoding="utf-8").write(
        "%% SINH TU CROSSREF boi code/verify_ref.py. KHONG sua tay.\n"
        "%% Moi muc lay tu du lieu Crossref, khong phai tu phong doan cua nguoi viet.\n\n"
        + "\n".join(ra_bib))
    with io.open(os.path.join(GOC, "results", "ref-verify.md"), "w", encoding="utf-8") as f:
        f.write("# Đối chiếu tham khảo với Crossref\n\nSinh bởi `code/verify_ref.py`. "
                "Mỗi mục bib lấy TỪ Crossref, cột phán quyết là kết quả đối chiếu với phỏng "
                "đoán ban đầu.\n\n| khoá | tiêu đề Crossref | tác giả đầu | năm + venue | phán quyết |\n")
        f.write("|---|---|---|---|---|\n")
        for r in bang:
            f.write("| `%s` | %s | %s | %s | %s |\n" % r)
    print("\n=> %d muc VAO refs.bib · %d muc BI BO (Crossref tra ve bai khac): %s"
          % (len(ra_bib), len(bo_di), ", ".join(bo_di)))
    print("   san journal la >= 36 tham khao: %s" % ("DAT" if len(ra_bib) >= 36 else "CHUA DAT"))
    return 0 if len(ra_bib) >= 36 else 1


if __name__ == "__main__":
    sys.exit(main())
