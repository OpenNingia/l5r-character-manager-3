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

from PySide import QtGui, QtCore
from datetime import datetime
import models
import rules
import hashlib
import dal
import dal.query


class FDFExporter(object):
    def __init__(self):
        self.model  = None
        self.form   = None

    def set_model(self, model):
        self.model = model

    def set_form(self, form):
        self.form = form

    def export(self, io):
        self.export_header(io)
        self.export_body  (io)
        self.export_footer(io)

    def export_header(self, io):
        io.write("%FDF-1.2\n%????\n1 0 obj \n<< /FDF << /Fields [ ")

    def export_body(self, io):
        pass

    def export_footer(self, io):
        hash_ = hashlib.md5()
        hash_.update(str(datetime.now()))
        io.write(unicode.format(u"] \n/F (dummy.pdf) /ID [ <{0}>\n] >>",
                 hash_.hexdigest()))
        io.write(u" \n>> \nendobj\ntrailer\n")
        io.write(u"<<\n/Root 1 0 R \n\n>>\n%%EOF\n")

    def export_field(self, key, value, io):
        if type(value) == type(True):
            io.write(unicode.format(u"<< /V /{1} /T({0})>>", key, u'Yes' if value else u'No'))
        else:
            to_write = unicode.format(u"<< /V({1}) /T({0})>>", key, value).encode("iso-8859-15", "xmlcharrefreplace")
            io.write(to_write)

    # HELPERS

    def get_clan_name(self):
        return self.form.cb_pc_clan.currentText()

    def get_family_name(self):
        return self.form.cb_pc_family.currentText()

    def get_school_name(self):
        return self.form.cb_pc_school.currentText()

    def get_exp(self):
        return u'%s / %s' % (self.model.get_px(), self.model.exp_limit)


def zigzag(l1, l2):
    def _zigzag(l1_, l2_):
        rl = []
        i  = 0
        for i in range(0, len(l2_)):
            rl.append(l1_[i])
            rl.append(l2_[i])
        return rl + l1_[len(l2_):]

    if len(l1) >= len(l2):
        return _zigzag(l1,l2)
    return _zigzag(l2, l1)

