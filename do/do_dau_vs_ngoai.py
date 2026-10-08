#!/usr/bin/env python3
"""PHEP GIET cho ung vien U2: doc may co te hon BEN TRONG vung dau do khong?

  python3 do/do_dau_vs_ngoai.py [--trang 50] [--dpi 200]

Vi sao khong phai khoanh tay: dung ban SINH SO co dau do. Lop chu trong PDF la van ban
tham chieu (co san toa do tung tu), con dau do la anh de len tren. Dung trang ra anh, cho
tesseract doc, roi ghep tung tu theo TOA DO. Moi tu co hai nhan:
  - trong/ngoai vung dau do  (dem diem anh do trong hop cua tu)
  - sai so ky tu so voi tu tham chieu
=> so sanh CER trong vs ngoai TREN CUNG MOT TRANG, nen moi thu khac (chat luong quet, phong
   chu, co chu) deu bi khu.

DOI CHUNG AM (bat buoc, in cuoi): chay dung phep do tren cac trang KHONG co dau do, chia tu
thanh hai nhom NGAU NHIEN cung co. Neu bo do van bao chenh lech lon o day thi bo do hong,
khong phai dau do co hai.

Ma thoat: 0 chay xong, 1 doi chung am that bai.
"""
import argparse, collections, glob, os, random, re, subprocess, sys, tempfile

GOC = "/Users/agentra/Documents/hao/working"
NGUON = ["van-ban-tong-hop", "dau-van-ban", "edu-legal-crawl"]
SEED = 20260923


def levenshtein(a, b):
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    truoc = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        nay = [i]
        for j, cb in enumerate(b, 1):
            nay.append(min(truoc[j] + 1, nay[j - 1] + 1, truoc[j - 1] + (ca != cb)))
        truoc = nay
    return truoc[-1]


def cac_pdf():
    r = []
    for n in NGUON:
        for g, _, fs in os.walk(os.path.join(GOC, n)):
            r += [os.path.join(g, f) for f in fs if f.lower().endswith(".pdf")]
    return sorted(r)


def mat_na_do(im):
    """Mang bool cung kich thuoc anh: True o diem anh DO DAM (muc dau)."""
    import numpy as np
    a = np.asarray(im.convert("RGB")).astype("int16")
    r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    return (r > 110) & (r - g > 55) & (r - b > 55)


def doc_tsv(anh):
    """tesseract -> [(x, y, w, h, chu)] muc TU."""
    r = subprocess.run(["tesseract", anh, "stdout", "-l", "vie", "--psm", "3", "tsv"],
                       capture_output=True, text=True)
    ra = []
    for d in r.stdout.splitlines()[1:]:
        c = d.split("\t")
        if len(c) < 12 or c[11].strip() == "":
            continue
        try:
            ra.append((int(c[6]), int(c[7]), int(c[8]), int(c[9]), c[11].strip()))
        except ValueError:
            continue
    return ra


def iou(p, q):
    ax, ay, aw, ah = p
    bx, by, bw, bh = q
    x0, y0 = max(ax, bx), max(ay, by)
    x1, y1 = min(ax + aw, bx + bw), min(ay + ah, by + bh)
    if x1 <= x0 or y1 <= y0:
        return 0.0
    g = (x1 - x0) * (y1 - y0)
    return g / float(aw * ah + bw * bh - g)


