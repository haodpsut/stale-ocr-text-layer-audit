#!/usr/bin/env python3
"""Lam sach `results/toan-kho.csv` TRUOC KHI CONG KHAI.
    python3 code/lam_sach_csv.py --ra repo/results/toan-kho.csv

Cot `tep` dang mang TEN TEP THAT cua van ban hanh chinh noi bo cua mot truong CO TEN, va mot
so con kem TRICH YEU o duoi phan dau (dai khai `<so>_<loai>_<nam>_<coquan>_<trich-yeu-day-du>`).
Cong khai nguyen trang la cong bo sieu du lieu hanh chinh noi bo.

⛔ Va chinh tep nay tung la cho ro ri thu hai: ban dau toi viet hai TEN TEP THAT vao docstring
lam vi du. Bo che du lieu ma lai in du lieu ra trong chu thich cua chinh no. Vi du phai la
KHUON, khong duoc la ban ghi that.

Nhung bo PHAN DAU `<so>_<loai>_<nam>_<coquan>[_<dd-mm>]` CHINH LA VAN BAN CHUAN cua bai: moi
so ve phuc hoi truong deu do no sinh ra. Bo no di thi khong ai dung lai duoc ket qua nao.

Nen: GIU phan dau, CAT phan trich yeu. Tep khong theo quy uoc thi thay han bang mot bam ngan.

TU KIEM, script tu choi ghi neu mot phep hong:
  K1 so dong khong doi
  K2 voi MOI dong, khuon ten tep cho CUNG ket qua truoc va sau  (van ban chuan khong suy suyen)
  K3 khong ten tep nao con ky tu ngoai [0-9A-Za-z_-] truoc `.pdf`
  K4 phan bo theo `phan_loai` khong doi
  K5 moi cot KHAC `tep` khong doi, tung o mot
  K6 ten tep sau khi che van DUY NHAT (neu dung thi them hau to, va phai bao ra)
"""
import argparse, collections, csv, hashlib, io, os, re, sys

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KHUON = re.compile(r"^(\d{3,4})_([A-Z]{2,4})_(\d{4})_([A-Z]+)(?:_(\d{2})-(\d{2}))?", re.I)
SACH = re.compile(r"^[0-9A-Za-z_-]+\.pdf$")
loi = []


def kiem(dk, ten, ct=""):
    if not dk:
        loi.append(ten)
    print("  %s %s%s" % ("DAT " if dk else "HONG", ten, ("  [" + ct + "]") if ct else ""))


def che(ten):
    m = KHUON.match(ten)
    if m:
        giu = ten[m.start():m.end()]
        return giu + ".pdf"
    return "ngoai-" + hashlib.sha1(ten.encode("utf-8")).hexdigest()[:10] + ".pdf"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vao", default=os.path.join(GOC, "results", "toan-kho.csv"))
    ap.add_argument("--ra", default=os.path.join(GOC, "repo", "results", "toan-kho.csv"))
    a = ap.parse_args()
    with io.open(a.vao, encoding="utf-8") as f:
        r = csv.DictReader(f)
        cot = r.fieldnames
        hang = list(r)
    print("== LAM SACH CSV TRUOC KHI CONG KHAI ==")
    print("  vao: %s (%d dong)" % (a.vao, len(hang)))

    moi = []
    dem = collections.Counter()
    for h in hang:
        t = dict(h)
        t["tep"] = che(h["tep"])
        dem[t["tep"]] += 1
        if dem[t["tep"]] > 1:                      # trung sau khi che: them hau to
            t["tep"] = t["tep"][:-4] + "-%d.pdf" % dem[t["tep"]]
        moi.append(t)

    kiem(len(moi) == len(hang), "K1 so dong khong doi", "%d / %d" % (len(moi), len(hang)))

    lech = []
    for h, t in zip(hang, moi):
        a_, b_ = KHUON.match(h["tep"]), KHUON.match(t["tep"])
        ga = a_.groups() if a_ else None
        gb = b_.groups() if b_ else None
        if ga != gb:
            lech.append("%s -> %s" % (h["tep"][:40], t["tep"]))
    kiem(not lech, "K2 van ban chuan khong suy suyen o moi dong",
         "%d dong lech: %s" % (len(lech), "; ".join(lech[:3])))

    ban = [t["tep"] for t in moi if not SACH.match(t["tep"])]
    kiem(not ban, "K3 khong ten tep nao con ky tu la", ", ".join(ban[:3]))

    pa = collections.Counter(h["phan_loai"] for h in hang)
    pb = collections.Counter(t["phan_loai"] for t in moi)
    kiem(pa == pb, "K4 phan bo theo phan_loai khong doi", "%s vs %s" % (dict(pa), dict(pb)))

    khac = []
    for h, t in zip(hang, moi):
        for c in cot:
            if c != "tep" and h[c] != t[c]:
                khac.append("%s/%s" % (h["tep"][:24], c))
    kiem(not khac, "K5 moi cot khac `tep` khong doi", "%d o lech" % len(khac))

    trung = [k for k, v in collections.Counter(t["tep"] for t in moi).items() if v > 1]
    kiem(not trung, "K6 ten tep sau khi che van duy nhat", ", ".join(trung[:3]))
    n_hau_to = sum(1 for k, v in dem.items() if v > 1)
    if n_hau_to:
        print("  ⚠ %d ten bi trung sau khi che, da them hau to so" % n_hau_to)

    if loi:
        print("\n=> CHUA DAT, KHONG ghi (%d loi)" % len(loi))
        for x in loi:
            print("   loi: " + x)
        return 1

    os.makedirs(os.path.dirname(a.ra), exist_ok=True)
    with io.open(a.ra, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cot)
        w.writeheader()
        w.writerows(moi)
    n_khuon = sum(1 for t in moi if KHUON.match(t["tep"]))
    print("\n  da ghi %s" % a.ra)
    print("  %d/%d dong giu nguyen phan dau <so>_<loai>_<nam>_<coquan>, %d dong thay bang bam"
          % (n_khuon, len(moi), len(moi) - n_khuon))
    print("=> DAT")
    return 0


if __name__ == "__main__":
    sys.exit(main())
