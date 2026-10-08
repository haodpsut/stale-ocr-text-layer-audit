#!/usr/bin/env python3
"""Do KHO VAN BAN co san, truoc khi hua bat cu dieu gi trong de cuong bai.

  python3 do/do_corpus.py [--mau 120] [--dau 40]

In ba so, moi so co doi chung:
  1. Ti le PDF QUET / SINH SO  (quet = pdftotext 2 trang dau ra < 20 ky tu)
  2. Ti le trang co DAU DO     (dem diem anh do dam sau khi dung pdftoppm 80 dpi)
  3. Doi chung am cho phep (2): cung phep dem chay tren ban SINH SO, noi dau do van co;
     va tren mot anh xam tu tao, noi KHONG the co dau do (phai ra 0,000).
Seed co dinh. Moi lan chay lai ra cung so.
"""
import argparse, collections, os, random, subprocess, sys, tempfile

GOC = "/Users/agentra/Documents/hao/working"
NGUON = ["van-ban-tong-hop", "dau-van-ban", "edu-legal-crawl"]
SEED = 20260923


def liet_ke():
    r = collections.OrderedDict()
    for n in NGUON:
        d, ps = os.path.join(GOC, n), []
        for g, _, fs in os.walk(d):
            ps += [os.path.join(g, f) for f in fs if f.lower().endswith(".pdf")]
        r[n] = sorted(ps)
    return r


def co_chu(p, nguong=20):
    """True neu boc duoc chu (ban sinh so). Loi khi mo = coi nhu khong boc duoc."""
    try:
        t = subprocess.run(["pdftotext", "-l", "2", p, "-"],
                           capture_output=True, text=True, timeout=30).stdout
    except Exception:
        return None
    return len(t.strip()) >= nguong


def ti_le_do(p, dpi=80):
    """Ti le diem anh DO DAM tren trang 1. None neu khong dung duoc anh."""
    from PIL import Image
    with tempfile.TemporaryDirectory() as tmp:
        dau = os.path.join(tmp, "t")
        try:
            subprocess.run(["pdftoppm", "-r", str(dpi), "-f", "1", "-l", "1",
                            "-png", p, dau], capture_output=True, timeout=60)
        except Exception:
            return None
        anh = [f for f in os.listdir(tmp) if f.endswith(".png")]
        if not anh:
            return None
        return do_trong_anh(Image.open(os.path.join(tmp, anh[0])))


def do_trong_anh(im):
    """Diem 'do dam': R cao han han G va B. Nguong chon de muc den va giay ngA deu truot."""
    im = im.convert("RGB")
    im.thumbnail((700, 700))
    px = im.load()
    w, h = im.size
    n = 0
    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y]
            if r > 110 and r - g > 55 and r - b > 55:
                n += 1
    return n / float(w * h)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mau", type=int, default=120)
    ap.add_argument("--dau", type=int, default=40)
    a = ap.parse_args()
    random.seed(SEED)

    kho = liet_ke()
    tong = sum(len(v) for v in kho.values())
    print("== KHO VAN BAN ==")
    for k, v in kho.items():
        print("  %-20s %5d PDF" % (k, len(v)))
    print("  %-20s %5d PDF" % ("TONG", tong))
    if not tong:
        sys.exit("khong thay PDF nao")

    tat_ca = [p for v in kho.values() for p in v]
    mau = random.sample(tat_ca, min(a.mau, tong))
    print("\n== 1. QUET hay SINH SO (mau n=%d, seed=%d) ==" % (len(mau), SEED))
    dem = collections.Counter()
    quet, sinh_so = [], []
    for p in mau:
        c = co_chu(p)
        if c is None:
            dem["khong mo duoc"] += 1
        elif c:
            dem["sinh so"] += 1; sinh_so.append(p)
        else:
            dem["quet"] += 1; quet.append(p)
    for k, v in dem.most_common():
        print("  %-16s %4d  (%.1f%%)" % (k, v, 100.0 * v / len(mau)))

    print("\n== 2. DAU DO tren trang 1 ==")
    from PIL import Image
    for ten, tap in (("QUET", quet), ("SINH SO", sinh_so)):
        lay = tap[:a.dau]
        if not lay:
            print("  %-8s khong co mau" % ten); continue
        tl = [x for x in (ti_le_do(p) for p in lay) if x is not None]
        if not tl:
            print("  %-8s khong dung duoc anh" % ten); continue
        co = sum(1 for x in tl if x > 0.0015)
        tl.sort()
        print("  %-8s n=%3d  co dau do: %3d (%.0f%%)  trung vi ti le do: %.5f"
              % (ten, len(tl), co, 100.0 * co / len(tl), tl[len(tl) // 2]))

    print("\n== 3. DOI CHUNG AM ==")
    xam = Image.new("RGB", (300, 300), (128, 128, 128))
    r1 = do_trong_anh(xam)
    print("  anh xam thuan (phai = 0,00000): %.5f  %s" % (r1, "DAT" if r1 == 0 else "HONG"))
    do_tinh = Image.new("RGB", (300, 300), (200, 40, 40))
    r2 = do_trong_anh(do_tinh)
    print("  anh do thuan (phai = 1,00000): %.5f  %s" % (r2, "DAT" if r2 > 0.99 else "HONG"))
    return 0 if (r1 == 0 and r2 > 0.99) else 1


if __name__ == "__main__":
    sys.exit(main())
