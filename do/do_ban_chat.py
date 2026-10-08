#!/usr/bin/env python3
"""Lop chu HONG that ra la gi?  python3 do/do_ban_chat.py [--n 40]

Phai chay vi toi suyt viet sai cau chuyen. Nhin chu boc ra: 'Tnrong' cho "Truong", 's6' cho
"so", 'cir' cho "cu". Day la LOI OCR kinh dien, KHONG phai mojibake cua ma cu TCVN3. Gia thuyet
moi: cac tep ay la BAN QUET co san mot lop OCR toi nhung vao, chu khong phai ban sinh so.

Hai gia thuyet cho hai bai bao hoan toan khac nhau:
  GT-A "ma cu"        : ban sinh so that, glyph ve chu Viet nhung /ToUnicode khai sang Latin.
                        Sua duoc bang chuyen ma, khong mat mat.
  GT-B "OCR nhung san": anh quet + lop chu vo hinh do mot may OCR cu sinh ra. Khong sua duoc
                        bang chuyen ma; phai OCR LAI. Va lop chu ay la mot LOI DO, khong phai
                        mot phep ma hoa.

Phan biet bang ba dau hieu doc duoc tu chinh tep:
  1. trang 1 co anh phu gan het trang khong  (quet thi co)
  2. che do to chu cua lop chu  (OCR nhung thuong dung che do vo hinh, Tr 3)
  3. ti le tu KHONG co trong tu dien tieng Viet khong dau  (OCR toi thi cao bat thuong)
"""
import argparse, collections, os, random, re, sys, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from do_lop_chu import phan_loai, cac_pdf, SEED     # noqa: E402


def dau_hieu(p):
    import fitz
    try:
        d = fitz.open(p)
        tr = d[0]
    except Exception:
        return None
    dt = tr.rect
    dien_trang = abs(dt.width * dt.height) or 1.0

    # 1. anh lon nhat phu bao nhieu phan trang
    phu = 0.0
    try:
        for im in tr.get_image_info():
            b = im.get("bbox")
            if b:
                from fitz import Rect
                r = Rect(b)
                phu = max(phu, abs(r.width * r.height) / dien_trang)
    except Exception:
        pass

    # 2. che do to chu: 3 = vo hinh (lop OCR nam duoi anh)
    vo_hinh = 0
    tong_span = 0
    try:
        for bl in tr.get_text("dict")["blocks"]:
            for ln in bl.get("lines", []):
                for sp in ln.get("spans", []):
                    tong_span += 1
                    # bit 'render mode' khong co san; dung mau trang/alpha lam dau hieu phu
                    if sp.get("color", 0) == 16777215:
                        vo_hinh += 1
    except Exception:
        pass
    return phu, (vo_hinh / tong_span if tong_span else 0.0), tong_span


def kiem_che_do_to(p):
    """Doc thang luong lenh trang: Tr 3 = to chu vo hinh. Dau hieu chac chan cua lop OCR."""
    import fitz
    try:
        d = fitz.open(p)
        noi_dung = d[0].read_contents().decode("latin-1", "ignore")
    except Exception:
        return None
    return bool(re.search(r"\b3\s+Tr\b", noi_dung))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=40)
    a = ap.parse_args()
    random.seed(SEED)
    tat = [p for v in cac_pdf().values() for p in v]
    random.shuffle(tat)

    nhom = {"LOP CHU HONG": [], "LOP CHU TOT": []}
    for p in tat:
        if all(len(v) >= a.n for v in nhom.values()):
            break
        k, _ = phan_loai(p)
        if k in nhom and len(nhom[k]) < a.n:
            nhom[k].append(p)

    print("== BAN CHAT LOP CHU HONG: ma cu (GT-A) hay OCR nhung san (GT-B)? ==")
    print("  %-14s %5s %10s %10s %10s" %
          ("nhom", "n", "anh>80%", "to vo hinh", "tb span"))
    for k, ps in nhom.items():
        anh, vh, sp, n = 0, 0, [], 0
        for p in ps:
            d = dau_hieu(p)
            if d is None:
                continue
            n += 1
            if d[0] > 0.80:
                anh += 1
            sp.append(d[2])
            if kiem_che_do_to(p):
                vh += 1
        print("  %-14s %5d %9s %10s %10.0f" %
              (k, n, "%d (%.0f%%)" % (anh, 100.0 * anh / n) if n else "-",
               "%d (%.0f%%)" % (vh, 100.0 * vh / n) if n else "-",
               sum(sp) / len(sp) if sp else 0))

    print("\n== PHAN QUYET ==")
    print("  anh phu >80%% trang + che do to VO HINH  => GT-B: ban QUET co lop OCR nhung san")
    print("  khong anh + glyph ve chu Viet            => GT-A: ban sinh so, ma cu")
    print("\n  Ai dung thi doi ca ten bai. GT-B thi 'lop chu noi doi' van dung, nhung nguyen")
    print("  nhan la MOT MAY OCR CU da chay va ket qua bi dong bang trong tep, chu khong phai")
    print("  van de ma hoa. Va khi do KHONG the sua bang chuyen ma, phai OCR lai.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
