# -*- coding: utf-8 -*-
"""Tests for DatapackProxy's catalogue<->installed matching.

The official datapack repo is internally inconsistent: some manifest ids
keep the ``_pack`` suffix the filename has (``great_clan_pack``), one drops
a ``_data_pack`` (``community`` vs ``community_data_pack``), and ``LBS`` is
upper-case while its asset is ``lbs_pack``. _norm_key must canonicalise both
sides so an installed pack is recognised in the catalogue (otherwise the
row keeps the "Install" button enabled even when installed -- the bug this
guards against).
"""
__author__ = 'Daniele Simonetti'

import unittest

from l5r.qmlui.proxies.datapack_proxy import _norm_key


class TestNormKey(unittest.TestCase):

    # (catalogue asset filename, manifest id) pairs that MUST collide.
    CASES = [
        ("core_pack-5.0.l5rcmpack", "core"),
        ("book_of_air_pack-1.2.l5rcmpack", "book_of_air"),
        ("community_data_pack-1.3.l5rcmpack", "community"),
        ("emerald_empire_pack-1.2.l5rcmpack", "emerald_empire_pack"),
        ("great_clan_pack-1.6.l5rcmpack", "great_clan_pack"),
        ("imperial_histories_pack-1.1.l5rcmpack", "imperial_histories"),
        ("lbs_pack-1.2.l5rcmpack", "LBS"),
        ("strongholds_pack-1.2.l5rcmpack", "strongholds"),
    ]

    def test_asset_matches_installed_id(self):
        for asset, pack_id in self.CASES:
            self.assertEqual(
                _norm_key(asset), _norm_key(pack_id),
                msg="asset %r should match id %r" % (asset, pack_id))

    def test_distinct_packs_do_not_collide(self):
        keys = {_norm_key(asset) for asset, _ in self.CASES}
        self.assertEqual(len(keys), len(self.CASES))

    def test_strips_version_and_suffix(self):
        self.assertEqual("strongholds",
                         _norm_key("strongholds_pack-1.2.l5rcmpack"))
        self.assertEqual("strongholds", _norm_key("strongholds.zip"))


if __name__ == "__main__":
    unittest.main()
