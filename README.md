# When the Text Layer Lies — measurement code and results

Code and derived results for the study *When the Text Layer Lies: Stale Embedded OCR in an
Operational Administrative Archive*.

The study asks what happens when a document pipeline applies the usual rule, *if the PDF already
reports text, skip OCR*, to a real operational archive of 5 048 files. Every number and every
figure in the paper is produced by a script in this repository; none is typed by hand.

## What is here, and what is not

| | |
|---|---|
| `code/` | experiment drivers, the number generator, the figure generators, and the manuscript gate |
| `do/` | the primitive measurements over the archive |
| `results/` | raw logs, the per-document classification table, the generated LaTeX macros and tables |
| `figures/` | every figure in the paper, plus the TikZ sources and the shared style file |

**Not here: the archive itself.** The 5 048 PDFs are the operational document store of a single
institution and are not ours to redistribute. The scripts in `do/` read them from a directory
configured at the top of `do/do_lop_chu.py`; everything downstream of
`results/toan-kho.csv` runs without them.

## Reproducing the numbers

`results/toan-kho.csv` is the one artefact derived directly from the PDFs: one row per file,
carrying its text-layer classification, diacritic ratio, PDF producer and `/ToUnicode` status.
With that file present, the whole analysis re-runs without the archive:

```bash
pip install -r requirements.txt

python3 code/make_claims.py          # every macro and three tables, from toan-kho.csv + logs
python3 code/e6_e7_nguong.py         # rho distribution and the threshold sweep   -> F1, F2
python3 code/e11_e12_phan_tang.py    # stratification by document type            -> F5
python3 code/f6_hinh_truong.py       # per-field recovery                         -> F6
python3 code/f12_f16_hinh_luong.py   # the flow figures and the break-even curve  -> F12..F16
```

Three experiments re-read the page images and therefore need the archive: `e8_bo_do.py`
(detector scores against image-derived labels), `e9_quet_dpi.py` (resolution sweep), and
`e10_bon_truong.py` / `e15_ba_nhanh.py` (paired field recovery). Their outputs are checked in
under `results/` so that the figures and tables can be rebuilt without them.

### One redaction, and what it does not cost

The filenames in `results/toan-kho.csv` are the archive's own, and the filing convention encodes
the ground truth in them: `<number>_<type>_<year>_<issuer>`. That prefix is kept, because every
field-recovery number in the paper is measured against it. What is removed is the free-text
subject line some filenames carry after the prefix, since those describe the business of a named
institution and are not ours to publish; filenames that do not follow the convention are replaced
by a short hash of themselves. The redaction is performed by `code/lam_sach_csv.py`, which
refuses to write unless the filing-convention match is bit-identical before and after, every
other column is unchanged cell by cell, and the class distribution is preserved.

It costs nothing in reproducibility. Running `make_claims.py` on the redacted table reproduces
all 59 generated macros exactly, and the four figure generators that do not need the page images
rebuild every figure they own.

## How the results are checked

Each script carries its own assertions and **refuses to write output when one fails**. Beyond
that there are two whole-manuscript checks:

```bash
python3 code/cong_bai.py   # 41 checks over the built PDF and its sources
python3 code/tiem_loi.py   # injects 18 real defects and asserts each is caught
```

`cong_bai.py` rebuilds the manuscript from clean, then checks, among other things, that every
figure and table is referred to in the prose, that no page is left carrying only floats, that no
in-figure text falls below 6 pt once scaled, that every quantity in the text is a generated macro
rather than a typed number, and that the algebra of each proposition recomputes to the value the
manuscript prints. `tiem_loi.py` exists because a gate that has only ever been green proves
nothing: it injects a real defect for each check and fails if the check that should catch it does
not.

Two planned analyses were withdrawn after their own controls showed they could not support a
conclusion. Their code is kept here (`code/e11_e12_phan_tang.py` for the stratification by year,
`code/e13_mo_hinh_chu_so.py` for the closed-form digit model) so that the withdrawal can be
checked rather than taken on trust.

## Checking this repository for leaked record metadata

Before each push the tree is scanned for strings shaped like a document subject line
(`[a-z]+(-[a-z]+){4,}`). One known false positive is expected and is not data: the filename
`4-title-page-with-author-details.pdf` inside `build-submit.sh`. Any other hit should be treated
as a real leak until shown otherwise.

## Language

Code comments and internal documentation are in Vietnamese; the figures, generated tables and the
manuscript are in English.

## Citation

Please cite the paper. Funding: Science and Technology Development Fund of The University of
Danang, project B2025-DN02-25.
