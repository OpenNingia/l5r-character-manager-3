#!/usr/bin/env python3
"""Finalize l5r/share/l5rcm/sheet_courtier.pdf form-field names.

The courtier character sheet ships with a half-finished AcroForm: the left
column (school 0) is correctly named with the ``COURTIER_SCHOOL_*`` scheme,
but the right column (school 1) is full of auto-generated junk field names
(``1_47``, ``2_46``, ``bo3``, ``EFFECT_32``, ``undefined_33`` ...) that no
exporter can target. This breaks PDF export onto the dedicated sheet, which is
why courtiers are currently rendered onto ``sheet_bushi.pdf`` instead
(see OpenNingia/l5r-character-manager-3#385).

The form is completely FLAT (every field is a top-level widget whose ``/T``
holds the full dotted name -- no /Parent, /Kids or /TM), so finalizing it is
just rewriting ``/T`` (and, for the merge step, ``/Rect`` + ``/Ff``).

What it does
------------
1. *Canonicalize positionally.* The right-column widgets are matched, by their
   vertical position, to the correctly-named left-column widgets and given the
   same logical slot with the school index switched 0 -> 1. This repairs both
   the junk names and the right-column widgets that were sitting on the wrong row.
2. *Merge EFFECT lines (default).* The six single-line ``EFFECT.i.r.{0..5}``
   boxes per rank are collapsed into ONE multiline text field spanning the same
   area -- exactly like ``BUSHI_TECH_TEXT`` on the bushi sheet -- so the PDF
   handles word-wrap (fixes the "description runs off the page" bug, #387).
3. *Emit a naming scheme.*
     --scheme bushi    (default)  BUSHI_SCHOOL_NM.i / BUSHI_TECH.r.i /
                                  BUSHI_TECH_TEXT.r.i  -> matches the EXISTING
                                  FDFExporterCourtier, so no exporter code change
                                  is needed (only point l5rcmcore back to
                                  'sheet_courtier.pdf').
     --scheme courtier            COURTIER_SCHOOL_NM.i / COURTIER_SCHOOL_RANK.i.r
                                  / COURTIER_SCHOOL_EFFECT.i.r -> requires
                                  adapting FDFExporterCourtier to these names.

Usage
-----
    python tools/finalize_courtier_sheet.py --dry-run
    python tools/finalize_courtier_sheet.py                 # -> *_fixed.pdf
    python tools/finalize_courtier_sheet.py --scheme courtier --no-merge
    python tools/finalize_courtier_sheet.py --inplace
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from collections import defaultdict

import pikepdf

DEFAULT_PDF = os.path.join("l5r", "share", "l5rcm", "sheet_courtier.pdf")

COLUMN_SPLIT_X = 210.0   # x-centre splitting left (school 0) / right (school 1)
Y_TOLERANCE = 6.0        # max vertical gap to call two widgets "same row"
FF_MULTILINE = 1 << 12   # AcroForm field flag bit 13

# Horizontal span (pt) of the printed ruling lines in each school's EFFECT
# column, measured from the sheet's background raster. The lines are slightly
# wider than the form-field widgets, and the right column's lines run past the
# field edge (to ~399.6) but stop just short of the adjacent NOTES section
# (which starts at ~401.8), so the white cover is capped at 400 to avoid it.
EFFECT_COVER_X = {0: (36.0, 202.0), 1: (216.0, 400.0)}


def y_centre(r):
    return (float(r[1]) + float(r[3])) / 2.0


def x_centre(r):
    return (float(r[0]) + float(r[2])) / 2.0


def school1(name0):
    p = name0.split(".")
    p[1] = "1"
    return ".".join(p)


_CANON = re.compile(
    r"^COURTIER_SCHOOL_(NM|RANK|EFFECT)\.(\d+)(?:\.(\d+))?(?:\.(\d+))?$")


def parse_canonical(name):
    """'COURTIER_SCHOOL_EFFECT.1.2.3' -> ('EFFECT', 1, 2, 3)"""
    m = _CANON.match(name)
    if not m:
        return None
    kind = m.group(1)
    i = int(m.group(2))
    r = int(m.group(3)) if m.group(3) is not None else None
    l = int(m.group(4)) if m.group(4) is not None else None
    return kind, i, r, l


def emit(scheme, kind, i, r, l):
    if scheme == "courtier":
        if kind == "NM":
            return f"COURTIER_SCHOOL_NM.{i}"
        if kind == "RANK":
            return f"COURTIER_SCHOOL_RANK.{i}.{r}"
        # EFFECT: merged drops the line index
        return (f"COURTIER_SCHOOL_EFFECT.{i}.{r}" if l is None
                else f"COURTIER_SCHOOL_EFFECT.{i}.{r}.{l}")
    # bushi scheme -- matches FDFExporterCourtier's emitted field names
    if kind == "NM":
        return f"BUSHI_SCHOOL_NM.{i}"
    if kind == "RANK":
        return f"BUSHI_TECH.{r}.{i}"
    return f"BUSHI_TECH_TEXT.{r}.{i}"


def canonicalize(pdf):
    """Return {objgen: (field, canonical_name)} plus diagnostics."""
    left = {}          # round(y) -> (y, name0)
    left_bad = []
    rights = []        # (field, name, y, objgen)
    canon = {}

    for f in pdf.Root.AcroForm.Fields:
        name = str(f.T) if "/T" in f else None
        rect = list(f.Rect) if "/Rect" in f else None
        if rect is None or name is None:
            rights.append((f, name, None, f.objgen))
            continue
        if x_centre(rect) < COLUMN_SPLIT_X:
            if name.startswith("COURTIER_SCHOOL_") and name.split(".")[1:2] == ["0"]:
                left[round(y_centre(rect), 1)] = (y_centre(rect), name)
                canon[f.objgen] = (f, name)
            else:
                left_bad.append(name)
        else:
            rights.append((f, name, y_centre(rect), f.objgen))

    unmatched = []
    for f, name, yc, og in rights:
        if yc is None:
            unmatched.append(name)
            continue
        best, best_d = None, Y_TOLERANCE
        for _, (lyc, lname) in left.items():
            d = abs(lyc - yc)
            if d < best_d:
                best_d, best = d, lname
        if best is None:
            unmatched.append((name, round(yc, 1)))
        else:
            canon[og] = (f, school1(best))

    by_name = defaultdict(list)
    for og, (f, n) in canon.items():
        by_name[n].append(og)
    collisions = {n: v for n, v in by_name.items() if len(v) > 1}
    return canon, unmatched, left_bad, collisions


def union_rect(rects):
    xs0 = [float(r[0]) for r in rects]
    ys0 = [float(r[1]) for r in rects]
    xs1 = [float(r[2]) for r in rects]
    ys1 = [float(r[3]) for r in rects]
    return [min(xs0), min(ys0), max(xs1), max(ys1)]


def apply(pdf, canon, scheme, merge):
    delete = set()                       # objgens to drop
    effect_groups = defaultdict(list)    # (i, r) -> [(line, field)]
    effect_rects = []                    # union rects of the merged EFFECT fields

    def rename(field, new):
        field.T = pikepdf.String(new)
        # the source sheet mirrors the field name into /TU (tooltip / alternate
        # name); keep them in sync so editors that display /TU don't show stale
        # names like 'EFFECT_32'.
        field.TU = pikepdf.String(new)

    for og, (f, cname) in canon.items():
        kind, i, r, l = parse_canonical(cname)
        if kind == "EFFECT" and merge:
            effect_groups[(i, r)].append((l, f))
        else:
            rename(f, emit(scheme, kind, i, r, l))

    for (i, r), items in effect_groups.items():
        items.sort(key=lambda t: t[0])           # by line index
        keeper = items[0][1]                      # line 0 (topmost)
        rects = [list(f.Rect) for _, f in items]
        u = union_rect(rects)
        effect_rects.append(u)
        keeper.Rect = pikepdf.Array([round(v, 2) for v in u])
        keeper.Ff = int(keeper.get("/Ff", 0)) | FF_MULTILINE
        if "/AP" in keeper:
            del keeper.AP                          # regenerate appearance at new size
        rename(keeper, emit(scheme, "EFFECT", i, r, None))
        for _, f in items[1:]:
            delete.add(f.objgen)

    if delete:
        pdf.Root.AcroForm.Fields = pikepdf.Array(
            [f for f in pdf.Root.AcroForm.Fields if f.objgen not in delete])
        for page in pdf.pages:
            if "/Annots" in page:
                page.Annots = pikepdf.Array(
                    [a for a in page.Annots if a.objgen not in delete])
        pdf.Root.AcroForm.NeedAppearances = True
    return len(delete), effect_rects


def cover_effect_rules(pdf, rects):
    """Paint an opaque white rectangle over each merged EFFECT region.

    The page-background ruling lines are baked into the /Im0 raster image, so
    they cannot be removed as vector operators. The sheet background is pure
    white, so painting white rectangles over the (now merged) EFFECT areas
    hides the rules invisibly. Field text renders above page content, so the
    wrapped technique description stays on top and legible.
    """
    if not rects:
        return 0
    parts = ["q 1 1 1 rg"]
    for x0, y0, x1, y1 in rects:
        # widen to the column's full ruling-line span (the field widget is
        # narrower than the printed lines, especially in the right column).
        school = 0 if (x0 + x1) / 2 < COLUMN_SPLIT_X else 1
        cx0, cx1 = EFFECT_COVER_X[school]
        parts.append(f"{cx0:.2f} {y0:.2f} {cx1 - cx0:.2f} {y1 - y0:.2f} re")
    parts.append("f Q")
    blob = ("\n" + "\n".join(parts) + "\n").encode("latin-1")
    # all form fields live on page 0 in this sheet; the white fill is appended
    # after the image Do, in default user space (the image's cm is balanced by
    # its own q/Q).
    pdf.pages[0].contents_add(blob, prepend=False)
    return len(rects)


def verify(path, scheme):
    pdf = pikepdf.open(path)
    names = sorted(str(f.T) for f in pdf.Root.AcroForm.Fields if "/T" in f)
    prefix = "BUSHI_" if scheme == "bushi" else "COURTIER_"
    good = [n for n in names if n.startswith(prefix)]
    bad = [n for n in names if not n.startswith(prefix)]
    ml = 0
    stale_tu = []
    for f in pdf.Root.AcroForm.Fields:
        if int(f.get("/Ff", 0)) & FF_MULTILINE:
            ml += 1
        tu = str(f.get("/TU")) if "/TU" in f else None
        if tu is not None and not tu.startswith(prefix):
            stale_tu.append((str(f.get("/T", "")), tu))
    print(f"  verify: {len(names)} fields | {prefix}*={len(good)} | other={len(bad)} | "
          f"multiline={ml} | stale /TU={len(stale_tu)}")
    if bad:
        print("  NON-SCHEME /T:", bad)
    if stale_tu:
        print("  STALE /TU:", stale_tu)
    print("  fields:", names)
    return not bad and not stale_tu


def main(argv=None):
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf", nargs="?", default=DEFAULT_PDF)
    ap.add_argument("-o", "--output")
    ap.add_argument("--scheme", choices=("bushi", "courtier"), default="bushi")
    ap.add_argument("--no-merge", dest="merge", action="store_false",
                    help="keep the 6 EFFECT lines (only valid with --scheme courtier)")
    ap.add_argument("--no-cover-rules", dest="cover_rules", action="store_false",
                    help="don't paint white over the EFFECT background ruling lines")
    ap.add_argument("--inplace", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args(argv)

    if args.scheme == "bushi" and not args.merge:
        ap.error("--scheme bushi requires merged EFFECT fields (drop --no-merge)")
    if not os.path.exists(args.pdf):
        ap.error(f"file not found: {args.pdf}")

    # allow_overwriting_input loads the file fully into memory so --inplace
    # (and -o pointing back at the source) can overwrite it.
    pdf = pikepdf.open(args.pdf, allow_overwriting_input=True)
    canon, unmatched, left_bad, collisions = canonicalize(pdf)

    print(f"source         : {args.pdf}")
    print(f"scheme         : {args.scheme}  (merge EFFECT = {args.merge})")
    print(f"fields mapped  : {len(canon)}")
    print(f"unmatched      : {len(unmatched)}")
    print(f"bad left-column: {len(left_bad)}")
    print(f"collisions     : {len(collisions)}")
    if unmatched:
        print("  UNMATCHED:", unmatched)
    if left_bad:
        print("  BAD LEFT  :", left_bad)
    if collisions:
        print("  COLLISIONS:", collisions)

    blocking = bool(unmatched or left_bad or collisions)
    if args.dry_run:
        print("[dry-run] computing target field set without writing...")
        # preview target names
        from collections import Counter
        prev = Counter()
        seen = set()
        for og, (f, cname) in canon.items():
            kind, i, r, l = parse_canonical(cname)
            if kind == "EFFECT" and args.merge:
                key = emit(args.scheme, "EFFECT", i, r, None)
            else:
                key = emit(args.scheme, kind, i, r, l)
            seen.add(key)
        print(f"  -> {len(seen)} unique target fields")
        for n in sorted(seen):
            print("    ", n)
        return 1 if blocking else 0

    if blocking and not args.force:
        print("ABORT: resolve issues above or use --force.", file=sys.stderr)
        return 1

    n_deleted, effect_rects = apply(pdf, canon, args.scheme, args.merge)
    n_covered = 0
    if args.merge and args.cover_rules:
        n_covered = cover_effect_rules(pdf, effect_rects)
    out = args.pdf if args.inplace else (
        args.output or os.path.splitext(args.pdf)[0] + "_fixed.pdf")
    pdf.save(out)
    print(f"merged-away fields: {n_deleted}")
    print(f"EFFECT areas whitened: {n_covered}")
    print(f"wrote: {out}")
    verify(out, args.scheme)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