class FDFExporterAll(FDFExporter):
    def __init__(self):
        super(FDFExporterAll, self).__init__()

    def export_body(self, io):
        m = self.model
        f = self.form

        fields = {}
        fields['NAME'   ] = m.name
        fields['CLAN'   ] = self.get_clan_name   ()
        fields['RANK'   ] = m.get_insight_rank   ()
        fields['FAMILY' ] = self.get_family_name ()
        fields['SCHOOL' ] = self.get_school_name ()
        fields['EXP'    ] = self.get_exp         ()
        fields['INSIGHT'] = m.get_insight        ()

        # TRAITS AND RINGS
        for i in xrange(0, 8):
            fields[models.attrib_name_from_id(i).upper()] = m.get_mod_attrib_rank(i)
        for i in xrange(0, 5):
            fields[models.ring_name_from_id(i).upper()] = m.get_ring_rank(i)

        # HONOR, GLORY, STATUS, TAINT
        hvalue, hdots = rules.split_decimal(m.get_honor ())
        gvalue, gdots = rules.split_decimal(m.get_glory ())
        svalue, sdots = rules.split_decimal(m.get_status())
        tvalue, tdots = rules.split_decimal(m.get_taint ())

        fields['HONOR' ] = hvalue
        fields['GLORY' ] = gvalue
        fields['STATUS'] = svalue
        fields['TAINT' ] = tvalue

        for i in xrange(1, hdots*10+1):
            fields['HONOR_DOT.%d' % i ]  = True

        for i in xrange(1, gdots*10+1):
            fields['GLORY_DOT.%d' % i ]  = True

        for i in xrange(1, sdots*10+1):
            fields['STATUS_DOT.%d' % i]  = True

        for i in xrange(1, tdots*10+1):
            fields['TAINT_DOT.%d' % i ]  = True

        # INITIATIVE
        fields['INITIATIVE_BASE'] = f.tx_base_init.text()
        fields['INITIATIVE_MOD' ] = f.tx_mod_init .text()
        fields['INITIATIVE_CUR' ] = f.tx_cur_init .text()

        # TN / RD
        fields['TN_BASE'] = m.get_base_tn ()
        fields['TN_CUR' ] = m.get_cur_tn  ()
        fields['BASE_RD'] = m.get_base_rd ()
        fields['CUR_RD' ] = m.get_full_rd ()

        # ARMOR
        fields['ARMOR_TYPE' ] = m.get_armor_name   ()
        fields['ARMOR_TN'   ] = m.get_armor_tn     ()
        fields['ARMOR_RD'   ] = m.get_armor_rd     ()
        fields['ARMOR_NOTES'] = m.get_armor_desc   ()

        # WOUNDS
        w_labels = ['HEALTHY', 'NICKED', 'GRAZED',
                    'HURT', 'INJURED', 'CRIPPLED',
                    'DOWN', 'OUT']
        for i in xrange(0, len(w_labels)):
            fields[w_labels[i]] = str(f.get_health_rank(i))

        fields['WOUND_HEAL_BASE'] = (m.get_mod_attrib_rank(models.ATTRIBS.STAMINA)*2
                                     + m.get_insight_rank())
        fields['WOUND_HEAL_CUR' ] = fields['WOUND_HEAL_BASE']

        # SKILLS
        count = min(23, len(f.sk_view_model.items))
        for i in xrange(1, count+1):
            sk = f.sk_view_model.items[i-1]
            fields['SKILL_IS_SCHOOL.%d' % i] = sk.is_school
            fields['SKILL_NAME.%d'    % i  ] = sk.name
            fields['SKILL_RANK.%d'    % i  ] = sk.rank
            fields['SKILL_TRAIT.%d'   % i  ] = (dal.query.get_trait(f.dstore, sk.trait) or
                                                dal.query.get_ring (f.dstore, sk.trait))
            fields['SKILL_EMPH_MA.%d' % i  ] = ', '.join(sk.emph)

        # MERITS AND FLAWS
        merits = f.merits_view_model.items
        flaws  = f.flaws_view_model .items

        count = min(17, len(merits))
        for i in xrange(1, count+1):
            merit = merits[i-1]
            fields['ADVANTAGE_NM.%d' % i] = merit.name
            fields['ADVANTAGE_PT.%d' % i] = abs(merit.cost)

        count = min(17, len(flaws))
        for i in xrange(1, count+1):
            flaw = flaws[i-1]
            fields['DISADVANTAGE_NM.%d' % i] = flaw.name
            fields['DISADVANTAGE_PT.%d' % i] = abs(flaw.cost)

        # WEAPONS
        melee_weapons = f.melee_view_model .items
        range_weapons = [x for x in f.ranged_view_model.items if 'melee' not in x.tags]
        wl = zigzag(melee_weapons, range_weapons)

        count = min(2, len(wl))
        for i in xrange(1, count+1):
            weap = wl[i-1]
            fields['WEAP_TYPE.%d'  % i] = weap.name
            if weap.base_atk != weap.max_atk:
                fields['WEAP_ATK.%d'   % i] = weap.base_atk + "/" + weap.max_atk
            else:
                fields['WEAP_ATK.%d'   % i] = weap.base_atk
            if weap.base_dmg != weap.max_dmg:
                fields['WEAP_DMG.%d'   % i] = weap.base_dmg + "/" + weap.max_dmg
            else:
                fields['WEAP_DMG.%d'   % i] = weap.base_dmg
            fields['WEAP_NOTES.%d' % i] = weap.desc

        # ARROWS
        arrows        = f.arrow_view_model .items
        count = min(5, len(arrows))
        for i in xrange(1, count+1):
            ar = arrows[i-1]
            fields['ARROW_TYPE.%d'  % i] = ar.name.replace('Arrow', '')
            fields['ARROW_DMG.%d'   % i] = ar.dr
            fields['ARROW_QTY.%d'   % i] = ar.qty

        # PERSONAL INFORMATIONS
        fields['GENDER']         = m.get_property('sex')
        fields['AGE']            = m.get_property('age')
        fields['HEIGHT']         = m.get_property('height')
        fields['WEIGHT']         = m.get_property('weight')
        fields['HAIR']           = m.get_property('hair')
        fields['EYES']           = m.get_property('eyes')
        fields['FATHER']         = m.get_property('father')
        fields['MOTHER']         = m.get_property('mother')
        fields['BROTHERS']       = m.get_property('brothers')
        fields['SISTERS']        = m.get_property('sisters')
        fields['MARITAL STATUS'] = m.get_property('marsta')
        fields['SPOUSE']         = m.get_property('spouse')

        if m.get_property('childr'):
            chrows = m.get_property('childr').split('\n\r')
            for i in xrange(0, len(chrows)):
                fields['CHILDREN.%d' % (i+1)] = chrows[i]

        # EQUIPMENT
        equip_list = m.get_school_outfit() + m.get_property('equip', [])
        equip_num  = min(50, len(equip_list))
        equip_cols = [18, 18, 15]
        c          = 0
        for i in xrange(0, len(equip_cols)):
            for j in xrange(0, equip_cols[i]):
                if c < equip_num:
                    fields['EQUIP_LINE.{0}.{1}'.format(j, i)] = equip_list[c]
                    c += 1

        # MONEY
        money = m.get_property('money')
        if money and len(money) == 3:
            fields['KOKU'] = str( money[0] )
            fields['BU'  ] = str( money[1] )
            fields['ZENI'] = str( money[2] )

        # MISC
        misc = f.tx_pc_notes.get_plain_text()
        fields['MISCELLANEOUS'] = misc

        # EXPORT FIELDS
        for k in fields.iterkeys():
            self.export_field(k, fields[k], io)