def mot_trang(p, dpi, cho_dau=True):
    """Tra ve (danh sach cap, so tu trong dau) hoac None."""
    import fitz
    from PIL import Image
    try:
        d = fitz.open(p)
    except Exception:
        return None
    if d.page_count < 1:
        return None
    tr = d[0]
    tu_goc = tr.get_text("words")          # (x0,y0,x1,y1,chu,...)
    if len(tu_goc) < 40:                   # ban quet: khong co lop chu
        return None
    # ⛔ LOC BAT BUOC, them 23/09 sau khi lan chay dau cho ket qua VO NGHIA.
    # 55,6% tep co lop chu thi lop chu ay la ma cu TCVN3/VNI, tuc RAC. Lay rac lam van ban
    # tham chieu thi CER ra 0,33 o ca hai nhom va phep so trong/ngoai mat sach y nghia.
    import sys as _s, os as _o
    _s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__)))
    from do_lop_chu import ti_le_co_dau
    tl_dau = ti_le_co_dau(" ".join(w[4] for w in tu_goc))
    if tl_dau is None or tl_dau < 0.12:
        return None
    ti_le = dpi / 72.0
    with tempfile.TemporaryDirectory() as t:
        subprocess.run(["pdftoppm", "-r", str(dpi), "-f", "1", "-l", "1", "-png", p,
                        os.path.join(t, "x")], capture_output=True, timeout=120)
        a = glob.glob(os.path.join(t, "*.png"))
        if not a:
            return None
        im = Image.open(a[0])
        mn = mat_na_do(im)
        co_dau = mn.sum() / float(mn.size) > 0.0015
        if cho_dau != co_dau:
            return None
        ocr = doc_tsv(a[0])
    H, W = mn.shape
    cap = []
    for x0, y0, x1, y1, chu in [(w[0], w[1], w[2], w[3], w[4]) for w in tu_goc]:
        hp = (int(x0 * ti_le), int(y0 * ti_le),
              max(1, int((x1 - x0) * ti_le)), max(1, int((y1 - y0) * ti_le)))
        tot, doc_duoc = 0.0, ""
        for o in ocr:
            v = iou(hp, o[:4])
            if v > tot:
                tot, doc_duoc = v, o[4]
        if tot < 0.25:                     # khong ghep duoc: bo, khong doan
            continue
        bx, by, bw, bh = hp
        o_trong = mn[max(0, by):min(H, by + bh), max(0, bx):min(W, bx + bw)]
        ty_do = o_trong.mean() if o_trong.size else 0.0
        cap.append((chu, doc_duoc, ty_do > 0.02))
    return cap


def tinh(cap):
    """CER gop: tong khoang cach / tong do dai tham chieu."""
    kc = sum(levenshtein(a, b) for a, b, _ in cap)
    dd = sum(len(a) for a, _, _ in cap)
    return (kc / dd if dd else 0.0), len(cap)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trang", type=int, default=50)
    ap.add_argument("--dpi", type=int, default=200)
    a = ap.parse_args()
    random.seed(SEED)
    ds = cac_pdf()
    random.shuffle(ds)
    print("== PHEP GIET U2: trong vs ngoai vung dau do ==")
    print("   nguon %d PDF, dpi=%d, seed=%d\n" % (len(ds), a.dpi, SEED))

    trong, ngoai, so_trang = [], [], 0
    for p in ds:
        if so_trang >= a.trang:
            break
        c = mot_trang(p, a.dpi, cho_dau=True)
        if not c:
            continue
        t = [x for x in c if x[2]]
        if len(t) < 5:                     # dau khong de len chu o trang nay
            continue
        so_trang += 1
        trong += t
        ngoai += [x for x in c if not x[2]]
        if so_trang % 10 == 0:
            print("   ... %d trang" % so_trang)

    if so_trang == 0:
        sys.exit("khong tim duoc trang nao co dau de len chu")

    ct, nt = tinh(trong)
    cn, nn = tinh(ngoai)
    print("\n%d trang co dau do de len chu" % so_trang)
    print("  %-26s %6s %8s" % ("nhom", "so tu", "CER"))
    print("  %-26s %6d %8.4f" % ("TRONG vung dau", nt, ct))
    print("  %-26s %6d %8.4f" % ("NGOAI vung dau", nn, cn))
    print("  chenh lech tuyet doi        %8.4f" % (ct - cn))
    print("  ty so                       %8.2f lan" % (ct / cn if cn else 0))

    print("\n== DOI CHUNG AM: trang KHONG co dau, chia ngau nhien hai nhom ==")
    kd = []
    for p in ds:
        if len(kd) >= 12:
            break
        c = mot_trang(p, a.dpi, cho_dau=False)
        if c and len(c) > 60:
            kd.append(c)
    if not kd:
        print("  khong lay duoc trang khong dau => KHONG KET LUAN DUOC")
        return 1
    lech = []
    for c in kd:
        x = list(c)
        random.shuffle(x)
        k = int(len(x) * (nt / float(nt + nn)))
        k = max(5, min(len(x) - 5, k))
        c1, _ = tinh(x[:k])
        c2, _ = tinh(x[k:])
        lech.append(abs(c1 - c2))
    lech.sort()
    tv = lech[len(lech) // 2]
    print("  %d trang, chenh lech ngau nhien: trung vi %.4f, lon nhat %.4f" %
          (len(lech), tv, lech[-1]))
    dat = abs(ct - cn) > 3 * max(tv, 1e-9)
    print("  => chenh lech THAT %s nhieu ngau nhien (nguong: gap 3 lan trung vi)"
          % ("LON HON" if dat else "KHONG lon hon"))
    print("\n  PHAN QUYET U2: %s" % ("CON SONG" if dat else "BI GIET"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
