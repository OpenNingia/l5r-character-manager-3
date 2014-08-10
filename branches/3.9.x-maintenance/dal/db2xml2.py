# -*- coding: iso-8859-1 -*-
# Copyright (C) 2011 Daniele Simonetti
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

import sqlite3
import sys
import os
import string

#import xml.etree.cElementTree as ET
import lxml.etree as ET

def _lu(s):
    s1 = ''
    flag = True
    for c in s.strip():
        if (c in string.punctuation):
            continue
        if (c in string.ascii_letters or
            c in string.digits):
            s1 += c.lower()
            flag = True
        elif flag:
            s1 += '_'
            flag = False
    return s1

def exp_clans(db, out_file, out_path):
    c = db.cursor()
    c.execute('''select uuid, name
                 from clans order by name''')

    if not os.path.exists(out_path):
        os.makedirs(out_path)

    scs  = [ x for x in c.fetchall() ]
    root = ET.Element('L5RCM')
    fpath = os.path.join(out_path, out_file)

    for uuid, name in scs:
        ec = ET.SubElement(root, 'Clan', {'name': name, 'id': _lu(name)})

    if root is not None:
        ET.ElementTree(root).write(fpath, pretty_print = True, encoding='UTF-8', xml_declaration=True)

def exp_families(db, out_file, out_path):
    c = db.cursor()
    c.execute("select clans.name, families.name, perk from families inner join clans on clans.uuid=clan_id order by clans.name")
    cn   = None
    if not os.path.exists(out_path):
        os.makedirs(out_path)
    scs  = [ x for x in c.fetchall() ]
    root = None
    for clan, name, perk in scs:
        if cn != clan and root is not None:
            fname = "{0}_{1}".format(cn, out_file)
            fpath = os.path.join(out_path, fname)
            ET.ElementTree(root).write(fpath, pretty_print = True, encoding='UTF-8', xml_declaration=True)
            root = None

        if root is None:
            root = ET.Element('L5RCM')
            cn    = clan

        if '(' in name:
            name = name[0:name.find('(')].strip()

        efam = ET.SubElement(root, 'Family', {'name': name, 'id': _lu(clan + ' ' + name), 'clanid': _lu(clan)})
        if perk: ET.SubElement(efam, 'Trait').text = _lu(perk)

    if root is not None:
        fname = "{0}_{1}".format(cn, out_file)
        fpath = os.path.join(out_path, fname)
        ET.ElementTree(root).write(fpath, pretty_print = True, encoding='UTF-8', xml_declaration=True)

def exp_schools(db, out_file, out_path):
    c = db.cursor()
    c.execute('''select schools.uuid, clans.name, schools.name, tag, perk,
                 affinity, deficiency, honor
                 from schools inner join clans on clans.uuid=clan_id order by clans.name''')
    cn   = None

    if not os.path.exists(out_path):
        os.makedirs(out_path)

    scs  = [ x for x in c.fetchall() ]
    root = None


    for uuid, clan, name, tags, perk, affi, defi, hon in scs:
        if cn != clan and root is not None:
            fname = "{0}_{1}".format(cn, out_file)
            fpath = os.path.join(out_path, fname)
            ET.ElementTree(root).write(fpath, pretty_print = True, encoding='UTF-8', xml_declaration=True)
            root = None

        if root is None:
            root = ET.Element('L5RCM')
            cn    = clan

        if '(' in name:
            name = name[0:name.find('(')].strip()

        efam = ET.SubElement(root, 'School', {'name': name, 'id': _lu(clan + ' ' + name), 'clanid': _lu(clan)})
        if perk: ET.SubElement(efam, 'Trait').text = _lu(perk)
        if affi: ET.SubElement(efam, 'Affinity').text = _lu(affi)
        if defi: ET.SubElement(efam, 'Deficiency').text = _lu(defi)
        if hon : ET.SubElement(efam, 'Honor').text = str(hon)
        etags = ET.SubElement(efam, 'Tags')
        for tag in tags.split(';'):
            ET.SubElement(etags, 'Tag').text = _lu(tag)
            ET.SubElement(etags, 'Tag').text = _lu(clan + ' ' + tag)

        exp_school_skills(db, uuid, ET.SubElement(efam, 'Skills'))
        exp_school_spells(db, uuid, ET.SubElement(efam, 'Spells'))
        exp_school_techs (db, uuid, clan, ET.SubElement(efam, 'Techs' ))
        exp_school_requirements(db, uuid, ET.SubElement(efam, 'Requirements'))

    if root is not None:
        fname = "{0}_{1}".format(cn, out_file)
        fpath = os.path.join(out_path, fname)
        ET.ElementTree(root).write(fpath, pretty_print = True, encoding='UTF-8', xml_declaration=True)

