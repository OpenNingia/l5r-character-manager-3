# -*- coding: utf-8 -*-
# Tests for l5r.util.section_visibility (the per-character hidden-section
# store). The store path is redirected to a temp file -- no real config dir.
__author__ = 'Daniele Simonetti'

import os
import tempfile
import unittest
from unittest import mock

from l5r.util import section_visibility as sv


class TestSectionVisibility(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self._store = os.path.join(self._dir.name, "section_visibility.json")
        patcher = mock.patch.object(sv, "_store_path", return_value=self._store)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self._dir.cleanup)

    def test_roundtrip(self):
        sv.store("hero.l5r", {"kiho", "spells"})
        self.assertEqual(sv.load("hero.l5r"), {"kiho", "spells"})

    def test_load_absent_is_empty(self):
        # No store file written yet.
        self.assertEqual(sv.load("hero.l5r"), set())

    def test_empty_set_drops_key(self):
        sv.store("hero.l5r", {"kiho"})
        sv.store("hero.l5r", set())
        self.assertEqual(sv.load("hero.l5r"), set())
        # Key removed entirely rather than left as an empty list.
        self.assertNotIn(sv._key("hero.l5r"), sv._read_map())

    def test_empty_path_is_noop(self):
        # A never-saved character can't be keyed: store is a no-op and
        # load returns empty without touching disk.
        sv.store("", {"kiho"})
        self.assertFalse(os.path.exists(self._store))
        self.assertEqual(sv.load(""), set())

    def test_distinct_paths_distinct_keys(self):
        sv.store("a.l5r", {"kiho"})
        sv.store("b.l5r", {"spells"})
        self.assertEqual(sv.load("a.l5r"), {"kiho"})
        self.assertEqual(sv.load("b.l5r"), {"spells"})

    def test_key_is_path_normalised(self):
        # Same file via different spellings hashes to the same key.
        self.assertEqual(
            sv._key("./sub/../hero.l5r"),
            sv._key("hero.l5r"),
        )


if __name__ == "__main__":
    unittest.main()
