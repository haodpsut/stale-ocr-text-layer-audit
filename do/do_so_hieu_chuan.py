#!/usr/bin/env python3
"""Do DO CHINH XAC so hieu, co VAN BAN CHUAN.  python3 do/do_so_hieu_chuan.py [--n 60]

⛔ Sua mot ket luan sai cua chinh toi (23/09). `do_viet_tay.py` bao 55% so hieu la "viet tay".
SAI. Nhin ky vi du ben canh ten tep:
    ten tep 0626 -> OCR doc 'e7e'      ten tep 0444 -> 'a4a'
    ten tep 0630 -> '6)0'              ten tep 0043 -> 'a43'     ten tep 0357 -> '35"'
Cung MOT day so, bi doc nham theo kieu OCR kinh dien (6->e, 4->a, 0->), 7->"). Khong phai
chu viet tay. Bo phan loai cu chi do "ky tu khong phai chu so" nen goi nham ten hien tuong.

Nhung cho sai ay lo ra thu gia tri hon: **ten tep LA van ban chuan cho so hieu**. Bang chung:
noi OCR doc sach thi no khop ten tep (0442 -> '442 /2015', 0687 -> '687 /2015'), va noi doc ban
thi chuoi rac van giu dung so chu so.

Nen do duoc DO CHINH XAC THAT, khong phai chi "hai ben co khop nhau khong":
    A = lop chu nhung san     B = OCR hien dai     chuan = so trong ten tep
Va cau hoi quan trong nhat: khi mot ben tra ve mot so TRONG NHU THAT, no dung bao nhieu phan tram?
"""
import argparse, collections, os, random, re, sys, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from do_lop_chu import phan_loai, cac_pdf, SEED     # noqa: E402
from do_truong import gap_dau, doc_A, doc_B         # noqa: E402

KHUON = re.compile(r"^(\d{3,4})_([A-Z]{2,4})_(\d{4})_([A-Z]+)", re.I)
DOAN = re.compile(r"\bso\s*[:.]?\s*(.{0,30}?)/\s*(qd|tb|cv|kh|hd|bc)\b")


def so_hieu(t):
    """Tra ve (chuoi tho giua 'So:' va '/QD', so nguyen neu boc duoc mot so sach).

    ⭐ NEO VAO PHAN DAU TRANG. Ban dau toi tim tren CA trang, va bo trich nhat nham mot CAN CU
    (270/2006/QD-TTg cua Thu tuong) roi bao la so hieu cua van ban. Do la loi cua bo trich, khong
    phai loi cua OCR, va tron hai nguyen nhan lai thi con so cuoi cung vo nghia. So hieu rieng
    cua van ban luon nam TRUOC cum 'can cu' dau tien.
    """
    g0 = gap_dau(t)
    k = g0.find("can c")
    m = DOAN.search(g0[:k] if k > 80 else g0)
    if not m:
        return None, None
    tho = m.group(1).strip()
    s = re.match(r"^\s*(\d{1,5})\b", tho)
    return tho, (int(s.group(1)) if s else None)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=60)
    a = ap.parse_args()
    random.seed(SEED)
    tat = [p for v in cac_pdf().values() for p in v]
    random.shuffle(tat)
    mau = []
    for p in tat:
        if len(mau) >= a.n:
            break
        if KHUON.match(os.path.basename(p)) and phan_loai(p)[0] == "LOP CHU HONG":
            mau.append(p)

    d = collections.Counter()
    sai = []
    for p in mau:
        chuan = int(KHUON.match(os.path.basename(p)).group(1))
        try:
            tho_a, sa = so_hieu(doc_A(p))
            tho_b, sb = so_hieu(doc_B(p))
        except Exception:
            continue
        d["xet"] += 1
        for ten, s, tho in (("A lop chu", sa, tho_a), ("B OCR moi", sb, tho_b)):
            if s is None:
                d[ten + ": khong ra so nao"] += 1
            elif s == chuan:
                d[ten + ": DUNG"] += 1
            else:
                d[ten + ": SAI ma trong nhu that"] += 1
                if ten.startswith("B") and len(sai) < 8:
                    sai.append((os.path.basename(p)[:28], chuan, s, tho))

    n = d["xet"] or 1
    print("== DO CHINH XAC SO HIEU, van ban chuan = so trong ten tep (n=%d) ==" % n)
    for ten in ("A lop chu", "B OCR moi"):
        dung = d[ten + ": DUNG"]
        saii = d[ten + ": SAI ma trong nhu that"]
        khong = d[ten + ": khong ra so nao"]
        ra = dung + saii
        print("\n  %s" % ten)
        print("    ra mot so  : %3d (%3.0f%%)" % (ra, 100.0 * ra / n))
        print("      trong do DUNG        : %3d (%3.0f%% cua ca mau)" % (dung, 100.0 * dung / n))
        print("      trong do SAI         : %3d (%3.0f%% cua ca mau)" % (saii, 100.0 * saii / n))
        print("    khong ra so: %3d (%3.0f%%)" % (khong, 100.0 * khong / n))
        if ra:
            print("    ⭐ KHI DA TRA VE MOT SO, no dung %.0f%% (%d/%d)" %
                  (100.0 * dung / ra, dung, ra))
    print("\n== VI DU B SAI (so trong nhu that nhung khac van ban chuan) ==")
    for ten, c, s, tho in sai:
        print("  %-28s chuan=%-5d OCR=%-5d  chuoi tho=%r" % (ten, c, s, tho))
    print("\n  Chi so dang chu y nhat la dong ⭐: no do dung cai ma mot pipeline KHONG the tu biet.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
