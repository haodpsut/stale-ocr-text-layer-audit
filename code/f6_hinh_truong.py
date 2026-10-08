#!/usr/bin/env python3
"""F6: hinh ket qua chinh, phuc hoi theo LOAI TRUONG.  python3 code/f6_hinh_truong.py

Doc thang tu `results/e10.log` de khong go tay mot con so nao. Ve hai cot cho moi truong
(lop chu nhung san vs OCR hien dai) kem khoang tin cay Wilson, xep theo do dai tu vung cua
truong, vi chinh THU TU ay la luan diem: truong tu vung dai mien nhiem, truong ngan dang so
thi bang khong.

TU KIEM: phai boc du 3 truong; va thu tu do duoc phai dung chieu (co quan > ngay > so hieu),
neu khong thi luan diem co che khong con dung va hinh KHONG duoc ve.
"""
import io, os, re, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import txstyle as TX   # bo style cua nha

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES, FIG = os.path.join(GOC, "results"), os.path.join(GOC, "figures")
loi = []


def kiem(dk, ten, ct=""):
    if not dk:
        loi.append(ten)
    print("  %s %s%s" % ("DAT " if dk else "HONG", ten, ("  [" + ct + "]") if ct else ""))


def main():
    t = io.open(os.path.join(RES, "e10.log"), encoding="utf-8").read()
    ten_en = {"co quan": "Issuing body\n(long lexical)",
              "ngay": "Issue date\n(mixed)",
              "so hieu": "Document number\n(short numeric)"}
    thu_tu = ["co quan", "ngay", "so hieu"]
    d = {}
    for ten in thu_tu:
        m = re.search(r"^\s+%s\s+(\d+)\s+(\d+)\s*\(\s*([\d.]+)%%\)\s+(\d+)\s*\(\s*([\d.]+)%%\)"
                      % ten, t, re.M)
        m2 = re.search(r"^\s+%s\s+\d+.*?\n\s+\[([\d.]+),\s*([\d.]+)\]\s+\[([\d.]+),\s*([\d.]+)\]"
                       % ten, t, re.M | re.S)
        if m:
            d[ten] = {"n": int(m.group(1)), "a": float(m.group(3)), "b": float(m.group(5)),
                      "ci": [float(x) for x in m2.groups()] if m2 else None}
    print("== F6: hinh phuc hoi theo loai truong ==")
    kiem(len(d) == 3, "boc du 3 truong tu e10.log", "%d" % len(d))
    if len(d) < 3:
        return 1
    a = [d[k]["a"] for k in thu_tu]
    kiem(a[0] > a[1] > a[2], "thu tu do duoc dung chieu: co quan > ngay > so hieu",
         "%.1f > %.1f > %.1f" % tuple(a))
    if loi:
        print("=> CHUA DAT, KHONG ve hinh")
        for x in loi:
            print("   loi: " + x)
        return 1

    b = [d[k]["b"] for k in thu_tu]
    y = np.arange(len(thu_tu))
    h = 0.36
    fig, ax = plt.subplots(figsize=(5.6, 2.9))
    tenA, mauA, _, _, hA = TX.NHANH["A"]
    tenB, mauB, _, _, hB = TX.NHANH["B"]
    ax.barh(y + h / 2, a, height=h, color=mauA, hatch="/", edgecolor="white",
            linewidth=0.5, label=tenA)
    ax.barh(y - h / 2, b, height=h, color=mauB, hatch=".", edgecolor="white",
            linewidth=0.5, label=tenB)
    for i, k in enumerate(thu_tu):
        ci = d[k]["ci"]
        if ci:
            ax.plot([ci[0], ci[1]], [y[i] + h / 2] * 2, color="black", lw=0.8, alpha=0.75,
                    marker="|", ms=4)
            ax.plot([ci[2], ci[3]], [y[i] - h / 2] * 2, color="black", lw=0.8, alpha=0.75,
                    marker="|", ms=4)
    ax.set_yticks(y)
    ax.set_yticklabels([ten_en[k] for k in thu_tu], fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("field recovered correctly (%)")
    ax.set_xlim(0, 118)
    ax.legend(loc="lower right")
    TX.grid_mo(ax, "x")
    # ⛔ ban dau dat nhan o CUOI THANH, no de len thanh khoang tin cay. Nay dat sau MUT PHAI
    # cua khoang tin cay, tuc sau ca hai thu.
    for i, k in enumerate(thu_tu):
        ci = d[k]["ci"] or [d[k]["a"]] * 2 + [d[k]["b"]] * 2
        ax.text(max(d[k]["a"], ci[1]) + 2.0, y[i] + h / 2, "%.1f" % d[k]["a"],
                va="center", fontsize=7.5, color=mauA)
        ax.text(max(d[k]["b"], ci[3]) + 2.0, y[i] - h / 2, "%.1f" % d[k]["b"],
                va="center", fontsize=7.5, color=mauB)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "f6-truong.pdf"))
    plt.close(fig)
    print("  da sinh F6: co quan %.1f/%.1f · ngay %.1f/%.1f · so hieu %.1f/%.1f"
          % (a[0], b[0], a[1], b[1], a[2], b[2]))
    print("=> DAT")
    return 0


if __name__ == "__main__":
    sys.exit(main())
