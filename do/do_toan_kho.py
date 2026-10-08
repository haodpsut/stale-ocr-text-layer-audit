#!/usr/bin/env python3
"""Do TOAN BO kho, khong lay mau:  python3 do/do_toan_kho.py

Sinh `results/toan-kho.csv` mot dong mot tep, roi in bang tong hop. Day la Bang 1 cua bai:
so dem THAT, khong phai uoc luong tu mau.

Cot: nguon, ten tep, so trang, phan loai, ti le ky tu co dau, producer, moi font co /ToUnicode,
     so hieu trong ten tep (neu ten tep theo khuon).

Chay lai duoc: neu tep CSV da co thi bo qua nhung dong da ghi.
"""
import collections, csv, io, os, re, subprocess, sys, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from do_lop_chu import ti_le_co_dau, cac_pdf         # noqa: E402

RA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                  "results", "toan-kho.csv")
KHUON = re.compile(r"^(\d{3,4})_([A-Z]{2,4})_(\d{4})_([A-Z]+)", re.I)
COT = ["nguon", "tep", "so_trang", "phan_loai", "ti_le_dau", "producer",
       "moi_font_co_tounicode", "so_hieu_ten_tep", "loai_ten_tep"]


def mot_tep(nguon, p):
    ten = os.path.basename(p)
    d = {"nguon": nguon, "tep": ten, "so_trang": "", "phan_loai": "", "ti_le_dau": "",
         "producer": "", "moi_font_co_tounicode": "", "so_hieu_ten_tep": "", "loai_ten_tep": ""}
    m = KHUON.match(ten)
    if m:
        d["so_hieu_ten_tep"] = str(int(m.group(1)))
        d["loai_ten_tep"] = m.group(2).upper()
    try:
        t = subprocess.run(["pdftotext", "-l", "3", p, "-"],
                           capture_output=True, text=True, timeout=45).stdout
    except Exception:
        d["phan_loai"] = "khong mo duoc"
        return d
    if len(t.strip()) < 20:
        d["phan_loai"] = "QUET"
    else:
        tl = ti_le_co_dau(t)
        if tl is None:
            d["phan_loai"] = "qua it chu"
        else:
            d["ti_le_dau"] = "%.4f" % tl
            d["phan_loai"] = "LOP CHU HONG" if tl < 0.12 else "LOP CHU TOT"
    try:
        from pypdf import PdfReader
        r = PdfReader(p)
        d["so_trang"] = str(len(r.pages))
        md = r.metadata
        if md:
            d["producer"] = str(md.get("/Producer") or md.get("/Creator") or "").strip()[:60]
        fo = (r.pages[0].get("/Resources") or {}).get("/Font")
        if fo:
            fo = fo.get_object()
            c = [("/ToUnicode" in fo[k].get_object()) for k in fo]
            d["moi_font_co_tounicode"] = str(bool(c and all(c)))
    except Exception:
        pass
    return d


def main():
    os.makedirs(os.path.dirname(RA), exist_ok=True)
    da_co = set()
    if os.path.exists(RA):
        with io.open(RA, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                da_co.add((r["nguon"], r["tep"]))
        print("tiep tuc: da co %d dong" % len(da_co))

    kho = cac_pdf()
    tong = sum(len(v) for v in kho.values())
    moi = not os.path.exists(RA)
    f = io.open(RA, "a", encoding="utf-8", newline="")
    w = csv.DictWriter(f, fieldnames=COT)
    if moi:
        w.writeheader()
    xong = len(da_co)
    for nguon, ps in kho.items():
        for p in ps:
            if (nguon, os.path.basename(p)) in da_co:
                continue
            w.writerow(mot_tep(nguon, p))
            xong += 1
            if xong % 250 == 0:
                f.flush()
                print("  ... %d/%d" % (xong, tong), flush=True)
    f.close()
    print("da ghi %s" % RA)

    with io.open(RA, encoding="utf-8") as f:
        hang = list(csv.DictReader(f))
    print("\n== BANG 1: TOAN KHO (n=%d, KHONG lay mau) ==" % len(hang))
    d = collections.Counter(r["phan_loai"] for r in hang)
    for k, v in d.most_common():
        print("  %-16s %5d  (%.1f%%)" % (k, v, 100.0 * v / len(hang)))
    cc = d["LOP CHU HONG"] + d["LOP CHU TOT"]
    if cc:
        print("  => trong so tep CO lop chu: %d/%d = %.1f%% HONG" %
              (d["LOP CHU HONG"], cc, 100.0 * d["LOP CHU HONG"] / cc))

    print("\n== BANG 2: PHAN MEM SINH PDF (chi tep co lop chu) ==")
    pm = collections.defaultdict(collections.Counter)
    for r in hang:
        if r["phan_loai"] in ("LOP CHU HONG", "LOP CHU TOT"):
            pm[r["producer"] or "(trong)"][r["phan_loai"]] += 1
    print("  %-52s %6s %6s %8s" % ("producer", "hong", "tot", "ti le"))
    for t, c in sorted(pm.items(), key=lambda x: -sum(x[1].values()))[:14]:
        h, g = c["LOP CHU HONG"], c["LOP CHU TOT"]
        print("  %-52s %6d %6d %7.0f%%" % (t[:52], h, g, 100.0 * h / (h + g)))

    print("\n== BANG 3: /ToUnicode (phep dao nguoc) ==")
    for k in ("LOP CHU HONG", "LOP CHU TOT"):
        x = [r["moi_font_co_tounicode"] for r in hang
             if r["phan_loai"] == k and r["moi_font_co_tounicode"]]
        co = sum(1 for v in x if v == "True")
        print("  %-14s moi font co /ToUnicode: %5d/%-5d (%.1f%%)" %
              (k, co, len(x), 100.0 * co / len(x) if x else 0))

    print("\n== BANG 4: THEO NGUON ==")
    for n in sorted(set(r["nguon"] for r in hang)):
        s = [r for r in hang if r["nguon"] == n]
        c = collections.Counter(r["phan_loai"] for r in s)
        k = c["LOP CHU HONG"] + c["LOP CHU TOT"]
        print("  %-20s n=%5d  quet %5d  hong %5d  tot %5d  %s" %
              (n, len(s), c["QUET"], c["LOP CHU HONG"], c["LOP CHU TOT"],
               ("(%.1f%% hong)" % (100.0 * c["LOP CHU HONG"] / k)) if k else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