def exp_school_skills(db, uuid, root):
    c = db.cursor()
    c.execute('''select skills.name, emphases, skill_rank
                 from school_skills inner join skills on skills.uuid=skill_uuid
                 where school_uuid=?
                 order by skills.name''', [uuid])

    for name, emphases, rank in c.fetchall():
        if emphases:
            ET.SubElement(root, "Skill", {'id': _lu(name), 'emphases': emphases, 'rank': str(rank) })
        else:
            ET.SubElement(root, "Skill", {'id': _lu(name), 'rank': str(rank) })

    c.execute('''select wildcard, skill_rank
                 from school_skills
                 where wildcard is not null
                 and school_uuid=?''', [uuid])

    for wildcard, rank in c.fetchall():
        epc = ET.SubElement(root, "PlayerChoose", {'rank': str(rank) })
        for wc in wildcard.split(';'):
            ET.SubElement(epc, "Wildcard").text = _lu(wc)

def exp_school_spells(db, uuid, root):
    c = db.cursor()
    c.execute('''select school_uuid, spells.name
                 from school_spells inner join spells on spells.uuid=spell_uuid
                 where school_uuid=?
                 order by spells.name''', [uuid])

    for sc, name in c.fetchall():
        ET.SubElement(root, "Spell", {'id': _lu(name)})

    c.execute('''select school_uuid, wildcard
                 from school_spells
                 where wildcard is not null
                 and school_uuid=?''', [uuid])

    for sc, wildcard in c.fetchall():
        elem, cnt = wildcard.split(' ')
        cnt = cnt.strip('()')
        epc = ET.SubElement(root, "PlayerChoose", {'count': cnt, 'element': _lu(elem)})

def exp_school_techs (db, uuid, clan, root):
    c = db.cursor()
    c.execute('''select school_techs.name, rank, desc
                 from school_techs inner join schools on schools.uuid=school_uuid
                 where school_uuid=?
                 order by rank''', [uuid])

    for name, rank, desc in c.fetchall():
        if '(' in name:
            name = name[0:name.find('(')].strip()

        if not desc: desc = ''
        ET.SubElement(root, "Tech", {'name': name, 'id': _lu(clan + ' ' + name), 'rank': str(rank)}).text = desc

def exp_school_requirements(db, uuid, root):
    c = db.cursor()
    c.execute('''select req_field, req_type, min_val, max_val, target_val
                 from requirements inner join schools on schools.uuid=ref_uuid
                 where ref_uuid=?''', [uuid])

    for field, type, min, max, trg in c.fetchall():
        attr = {'type': type, 'field': _lu(field) }
        if min: attr['min'] = str(min)
        if max: attr['min'] = str(max)
        if trg: attr['trg'] = str(trg)
        ET.SubElement(root, "Requirement", attr).text = field.title()

def exp_skills(db, out_file, out_path):
    c = db.cursor()
    c.execute('''select uuid, name, type, attribute
                 from skills order by type''')
    root = ET.Element('L5RCM')
    for uuid, name, type, trait in c.fetchall():
        attr = {'type': type, 'trait': _lu(trait), 'id': _lu(name), 'name': name}
        sk_def = ET.SubElement(root, "SkillDef", attr)
        exp_tags(db, uuid, ET.SubElement(sk_def, 'Tags'))
        ma_elem = ET.SubElement(sk_def, 'MasteryAbilities')
        c.execute('''select skill_rank, rule, brief
                     from mastery_abilities
                     where skill_uuid=?
                     order by skill_rank''', [uuid])

        for rank, rule, brief in c.fetchall():
            attr = {'rank': str(rank)}
            if rule: attr['rule'] = rule
            ET.SubElement(ma_elem, "MasteryAbility", attr).text = brief

    fpath = os.path.join(out_path, out_file)
    ET.ElementTree(root).write(fpath, pretty_print = True, encoding='UTF-8', xml_declaration=True)

