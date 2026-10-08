#!/usr/bin/env python3
"""Bo style HINH KET QUA cua nha, cho bai nay.  `import txstyle` truoc khi ve.

Chep quy uoc tu `paper-lab/transaction-figure-kit/results/make_results.py`, KHONG che lai:
  - phan biet series bang MAU + MARKER + KIEU NET, doc duoc khi in den trang
  - bang mau Okabe-Ito an toan cho nguoi mu mau; cot them hatch
  - truc manh, bo gai tren/phai, tick huong vao, grid mo hoac khong
  - phong serif khop than bai, xuat PDF vector, font nhung Type-42

⛔ Vi sao co tep nay: ngay 08/10 toi ve 5 hinh moi bang quy uoc TU NGHI RA (bon ho mau,
bo goc 2pt, to do/xanh la theo nghia tot/xau). Day la lan THU HAI mac dung loi ay; lan dau
27/08 o bai IoT-70170 va da ghi vao so. Bo cua nha nam o
`paper-lab/transaction-figure-kit/`, doc truoc khi ve bat cu hinh nao.

MOT MAU NHAN cho ca bai: accent = Okabe-Ito vermillion, danh cho thu bai NOI VE, tuc lop
chu hong va sai im lang. Moi thu khac la xam.
"""
import matplotlib as mpl

mpl.rcParams.update({
    "font.family": "serif",
    "font.serif": ["DejaVu Serif"],
    "mathtext.fontset": "dejavuserif",
    "font.size": 9,
    "axes.titlesize": 9,
    "axes.labelsize": 9,
    "legend.fontsize": 8,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "axes.linewidth": 0.6,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "xtick.direction": "in",
    "ytick.direction": "in",
    "xtick.major.width": 0.6,
    "ytick.major.width": 0.6,
    "lines.linewidth": 1.1,
    "lines.markersize": 4.5,
    "legend.frameon": False,
    "figure.dpi": 130,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})

# Okabe-Ito, dung y nguyen ten khoa cua kit
C = {"blue": "#0072B2", "verm": "#D55E00", "green": "#009E73",
     "gray": "#555555", "orange": "#E69F00", "sky": "#56B4E9"}

ACCENT = C["verm"]     # mau nhan DUY NHAT cua bai: lop chu hong / sai im lang
NEUTRAL = C["gray"]
SECOND = C["blue"]     # nhanh doc thu hai: OCR lai

# Hai nhanh doc, dung chung o moi hinh co hai nhanh
NHANH = {
    "A": ("embedded text layer", ACCENT, "o", "-", "//"),
    "B": ("re-OCR of the same page", SECOND, "s", "--", ".."),
}


def luu(fig, duong_dan):
    fig.savefig(duong_dan, bbox_inches="tight", pad_inches=0.02)


def grid_mo(ax, truc="y"):
    ax.grid(axis=truc, color="black", alpha=0.12, lw=0.5)
    ax.set_axisbelow(True)
