# -*- coding: utf-8 -*-
__author__ = 'Daniele Simonetti'

# fake clans
from dal.clan import Clan

test_clan_1 = Clan()
test_clan_1.id = 'test_clan_1'
test_clan_1.name = u'test_clan_1'

test_clan_2 = Clan()
test_clan_2.id = 'test_clan_2'
test_clan_2.name = u'test_clan_2'

# fake families
from dal.family import Family

test_family_1 = Family()
test_family_1.id = 'test_family_1'
test_family_1.name = u'test_family_1'
test_family_1.clanid = 'test_clan_1'
test_family_1.trait = 'strength'

test_family_2 = Family()
test_family_2.id = 'test_family_2'
test_family_2.name = u'test_family_2'
test_family_2.clanid = 'test_clan_2'
test_family_2.trait = 'reflexes'

# fake schools
from dal.school import School, SchoolKiho, SchoolTattoo

test_school_1 = School()
test_school_1.id = 'test_school_1'
test_school_1.name = u'test_school_1'
test_school_1.clanid = 'test_clan_1'
test_school_1.trait = 'willpower'

test_school_1.affinity = 'test_element_1'
test_school_1.deficiency = 'test_element_2'
test_school_1.honor = 0.0
test_school_1.kihos = SchoolKiho()
test_school_1.tattoos = SchoolTattoo()

test_school_1.tags = ['test_tag_1']
test_school_1.skills = []
test_school_1.skills_pc = []
test_school_1.techs = []
test_school_1.spells = []
test_school_1.spells_pc = []
test_school_1.outfit = []
test_school_1.money = [0]*3 # koku, bu, zeni
test_school_1.require = []
test_school_1.perks = []

# fake skills
from dal.skill import Skill, SkillCateg
test_skill_categ_1 = SkillCateg()
test_skill_categ_1.id = 'test_skill_categ_1'
test_skill_categ_1.name = u'test_skill_categ_1'

test_skill_categ_2 = SkillCateg()
test_skill_categ_2.id = 'test_skill_categ_2'
test_skill_categ_2.name = u'test_skill_categ_2'

test_skill_1 = Skill()
test_skill_1.id = 'test_skill_1'
test_skill_1.name = u'test_skill_1'
test_skill_1.trait = 'agility'
test_skill_1.type = test_skill_categ_1
test_skill_1.tags = []
test_skill_1.mastery_abilities = []
test_skill_1.desc = u""

test_skill_2 = Skill()
test_skill_2.id = 'test_skill_2'
test_skill_2.name = u'test_skill_2'
test_skill_2.trait = 'intelligence'
test_skill_2.type = test_skill_categ_2
test_skill_2.tags = []
test_skill_2.mastery_abilities = []
test_skill_2.desc = u""