def exp_weapons(db, out_file, out_path):
    c = db.cursor()
    c.execute('''select weapons.uuid, weapons.name, skills.name, dr,
                 dr_alt, range, strength, min_strength,
                 effect_id, cost
                 from weapons
                 inner join skills on skills.uuid=skill_uuid
                 order by skills.name''')

    root = ET.Element('L5RCM')
    for uuid, name, skill, dr, dr_alt, range, strength, min_strength, effect_id, cost in c.fetchall():
        attr = {'name': name}
        if skill: attr['skill'] = _lu(skill)
        if dr: attr['dr'] = dr
        if dr_alt: attr['dr_alt'] = dr_alt
        if range: attr['range'] = str(range)
        if strength: attr['strength'] = str(strength)
        if min_strength: attr['min_strength'] = str(min_strength)
        if cost: attr['cost'] = str(cost)

        wp_def = ET.SubElement(root, "Weapon", attr)
        exp_tags(db, uuid, ET.SubElement(wp_def, 'Tags'))

        if effect_id:
            d = db.cursor()
            d.execute('''select tag, desc from effects where uuid=?''', [effect_id])
            tag, desc = d.fetchone()
            ET.SubElement(wp_def, 'Effect', {'id': tag})

    fpath = os.path.join(out_path, out_file)
    ET.ElementTree(root).write(fpath, pretty_print = True, encoding='UTF-8', xml_declaration=True)

def exp_armors(db, out_file, out_path):
    c = db.cursor()
    c.execute('''select uuid, name, tn, rd,
                 special, cost
                 from armors
                 order by name''')

    root = ET.Element('L5RCM')
    for uuid, name, tn, rd, special, cost in c.fetchall():
        attr = {'name': name, 'tn': str(tn), 'rd': str(rd), 'cost': cost}

        ar_def = ET.SubElement(root, "Armor", attr)

        if special:
            ET.SubElement(ar_def, 'Effect', {'id': special})

    fpath = os.path.join(out_path, out_file)
    ET.ElementTree(root).write(fpath, pretty_print = True, encoding='UTF-8', xml_declaration=True)

def exp_spells(db, out_file, out_path):
    c = db.cursor()
    c.execute('''select uuid, name, ring, mastery,
                 range, area, duration, raises
                 from spells
                 order by mastery, ring, name asc''')

    root = ET.Element('L5RCM')
    for uuid, name, ring, mastery, range, area, duration, raises in c.fetchall():
        attr = {'id': _lu(name), 'name': name, 'element': _lu(ring), 'mastery': str(mastery), 'range': range,
                'area': area, 'duration': duration}

        sp_def = ET.SubElement(root, "SpellDef", attr)
        tags = ET.SubElement(sp_def, 'Tags')
        exp_tags(db, uuid, tags)
        if raises:
            r_elem = ET.SubElement(sp_def, 'Raises')
            for r in raises.split(';'):
                ET.SubElement(r_elem, 'Raise').text = r.strip()

        # add maho tag
        if '[MAHO]' in name:
            ET.SubElement(tags, 'Tag').text = 'maho'

    fpath = os.path.join(out_path, out_file)
    ET.ElementTree(root).write(fpath, pretty_print = True, encoding='UTF-8', xml_declaration=True)

def exp_tags(db, uuid, root):
    c = db.cursor()
    c.execute('''select uuid, tag
                 from tags
                 where uuid=? order by tag''', [uuid])

    for uuid, tag in c.fetchall():
        ET.SubElement(root, "Tag").text = _lu(tag)

