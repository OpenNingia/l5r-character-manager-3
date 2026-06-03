#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (C) 2014-2026 Daniele Simonetti
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
"""Dump untranslated strings from a Qt .ts file, or apply translations back.

Companion to update_translations.py and the `translate-ts` skill. It lets the
translation work happen as a reviewable {source: translation} JSON map instead
of hundreds of hand edits, and guarantees the .ts structure, placeholders and
markup survive intact.

  dump  <ts> [-o out.json]      write JSON {source: ""} for every UNtranslated
                                entry (deduped, in document order)
  apply <ts> <map.json>         fill untranslated entries whose source is a key
                                with a non-empty value; mark them finished

Guarantees / guard rails:
  * Only entries currently marked unfinished/empty are touched; finished
    translations are never overwritten.
  * apply is a targeted text edit: untouched <message> blocks stay byte-identical
    (clean git diffs). Only the matched <translation> slots change.
  * Keys/values are LITERAL text (XML entities decoded): write `<p>` and `"` in
    the JSON, not `&lt;p&gt;` / `&quot;`. apply re-escapes on the way in.
  * Placeholder safety: if a translation's %1/%2/... set differs from its source,
    that entry is SKIPPED and reported, never written.
  * Plural/numerus messages are skipped (can't be expressed as one string).

JSON map is keyed on <source> text; the same source in multiple contexts gets the
same translation (the right default for UI strings).
"""

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from xml.sax.saxutils import escape, unescape

# An unfinished translation slot, in the two shapes lupdate/pylupdate6 emit.
_UNFINISHED_RE = re.compile(
    r'<translation type="unfinished">\s*</translation>'
    r'|<translation type="unfinished"\s*/>'
)
_MESSAGE_RE = re.compile(r"<message[^>]*>.*?</message>", re.DOTALL)
_SOURCE_RE = re.compile(r"<source>(.*?)</source>", re.DOTALL)
_NUMERIC_ENTITY_RE = re.compile(r"&#(\d+);")
_PLACEHOLDER_RE = re.compile(r"%L?\d+")

_EXTRA_UNESCAPE = {"&quot;": '"', "&apos;": "'"}
_EXTRA_ESCAPE = {'"': "&quot;"}


def _unescape(text):
    text = unescape(text, _EXTRA_UNESCAPE)
    return _NUMERIC_ENTITY_RE.sub(lambda m: chr(int(m.group(1))), text)


def _escape(text):
    return escape(text, _EXTRA_ESCAPE)


def _is_unfinished(block):
    return bool(_UNFINISHED_RE.search(block))


def _source_of(block):
    m = _SOURCE_RE.search(block)
    return _unescape(m.group(1)) if m else None


def cmd_dump(args):
    text = Path(args.ts).read_text(encoding="utf-8")
    seen, sources = set(), []
    for block in _MESSAGE_RE.findall(text):
        if not _is_unfinished(block):
            continue
        src = _source_of(block)
        if src is None or src in seen:
            continue
        seen.add(src)
        sources.append(src)
    payload = {src: "" for src in sources}
    out = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        Path(args.out).write_text(out, encoding="utf-8")
        print(f"wrote {len(sources)} untranslated source(s) to {args.out}")
    else:
        sys.stdout.write(out)


def cmd_apply(args):
    mapping = json.loads(Path(args.map).read_text(encoding="utf-8"))
    text = Path(args.ts).read_text(encoding="utf-8")

    skipped_ph = []  # sources skipped because their placeholder set differs
    stats = Counter()

    def repl(match):
        block = match.group(0)
        if not _is_unfinished(block):
            return block
        src = _source_of(block)
        translation = mapping.get(src, "")
        if not (translation and translation.strip()):
            stats["left"] += 1
            return block
        if Counter(_PLACEHOLDER_RE.findall(src)) != Counter(_PLACEHOLDER_RE.findall(translation)):
            if src not in skipped_ph:
                skipped_ph.append(src)
            stats["skipped"] += 1
            return block
        stats["filled"] += 1
        new_tr = f"<translation>{_escape(translation)}</translation>"
        return _UNFINISHED_RE.sub(lambda _m: new_tr, block, count=1)

    new_text = _MESSAGE_RE.sub(repl, text)
    # Force LF: these .ts are LF-origin (lupdate on Linux). Writing with the
    # platform default would rewrite every line to CRLF on Windows and produce a
    # whole-file diff. newline="\n" keeps untouched <message> blocks byte-identical.
    Path(args.ts).write_text(new_text, encoding="utf-8", newline="\n")

    print(f"{args.ts}: filled {stats['filled']}, still untranslated {stats['left']}, "
          f"skipped (placeholder mismatch) {stats['skipped']} "
          f"in {len(skipped_ph)} unique source(s)")
    for src in skipped_ph:
        print(f"  ! placeholder mismatch, left untranslated: {src!r}")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Dump/apply translations for a Qt .ts file.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest="command", required=True)
    d = sub.add_parser("dump", help="write JSON {source: ''} of untranslated entries")
    d.add_argument("ts", help="path to the .ts file")
    d.add_argument("-o", "--out", help="output JSON path (default: stdout)")
    a = sub.add_parser("apply", help="fill untranslated entries from a JSON map")
    a.add_argument("ts", help="path to the .ts file")
    a.add_argument("map", help="path to the {source: translation} JSON map")

    args = parser.parse_args(argv)
    {"dump": cmd_dump, "apply": cmd_apply}[args.command](args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
