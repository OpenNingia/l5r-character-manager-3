# -*- coding: utf-8 -*-
"""Save -> load round-trip of the character model.

Regression guard for the bug where Rank advancements with pending choices
(skills_to_choose / merits / flaws) reloaded as plain dicts instead of typed
objects, crashing every redeem path that reads them by attribute.
"""

import os
import tempfile
import unittest

import l5rdal.school as dal_school

from l5r.models.chmodel import AdvancedPcModel
from l5r.models.advancements.rank import Rank
from l5r.models.advances import PerkAdv, SkillAdv

__author__ = 'Daniele Simonetti'


def _wildcard(value, modifier='or'):
    w = dal_school.SchoolSkillWildcard()
    w.value = value
    w.modifier = modifier
    return w


def _wildcard_set(rank, wildcards):
    s = dal_school.SchoolSkillWildcardSet()
    s.rank = rank
    s.wildcards = wildcards
    return s


class TestChModelRoundtrip(unittest.TestCase):

    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix='.l5r')
        os.close(fd)
        self.addCleanup(lambda: os.path.exists(self.path) and os.remove(self.path))

    def _save_and_reload(self, pc):
        self.assertTrue(pc.save_to(self.path))
        reloaded = AdvancedPcModel()
        self.assertTrue(reloaded.load_from(self.path))
        return reloaded

    def test_rank_is_rebuilt_as_rank(self):
        """A reloaded rank advancement is a real Rank, not a generic one."""
        pc = AdvancedPcModel()
        rank = Rank()
        rank.rank = 1
        rank.school = 'test_school'
        pc.add_advancement(rank)

        reloaded = self._save_and_reload(pc)

        self.assertEqual(1, len(reloaded.advans))
        self.assertIsInstance(reloaded.advans[0], Rank)
        self.assertEqual(1, reloaded.advans[0].rank)
        self.assertEqual('test_school', reloaded.advans[0].school)

    def test_skills_to_choose_survive_as_wildcard_sets(self):
        """skills_to_choose come back as SchoolSkillWildcardSet objects whose
        wildcards are SchoolSkillWildcard objects -- the shape the skill
        choosers read by attribute (the reported AttributeError)."""
        pc = AdvancedPcModel()
        rank = Rank()
        rank.rank = 1
        rank.skills_to_choose = [
            _wildcard_set(1, [_wildcard('high'), _wildcard('lore', 'not')]),
        ]
        pc.add_advancement(rank)

        reloaded = self._save_and_reload(pc)
        sets = reloaded.advans[0].skills_to_choose

        self.assertEqual(1, len(sets))
        wc_set = sets[0]
        self.assertIsInstance(wc_set, dal_school.SchoolSkillWildcardSet)
        # attribute access must work (this is exactly what used to crash)
        self.assertEqual(1, wc_set.rank)
        self.assertEqual(2, len(wc_set.wildcards))
        self.assertIsInstance(wc_set.wildcards[0], dal_school.SchoolSkillWildcard)
        self.assertEqual('high', wc_set.wildcards[0].value)
        self.assertEqual('or', wc_set.wildcards[0].modifier)
        self.assertEqual('lore', wc_set.wildcards[1].value)
        self.assertEqual('not', wc_set.wildcards[1].modifier)

    def test_starting_merits_and_flaws_survive_as_perkadvs(self):
        """merits/flaws nested on the first rank come back as PerkAdv objects
        (perks.py reads .cost / .perk / .rank by attribute)."""
        pc = AdvancedPcModel()
        rank = Rank()
        rank.rank = 1
        merit = PerkAdv('test_merit', 1, 3, 'merit')
        flaw = PerkAdv('test_flaw', 1, -2, 'flaw')
        rank.merits = [merit]
        rank.flaws = [flaw]
        pc.add_advancement(rank)

        reloaded = self._save_and_reload(pc)
        rrank = reloaded.advans[0]

        self.assertEqual(1, len(rrank.merits))
        self.assertEqual(1, len(rrank.flaws))
        self.assertEqual('test_merit', rrank.merits[0].perk)
        self.assertEqual(3, rrank.merits[0].cost)
        self.assertEqual('merit', rrank.merits[0].tag)
        self.assertEqual('test_flaw', rrank.flaws[0].perk)
        self.assertEqual(-2, rrank.flaws[0].cost)

    def test_spells_to_choose_restored_as_tuples(self):
        """spells_to_choose keep the (element, count, tag) tuple shape."""
        pc = AdvancedPcModel()
        rank = Rank()
        rank.rank = 2
        rank.spells_to_choose = [('fire', 1, 'attack')]
        pc.add_advancement(rank)

        reloaded = self._save_and_reload(pc)
        choices = reloaded.advans[0].spells_to_choose

        self.assertEqual([('fire', 1, 'attack')], choices)
        self.assertIsInstance(choices[0], tuple)

    def test_uuid_survives_roundtrip(self):
        """A character's stable uuid is preserved across save/load."""
        pc = AdvancedPcModel()
        pc.uuid = 'fixed-uuid-1234'
        reloaded = self._save_and_reload(pc)
        self.assertEqual('fixed-uuid-1234', reloaded.uuid)

    def test_legacy_save_without_uuid_loads_as_none(self):
        """A save predating the uuid field loads with uuid = None (the
        back-fill happens later, on demand, via api.character.ensure_uuid)."""
        import json
        # Save a normal document, then strip the `uuid` key to mimic a file
        # written by a version that predates the field.
        AdvancedPcModel().save_to(self.path)
        with open(self.path, 'rt') as fp:
            doc = json.load(fp)
        doc.pop('uuid', None)
        with open(self.path, 'wt') as fp:
            json.dump(doc, fp)

        reloaded = AdvancedPcModel()
        self.assertTrue(reloaded.load_from(self.path))
        self.assertIsNone(reloaded.uuid)

    def test_non_rank_advancement_stays_generic(self):
        """A plain advancement keeps its flat attributes and type tag."""
        pc = AdvancedPcModel()
        pc.add_advancement(SkillAdv('test_skill_1', 1))

        reloaded = self._save_and_reload(pc)

        self.assertEqual(1, len(reloaded.advans))
        self.assertEqual('skill', reloaded.advans[0].type)
        self.assertEqual('test_skill_1', reloaded.advans[0].skill)


if __name__ == '__main__':
    unittest.main()