class FDFExporterShugenja(FDFExporter):
    def __init__(self):
        super(FDFExporterShugenja, self).__init__()

    def export_body(self, io):
        m = self.model
        f = self.form

        fields = {}

        # spells
        print('Starting Spells Export')
        lPageNumber, lControlNumber = 1, 1
        lShortDescription = ''
        for spell in f.sp_view_model.items:
            fields['SPELL_NM.%d.%d'  % (lPageNumber, lControlNumber)       ] = spell.name
            fields['SPELL_MASTERY.%d.%d'  % (lPageNumber, lControlNumber)  ] = spell.mastery
            fields['SPELL_RANGE.%d.%d'  % (lPageNumber, lControlNumber)    ] = spell.range
            fields['SPELL_AREA.%d.%d'  % (lPageNumber, lControlNumber)     ] = spell.area
            fields['SPELL_DURATION.%d.%d'  % (lPageNumber, lControlNumber) ] = spell.duration
            fields['SPELL_ELEM.%d.%d'  % (lPageNumber, lControlNumber)     ] = spell.ring
            fields['SPELL_RAISE.%d.%d'  % (lPageNumber, lControlNumber)    ] = spell.raises
            fields['SPELL_TAGS.%d.%d'  % (lPageNumber, lControlNumber)     ] = spell.tags
            fields['SPELL_EFFECT.%d.%d'  % (lPageNumber, lControlNumber)   ] = self.shorten_string(spell.desc) or ''

            lControlNumber += 1
            if lControlNumber == 9 and lPageNumber == 1:
                lControlNumber = 1
                lPageNumber += 1

        # schools
        print('Starting Schools Export')
        schools = filter(lambda x: 'shugenja' in x.tags, m.schools)
        count = min(3, len(schools))
        for i in xrange(0, count):
            def_ = schools[i].deficiency.capitalize() if schools[i].deficiency else "None"
            aff_ = schools[i].affinity.capitalize()   if schools[i].affinity   else "None"

            if aff_.startswith('*'): # wildcard
                aff_ = m.get_affinity().capitalize()

            if def_.startswith('*'): # wildcard
                def_ = m.get_affinity().capitalize()

            school = dal.query.get_school(f.dstore, schools[i].school_id)
            if school:
                for tech in school.techs:
                    fields['SCHOOL_NM.%d'  % (i+1)    ] = school.name
                    fields['AFFINITY.%d'  % (i+1)     ] = aff_
                    fields['DEFICIENCY.%d'  % (i+1)   ] = def_
                    fields['SCHOOL_TECH.%d'  % (i+1)] = tech.desc
            else:
                print('cannot export character school', schools[i].school_id)

        # EXPORT FIELDS5
        for k in fields.iterkeys():
            self.export_field(k, fields[k], io)

    def shorten_string(self, text, max_characters = 615):
        try:
            #TODO: REGEX
            #TODO: Pixel Length of string
            lShortDescription = (text[:max_characters] + "...") if len(text) > max_characters else text

            lOpenParenCount = lShortDescription.count("(")
            lClosedParenCount = lShortDescription.count(")")

            for i in xrange(0, lOpenParenCount-lClosedParenCount):
                lShortDescription+=")"

            return lShortDescription


            #max_pixel_length = 1926
            #metrics = QtGui.QFontMetrics(self.form.font())
            #actualWidth = metrics.boundingRect(text).width()
            #lShortDescription = ''
            #if actualWidth > max_pixel_length:
            #    lWords = text.split()
            #    for word in lWords:
            #        lShortDescription+= " " + word
            #        if metrics.boundingRect(lShortDescription).width() >= max_pixel_length:
            #            break
            #else:
            #    lShortDescription = text

        except Exception as e:
            print( repr(e) )
            return None   

    def split_in_parts(self, text, max_lines = 6):
        try:
            words = text.split(' ')
            tl    = len(text)
            avg_chars_per_line = int(tl / max_lines)

            lines = []

            cl = 0
            i  = 0
            line = ''
            while True:
                if len(lines) >= max_lines or i >= len(words):
                    break
                if cl < (avg_chars_per_line-3):
                    line += words[i]+ ' '
                    cl = len(line)
                    i += 1
                else:
                    cl = 0
                    lines.append(line)
                    line = ''

            if len(line):
                lines.append(line)

            return lines

        except Exception as e:
            print( repr(e) )
            return None            

