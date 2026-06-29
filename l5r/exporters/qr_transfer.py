# -*- coding: utf-8 -*-
# Copyright (C) 2014-2026 Daniele Simonetti
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# QR transfer writer -- encodes a `.l5r` character save into a sequence of
# animated multi-frame QR codes that the Android companion app scans to
# import the character without a file transfer.
#
# This module is the *writer* half of the cross-implementation contract
# documented in docs/QR_IMPORT_FORMAT.md. It is the authoritative source:
# the doc's golden test vector is reproduced by test_qr_transfer.py. Keep
# this module pure (stdlib only, no Qt, no segno) so it stays trivially
# testable and so the contract logic is isolated from rendering -- the QR
# image rendering lives in l5r/qmlui/proxies/qr_image_provider.py.

import base64
import gzip
import json
import secrets
import string
import zlib

from l5r.models.chmodel import MyJsonEncoder

# Magic token + format version. The trailing "1" is the wire-format
# version; a reader must reject any other magic (see the spec, §9). Bump
# the version on any breaking change to the frame grammar.
MAGIC = u"L5RQR1"

# Base64 characters per frame. Kept deliberately small (~448) so each QR
# stays a low-version, low-density symbol a phone can focus on and decode
# quickly off a screen -- the bottleneck for animated transfer is per-frame
# scan reliability, not frame count. An 11 KB character (~3 KB gzip ~4 KB
# b64) becomes ~9 frames at this size. Tunable without touching the
# contract -- the reader concatenates all chunks first.
DEFAULT_CHUNK_CHARS = 448

# `id` alphabet/length: a short random transfer id lets the reader notice
# the user pointing the camera at a *different* character mid-scan. Spec
# recommendation: 6 uppercase base36 chars.
_ID_ALPHABET = string.ascii_uppercase + string.digits
_ID_LENGTH = 6


def serialize_character(pc):
    """Serialize a character model to the JSON payload carried over the wire.

    This is the same object graph `AdvancedPcModel.save_to` writes to a
    `.l5r` file (`MyJsonEncoder` -> each object's ``__dict__``), but
    *minified* -- no indentation, compact separators -- since gzip will
    compress it anyway and fewer pre-compression bytes means fewer frames.
    `ensure_ascii=False` keeps multi-byte names as UTF-8 (the wire is
    UTF-8 per the spec) rather than bloating them into ``\\uXXXX`` escapes.
    The companion's JSON parser is whitespace-agnostic, so the minified
    form is byte-for-byte equivalent character data.
    """
    return json.dumps(
        pc, cls=MyJsonEncoder, separators=(u",", u":"), ensure_ascii=False)


def _new_transfer_id():
    return u"".join(secrets.choice(_ID_ALPHABET) for _ in range(_ID_LENGTH))


def make_frames(json_text, chunk_chars=DEFAULT_CHUNK_CHARS, transfer_id=None):
    """Encode a JSON payload string into the list of QR frame strings.

    Pipeline (docs/QR_IMPORT_FORMAT.md §2): UTF-8 encode -> gzip -> Base64
    (standard alphabet, with padding) -> split into ``chunk_chars``-sized
    slices -> wrap each in ``MAGIC|id|seq|total|crc|data``. The CRC32 of
    the gzip blob is embedded identically in every frame so the reader can
    verify integrity after reassembly.

    gzip is pinned to ``mtime=0`` / ``compresslevel=9`` so the bytes are
    reproducible (the contract's golden test vector depends on it); the
    reader only ever decompresses, so the exact header bytes are immaterial
    to interop -- only to the test.
    """
    blob = gzip.compress(json_text.encode(u"utf-8"), compresslevel=9, mtime=0)
    b64 = base64.b64encode(blob).decode(u"ascii")
    crc = format(zlib.crc32(blob) & 0xFFFFFFFF, u"08x")
    tid = transfer_id or _new_transfer_id()

    chunks = [b64[i:i + chunk_chars]
              for i in range(0, len(b64), chunk_chars)] or [u""]
    total = len(chunks)
    return [u"{0}|{1}|{2}|{3}|{4}|{5}".format(MAGIC, tid, seq, total, crc, c)
            for seq, c in enumerate(chunks)]


def character_frames(pc, chunk_chars=DEFAULT_CHUNK_CHARS, transfer_id=None):
    """Convenience: serialize ``pc`` and encode it into QR frame strings."""
    return make_frames(
        serialize_character(pc), chunk_chars=chunk_chars,
        transfer_id=transfer_id)
