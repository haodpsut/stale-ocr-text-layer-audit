#!/usr/bin/env python3
"""Do SUC KHOE LOP CHU cua kho van ban:  python3 do/do_lop_chu.py [--mau 400]

Phat hien ra khi lam phep giet U2: nhieu PDF "co lop chu" thi lop chu ay KHONG DUNG DUOC.
Boc ra duoc 'BO GIAO DVC vA DAo TAO', 'Tnrong D~I HQC', 'Can cir quyet dinh s6'.

⛔ NGUYEN NHAN da duoc xac dinh lai 23/09 bang `do/do_ban_chat.py` (40/40 vs 0/40):
KHONG phai ma cu TCVN3 nhu toi ket luan luc dau, ma la **ban QUET co san mot lop OCR CU
nhung vao duoi anh** (anh phu >80%% trang, che do to chu vo hinh Tr 3). Xem
`gap/SUA-CAU-CHUYEN.md`. Hau qua giong nhau: moi he thong boc chu, tim kiem, lap chi muc
deu nuot rac ma KHONG bao loi, vi cong cu chi hoi "co lop chu chua" chu khong hoi "lop chu
co dung khong".

Phan ba nhom:
  QUET        : khong boc duoc chu (can OCR)
  LOP CHU HONG: boc duoc chu nhung gan nhu khong co ky tu co dau -> lop chu KHONG DUNG DUOC
  LOP CHU TOT : boc duoc chu Unicode tieng Viet binh thuong

DOI CHUNG (in cuoi): ti le ky tu co dau cua ba van ban tieng Viet Unicode TU TAO (phai cao)
va cua mot chuoi ASCII thuan (phai = 0). Bo do sai o hai ca nay thi moi so tren deu vo nghia.
"""
import argparse, collections, os, random, re, subprocess, sys, unicodedata

GOC = "/Users/agentra/Documents/hao/working"
NGUON = ["van-ban-tong-hop", "dau-van-ban", "edu-legal-crawl"]
SEED = 20260923

# Chu cai tieng Viet CO DAU (ke ca dau mu, dau moc, dau thanh). Khong gom a-z ASCII.
CO_DAU = re.compile(
    r"[À-ỹ]|[ĂăĐđƠơƯư]")


def ti_le_co_dau(t):
    """Ti le ky tu co dau tren tong so CHU CAI. Van ban hanh chinh VN that luon cao."""
    chu = [c for c in t if c.isalpha()]
    if len(chu) < 50:
        return None
    return sum(1 for c in chu if CO_DAU.match(c)) / float(len(chu))


def boc(p, trang=3):
    try:
        return subprocess.run(["pdftotext", "-l", str(trang), p, "-"],
                              capture_output=True, text=True, timeout=30).stdout
    except Exception:
        return None


def cac_pdf():
    r = collections.OrderedDict()
    for n in NGUON:
        ps = []
        for g, _, fs in os.walk(os.path.join(GOC, n)):
            ps += [os.path.join(g, f) for f in fs if f.lower().endswith(".pdf")]
        r[n] = sorted(ps)
    return r


def phan_loai(p, nguong=0.12):
    t = boc(p)
    if t is None:
        return "khong mo duoc", None
    if len(t.strip()) < 20:
        return "QUET", None
    tl = ti_le_co_dau(t)
    if tl is None:
        return "qua it chu", None
    return ("LOP CHU HONG" if tl < nguong else "LOP CHU TOT"), tl


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mau", type=int, default=400)
    ap.add_argument("--nguong", type=float, default=0.12)
    a = ap.parse_args()
    random.seed(SEED)

    print("== DOI CHUNG BO DO ==")
    that = ("Can cu Quyet dinh so 45/QD-DHKT ngay 12 thang 3 nam 2019 cua Hieu truong "
            "Truong Dai hoc Kien truc Da Nang ve viec ban hanh quy che dao tao")
    unicode_that = ("Căn cứ Quyết định số 45/QĐ-ĐHKT ngày 12 tháng 3 năm 2019 của Hiệu "
                    "trưởng Trường Đại học Kiến trúc Đà Nẵng về việc ban hành quy chế đào tạo")
    hong_that = "BO GIAO DVC vA DAo TAO TRUONG DH KIEN TRue DA. NANG CONG HOA. xA HOI cHiJ NGHiA"
    for ten, s, mong in (("Unicode tieng Viet that", unicode_that, "cao"),
                         ("ASCII khong dau", that, "~0"),
                         ("ma cu (TCVN3) that", hong_that, "~0")):
        print("  %-24s ti le co dau = %.3f   (mong doi %s)" % (ten, ti_le_co_dau(s) or 0, mong))
    r_uni, r_ascii = ti_le_co_dau(unicode_that), ti_le_co_dau(that)
    dat = r_uni > 0.25 and r_ascii < 0.02
    print("  => bo do %s\n" % ("DAT" if dat else "HONG, dung tin so ben duoi"))

    kho = cac_pdf()
    tat = [p for v in kho.values() for p in v]
    mau = random.sample(tat, min(a.mau, len(tat)))
    print("== PHAN LOAI (n=%d / %d PDF, nguong co dau=%.2f, seed=%d) ==" %
          (len(mau), len(tat), a.nguong, SEED))
    dem = collections.Counter()
    tl_hong, tl_tot = [], []
    for p in mau:
        k, tl = phan_loai(p, a.nguong)
        dem[k] += 1
        if k == "LOP CHU HONG":
            tl_hong.append(tl)
        elif k == "LOP CHU TOT":
            tl_tot.append(tl)
    for k, v in dem.most_common():
        print("  %-16s %4d  (%.1f%%)" % (k, v, 100.0 * v / len(mau)))

    co_chu = dem["LOP CHU HONG"] + dem["LOP CHU TOT"]
    if co_chu:
        print("\n  Trong so PDF CO lop chu: %d/%d = %.1f%% lop chu HONG" %
              (dem["LOP CHU HONG"], co_chu, 100.0 * dem["LOP CHU HONG"] / co_chu))
    for ten, x in (("hong", tl_hong), ("tot", tl_tot)):
        if x:
            x.sort()
            print("  ti le co dau, nhom %-4s: trung vi %.3f, lon nhat %.3f" %
                  (ten, x[len(x) // 2], x[-1]))

    print("\n== THEO NGUON ==")
    for n, ps in kho.items():
        if not ps:
            continue
        m2 = random.sample(ps, min(60, len(ps)))
        d2 = collections.Counter(phan_loai(p, a.nguong)[0] for p in m2)
        cc = d2["LOP CHU HONG"] + d2["LOP CHU TOT"]
        print("  %-20s n=%3d  quet %3d  lop chu hong %3d  tot %3d  %s" %
              (n, len(m2), d2["QUET"], d2["LOP CHU HONG"], d2["LOP CHU TOT"],
               ("(%.0f%% lop chu hong)" % (100.0 * d2["LOP CHU HONG"] / cc)) if cc else ""))
    return 0 if dat else 1


if __name__ == "__main__":
    sys.exit(main())
