# -*- coding: utf-8 -*-
# Copyright (C) 2014 Daniele Simonetti
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

import l5r.models as models
import l5r.api as api

import l5r.api.data
import l5r.api.data.skills
import l5r.api.data.clans
import l5r.api.data.families
import l5r.api.data.schools
import l5r.api.rules
import l5r.api.character
from l5r.exporters.fdfexporter import FDFExporter, zigzag


class FDFExporterTwoNPC(FDFExporter):

    def __init__(self, pcs):
        super(FDFExporterTwoNPC, self).__init__()
        self.pcs = pcs

    def export_body(self, io):
        f = self.form

        fields = {}

        for i, pc in enumerate(self.pcs):
            self.export_npc(i + 1, pc, fields)

        # EXPORT FIELDS
        for k in fields:
            self.export_field(k, fields[k], io)

    def get_skills_sorted(self, pc, key):

        skill_list = []
        for s in api.character.skills.get_all():
            sk_obj = api.data.skills.get(s)
            if not sk_obj:
                continue
            o = {
                'id': s,
                'rank': api.character.skills.get_skill_rank(s),
                'name': sk_obj.name,
                'emph': ', '.join(api.character.skills.get_skill_emphases(s))}

            skill_list.append(o)

        return sorted(skill_list, key=key)

    def fmt_skill_line(self, sk):
        if len(sk['emph']) > 0:
            return "{nm} {r} ({e})".format(nm=sk['name'], r=sk['rank'], e=sk['emph'])
        return "{nm} {r}".format(nm=sk['name'], r=sk['rank'])

    def export_npc(self, index, pc, fields):

        api.character.set_model(pc)

        def _af(key, value, idx=index):
            fields['{}{}'.format(key, idx)] = str(value)

        clan_obj = api.data.clans.get(api.character.get_clan())
        if clan_obj:
            _af("Clan", clan_obj.name)

        name = ""
        family_obj = api.data.families.get(api.character.get_family())
        if family_obj:
            name = "{} {}".format(family_obj.name, pc.name)
        else:
            name = pc.name
        _af("Name", name)

        sobj = api.data.schools.get(api.character.schools.get_current())
        if sobj:
            _af("School", sobj.name)

        _af("Rank", api.character.insight_rank())
        _af("Insight", api.character.insight())
        _af("XP", api.character.xp())

        # rings
        _af("Earth", api.character.ring_rank('earth'))
        _af("Air", api.character.ring_rank('air'))
        _af("Water", api.character.ring_rank('water'))
        _af("Fire", api.character.ring_rank('fire'))
        _af("Void", api.character.ring_rank('void'))

        # traits
        _af("Stamina", api.character.trait_rank('stamina'))
        _af("Willpower", api.character.trait_rank('willpower'))
        _af("Reflexes", api.character.trait_rank('reflexes'))
        _af("Awareness", api.character.trait_rank('awareness'))
        _af("Strength", api.character.trait_rank('strength'))
        _af("Perception", api.character.trait_rank('perception'))
        _af("Agility", api.character.trait_rank('agility'))
        _af("Intelligence", api.character.trait_rank('intelligence'))

        _af("Initiative", api.rules.format_rtk_t(api.rules.get_tot_initiative()))
        _af("Armor", api.character.get_full_tn())
        _af("Reduction", api.character.get_full_rd())

        # HEALTH
        w_labels = ['Healthy', 'Nicked', 'Grazed',
                    'Hurt', 'Injured', 'Crippled',
                    'Down', 'Out']

        hl = [0] * 8
        for i in range(0, 8):
            if i == 0:
                hl[i] = api.rules.get_health_rank(i)
            else:
                hl[i] = api.rules.get_health_rank(i) + hl[i - 1]
            _af(w_labels[i], hl[i])

        # WEAPONS
        melee_weapons = [x for x in pc.get_weapons() if 'melee' in x.tags]
        range_weapons = [
            x for x in pc.get_weapons() if 'ranged' in x.tags and 'melee' not in x.tags]

        wl = zigzag(melee_weapons, range_weapons)

        for i, weapon in enumerate(wl):
            if i >= 2:
                break
            j = (index - 1) * 2 + i + 1
            _af("Type", weapon.name, j)
            atk_roll = api.rules.format_rtk_t(
                api.rules.calculate_mod_attack_roll(pc, weapon))
            _af("Attack", atk_roll, j)
            dmg_roll = api.rules.format_rtk_t(
                api.rules.calculate_mod_damage_roll(pc, weapon))
            _af("Damage", dmg_roll, j)
            _af("Notes", weapon.desc, j)

        # OTHER TRAITS
        _af("Status", api.character.status())
        _af("Honor", api.character.honor())
        _af("Glory", api.character.glory())
        _af("GloryTN", int(50 - api.character.glory() * 5))

        # SKILLS
        skills = self.get_skills_sorted(pc, lambda x: x['rank'])
        # divide in 5 lists
        skill_per_line = max(5, len(skills) / 5)

        # offset
        off = 0

        for i in range(0, 5):
            sks = []
            if i == 4:
                sks = skills[off:]
            else:
                sks = skills[off:off + skill_per_line]

            if len(sks) == 0:
                break

            skill_line = ', '.join([self.fmt_skill_line(x) for x in sks])

            fn = "Skill  Rank Emphases {}".format(i + 1)
            if index > 1:
                fn += "_2"

            fields[fn] = skill_line

            off += skill_per_line
