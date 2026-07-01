# -*- coding: utf-8 -*-
# Contract tests for the QR transfer writer (l5r/exporters/qr_transfer.py).
#
# The authoritative cross-implementation contract is docs/QR_IMPORT_FORMAT.md;
# its §7 golden test vector is reproduced verbatim here. If the writer and the
# Android reader both pass this vector, they interoperate.

import base64
import gzip
import unittest
import zlib

from l5r.exporters import qr_transfer

# --- §7 golden test vector ------------------------------------------------
GOLDEN_PAYLOAD = (
    u'{"version":"4.0","char":{"name":"Doji Test","clan":"crane"},"advans":[]}')
GOLDEN_CRC = u"4c21ece1"
GOLDEN_B64 = (
    u"H4sIAAAAAAAC/6tWKkstKs7Mz1OyUjLRM1DSUUrOSCxSsqpWykvMTQUKuuRnZSqE"
    u"pBaXgKRyEkHqkosS81KVanWUElPKEvOKlayiY2sBLlLr40gAAAA=")
GOLDEN_FRAMES = [
    u"L5RQR1|7F3A|0|4|4c21ece1|H4sIAAAAAAAC/6tWKkstKs7Mz1OyUjLR",
    u"L5RQR1|7F3A|1|4|4c21ece1|M1DSUUrOSCxSsqpWykvMTQUKuuRnZSqE",
    u"L5RQR1|7F3A|2|4|4c21ece1|pBaXgKRyEkHqkosS81KVanWUElPKEvOK",
    u"L5RQR1|7F3A|3|4|4c21ece1|layiY2sBLlLr40gAAAA=",
]


def _decode(frames):
    """Reference reader: reassemble frames -> verify crc -> gunzip -> JSON."""
    magic, tid, _, total_s, crc, _ = frames[0].split(u"|", 5)
    assert magic == qr_transfer.MAGIC
    total = int(total_s)
    chunks = {}
    for fr in frames:
        f = fr.split(u"|", 5)
        assert f[0] == magic and f[1] == tid and f[3] == total_s and f[4] == crc
        chunks[int(f[2])] = f[5]
    b64 = u"".join(chunks[i] for i in range(total))
    blob = base64.b64decode(b64)
    assert format(zlib.crc32(blob) & 0xFFFFFFFF, u"08x") == crc
    return gzip.decompress(blob).decode(u"utf-8")


class TestQrTransferGoldenVector(unittest.TestCase):

    def test_frames_match_golden_vector(self):
        frames = qr_transfer.make_frames(
            GOLDEN_PAYLOAD, chunk_chars=32, transfer_id=u"7F3A")
        self.assertEqual(frames, GOLDEN_FRAMES)

    def test_b64_and_crc_match_golden_vector(self):
        # The data fields, concatenated in seq order, are the whole b64.
        data = u"".join(fr.split(u"|", 5)[5] for fr in GOLDEN_FRAMES)
        self.assertEqual(data, GOLDEN_B64)
        blob = base64.b64decode(GOLDEN_B64)
        self.assertEqual(format(zlib.crc32(blob) & 0xFFFFFFFF, u"08x"), GOLDEN_CRC)

    def test_roundtrip_reader_recovers_payload(self):
        frames = qr_transfer.make_frames(
            GOLDEN_PAYLOAD, chunk_chars=32, transfer_id=u"7F3A")
        self.assertEqual(_decode(frames), GOLDEN_PAYLOAD)


class TestQrTransferFraming(unittest.TestCase):

    def test_default_chunking_roundtrips_a_large_payload(self):
        # Incompressible content (random hex) so gzip can't crush it below
        # one chunk -- this exercises the multi-frame split + reassembly.
        import os
        payload = u'{"blob":"' + os.urandom(4000).hex() + u'"}'
        frames = qr_transfer.make_frames(payload)
        self.assertGreater(len(frames), 1)
        self.assertEqual(_decode(frames), payload)

    def test_frame_grammar_is_consistent_across_frames(self):
        frames = qr_transfer.make_frames(
            u'{"a":1}' * 500, chunk_chars=64, transfer_id=u"ABC123")
        total = len(frames)
        crc = frames[0].split(u"|", 5)[4]
        for seq, fr in enumerate(frames):
            magic, tid, s, tot, c, _ = fr.split(u"|", 5)
            self.assertEqual(magic, u"L5RQR1")
            self.assertEqual(tid, u"ABC123")
            self.assertEqual(int(s), seq)
            self.assertEqual(int(tot), total)
            self.assertEqual(c, crc)
            self.assertEqual(len(c), 8)

    def test_generated_transfer_id_shape(self):
        frames = qr_transfer.make_frames(u"{}")
        tid = frames[0].split(u"|", 5)[1]
        self.assertEqual(len(tid), qr_transfer._ID_LENGTH)
        self.assertTrue(all(ch in qr_transfer._ID_ALPHABET for ch in tid))

    def test_empty_payload_still_yields_one_frame(self):
        # gzip of "" is still a ~20-byte container, so this stays a single
        # well-formed frame that the reader recovers as "".
        frames = qr_transfer.make_frames(u"")
        self.assertEqual(len(frames), 1)
        self.assertEqual(_decode(frames), u"")


if __name__ == "__main__":
    unittest.main()