def exp_perks(db, out_file, out_path, perktype):
    c = db.cursor()
    c.execute('''select uuid, name, subtype, rule
                 from perks
                 where type=?
                 order by subtype, name asc''', [perktype])

    elem_nm = perktype.capitalize()

    root = ET.Element('L5RCM')
    for uuid, name, type, rule in c.fetchall():
        attr = {'id': _lu(name), 'name': name, 'type': type}
        if rule: attr['rule'] = rule

        merit = ET.SubElement(root, elem_nm, attr)

        c.execute('''select perk_rank, cost
                    from perk_ranks
                    where perk_uuid=?
                    order by perk_rank''',[uuid])

        for rank, cost in c.fetchall():
            rank_elem = ET.SubElement(merit, "Rank", {'id': str(rank), 'value': str(cost)})
            c.execute('''select tag, cost
                        from perk_excepts
                        where perk_uuid=? and perk_rank=?
                        order by tag''',[uuid, rank])

            for tag, ncost in c.fetchall():
                if '-' in ncost or '+' in ncost:
                    ncost = cost + int(ncost)
                else:
                    ncost = int(ncost)
                ET.SubElement(rank_elem, "Exception", {'tag': tag, 'value': str(ncost)})

    fpath = os.path.join(out_path, out_file)
    ET.ElementTree(root).write(fpath, pretty_print = True, encoding='UTF-8', xml_declaration=True)

def exp_effects(db, out_file, out_path):
    c = db.cursor()
    c.execute('''select tag, desc from effects''')

    root = ET.Element('L5RCM')
    for tag, desc in c.fetchall():
        sp_def = ET.SubElement(root, "EffectDef", {'id': tag}).text = desc

    fpath = os.path.join(out_path, out_file)
    ET.ElementTree(root).write(fpath, pretty_print = True, encoding='UTF-8', xml_declaration=True)

def exp_skill_types(db, out_file, out_path):
    c = db.cursor()
    c.execute('''select distinct type from skills order by type''')

    root = ET.Element('L5RCM')
    for sktype in c.fetchall():
        ET.SubElement(root, "SkillCateg", {'id': _lu(sktype[0])}).text = sktype[0].capitalize()

    fpath = os.path.join(out_path, out_file)
    ET.ElementTree(root).write(fpath, pretty_print = True, encoding='UTF-8', xml_declaration=True)

def exp_katas(db, out_file, out_path):
    c = db.cursor()
    c.execute('''select uuid, name, ring, mastery, desc from kata order by ring, mastery, name asc''')

    root = ET.Element('L5RCM')
    for uuid, name, ring, mastery, desc in c.fetchall():
        elem_kata = ET.SubElement(root, "KataDef", {'id': _lu(name), 'name': name, 'element': _lu(ring), 'mastery': str(mastery)})
        ET.SubElement(elem_kata, 'Description').text = desc
        exp_kata_requirements(db, uuid, ET.SubElement(elem_kata, 'Requirements'))

    fpath = os.path.join(out_path, out_file)
    ET.ElementTree(root).write(fpath, pretty_print = True, encoding='UTF-8', xml_declaration=True)

def exp_kata_requirements(db, uuid, root):
    c = db.cursor()
    c.execute('''select req_field, req_type, min_val, max_val, target_val
                 from requirements inner join kata on kata.uuid=ref_uuid
                 where ref_uuid=?''', [uuid])

    for field, type, min, max, trg in c.fetchall():
        attr = {'type': type, 'field': _lu(field).replace('_school', '') }
        if min: attr['min'] = str(min)
        if max: attr['min'] = str(max)
        if trg: attr['trg'] = str(trg)
        ET.SubElement(root, "Requirement", attr).text = field.title()

def main():
    db = sqlite3.connect(sys.argv[1])
    exp_clans   (db, "clans.xml", '../share/l5rcm/data')
    exp_families(db, "families.xml", '../share/l5rcm/data/families')
    exp_schools (db, "schools.xml", '../share/l5rcm/data/schools')
    exp_skills  (db, "skills.xml", '../share/l5rcm/data')
    exp_weapons (db, "weapons.xml", '../share/l5rcm/data')
    exp_armors  (db, "armors.xml", '../share/l5rcm/data')
    exp_spells  (db, "spells.xml", '../share/l5rcm/data')
    exp_perks   (db, "merits.xml", '../share/l5rcm/data', 'merit')
    exp_perks   (db, "flaws.xml", '../share/l5rcm/data',  'flaw')
    exp_effects (db, "weapon_effects.xml", '../share/l5rcm/data')
    exp_katas   (db, "katas.xml", '../share/l5rcm/data')


    exp_skill_types(db, "skill_categories.xml", '../share/l5rcm/data')

if __name__ == '__main__':
    main()