class FDFExporterBushi(FDFExporter):
    def __init__(self):
        super(FDFExporterBushi, self).__init__()

    def export_body(self, io):
        m = self.model
        f = self.form

        fields = {}

        # schools
        #schools = filter(lambda x: 'bushi' in x.tags, m.schools)
        # FIX FOR SAMURAI MONKS
        schools = [x for x in m.schools if 'bushi' in x.tags or ('monk' in x.tags and not 'brotherhood' in x.tags) ]
        techs   = [x for x in m.get_techs()]

        count = min(2, len(schools))
        for i in xrange(0, count):
            school = dal.query.get_school(f.dstore, schools[i].school_id)
            fields['BUSHI_SCHOOL_NM.%d'  % i ] = school.name

            for t in techs:
                #tech   = dal.query.get_school_tech(school, j+1)
                thsc, tech = dal.query.get_tech(f.dstore, t)
                if not tech:
                    break
                if thsc != school:
                    continue
                rank = tech.rank-1 if tech.rank > 0 else 0
                fields['BUSHI_TECH.%d.%d' % (rank, i)] = tech.name

        # kata
        katas = [x.kata for x in m.get_kata()]
        count = min(6, len(katas))
        for i in xrange(0, count):
            kata = dal.query.get_kata(f.dstore, katas[i])
            if not kata:
                break
            fields['KATA_NM.%d' % (i+1)] = kata.name
            fields['KATA_RING_MA.%d' % (i+1)] = '{0} ({1})'.format(kata.element, kata.mastery)

        # EXPORT FIELDS
        for k in fields.iterkeys():
            self.export_field(k, fields[k], io)

class FDFExporterMonk(FDFExporter):
    def __init__(self):
        super(FDFExporterMonk, self).__init__()

    def export_body(self, io):
        m = self.model
        f = self.form

        fields = {}

        # schools
        #schools = filter(lambda x: 'monk' in x.tags, m.schools)
        # ONLY BROTHERHOOD SCHOOLS
        schools = [x for x in m.schools if 'brotherhood' in x.tags]
        count = min(3, len(schools))
        for i in xrange(0, count):
            school = dal.query.get_school(f.dstore, schools[i].school_id)
            if school is None: break
            tech   = dal.query.get_school_tech(school, 1)
            if tech is None: break

            fields['MONK_SCHOOL.%d'  % (i+1) ] = school.name
            fields['MONK_TECH.%d' % (i+1)] = tech.name

        # kiho
        kihos = [x.kiho for x in m.get_kiho()]
        count = min(12, len(kihos))

        for i in xrange(0, count):
            kiho = dal.query.get_kiho(f.dstore, kihos[i])
            if not kiho:
                break
            fields['KIHO_NM.%d' % (i+1)] = kiho.name
            fields['KIHO_MASTERY.%d'% (i+1)] = str(kiho.mastery)
            fields['KIHO_ELEM.%d'% (i+1)] = dal.query.get_ring(f.dstore, kiho.element)
            fields['KIHO_TYPE.%d'% (i+1)] = kiho.type
            lines = self.split_in_parts(kiho.desc) or []
            lc    = min(6, len(lines))
            for j in xrange(0, lc):
                fields['KIHO_EFFECT.%d.%d' % (i+1, j)] = lines[j]

        # EXPORT FIELDS
        for k in fields.iterkeys():
            self.export_field(k, fields[k], io)

    def split_in_parts(self, text, max_lines = 6):
        try:
            words = text.split(' ')
            tl    = len(text)
            avg_chars_per_line = int(tl / max_lines)

            lines = []

            cl = 0
            i  = 0
            line = ''
            while True:
                if i >= len(words):
                    break
                if cl < (avg_chars_per_line-3):
                    line += words[i]+ ' '
                    cl = len(line)
                    i += 1
                else:
                    cl = 0
                    lines.append(line)
                    line = ''

            if len(line):
                lines.append(line)

            return lines

        except Exception as e:
            print( repr(e) )
            return None

class FDFExporterWeapons(FDFExporter):
    def __init__(self):
        super(FDFExporterWeapons, self).__init__()

    def export_body(self, io):
        m = self.model
        f = self.form
        fields = {}
        # WEAPONS

        count = min(10, len(m.get_weapons()))
        j = 0

        for weap in m.get_weapons()[0:count]:
            weap.base_atk = rules.format_rtk_t(rules.calculate_base_attack_roll(m, weap))
            weap.max_atk  = rules.format_rtk_t(rules.calculate_mod_attack_roll (m, weap))
            weap.base_dmg = rules.format_rtk_t(rules.calculate_base_damage_roll(m, weap))
            weap.max_dmg  = rules.format_rtk_t(rules.calculate_mod_damage_roll (m, weap))

            fields['WEAPON.TYPE.%d'  % j] = weap.name
            if weap.base_atk != weap.max_atk:
                fields['WEAPON.ATK.%d'   % j] = weap.base_atk + "/" + weap.max_atk
            else:
                fields['WEAPON.ATK.%d'   % j] = weap.base_atk
            if weap.base_dmg != weap.max_dmg:
                fields['WEAPON.DMG.%d'   % j] = weap.base_dmg + "/" + weap.max_dmg
            else:
                fields['WEAPON.DMG.%d'   % j] = weap.base_dmg
            fields['WEAPON.NOTES.%d' % j] = weap.desc
            j+=1

        # EXPORT FIELDS
        for k in fields.iterkeys():
            self.export_field(k, fields[k], io)

class FDFExporterCourtier(FDFExporter):
    def __init__(self):
        super(FDFExporterCourtier, self).__init__()

    def export_body(self, io):
        m = self.model
        f = self.form

        fields = {}

        # schools
        schools = filter(lambda x: 'courtier' in x.tags, m.schools)
        techs   = [x for x in m.get_techs()]

        count = min(2, len(schools))
        for i in xrange(0, count):
            school = dal.query.get_school(f.dstore, schools[i].school_id)
            fields['COURTIER_SCHOOL_NM.%d'  % i ] = school.name

            for t in techs:
                thsc, tech = dal.query.get_tech(f.dstore, t)
                if not tech:
                    break
                if thsc != school:
                    continue
                rank = tech.rank-1 if tech.rank > 0 else 0
                fields['COURTIER_SCHOOL_RANK.%d.%d' % (i, rank)] = tech.name
                print('COURTIER_SCHOOL_RANK.%d.%d' % (i, rank), tech.name)

        # EXPORT FIELDS
        for k in fields.iterkeys():
            self.export_field(k, fields[k], io)
