# -*- coding: utf-8 -*-
__author__ = 'Daniele'

from api import __api
import api.data

from collections import namedtuple

from asq.initiators import query
from asq.selectors import a_

from util import log


def get_all_kiho():
    """returns all character kiho"""
    return query(__api.pc.advans).where(lambda x: x.type == 'kiho').select(a_('kiho')).to_list()


def get_all_kata():
    """returns all character kata"""
    return query(__api.pc.advans).where(lambda x: x.type == 'kata').select(a_('kata')).to_list()


def check_kiho_eligibility(kiho_id):
    """returns if the character can acquire the kiho and if not, also returns a reason string"""
    # check eligibility
    against_mastery = 0

    kiho_ = api.data.powers.get_kiho(kiho_id)
    if not kiho_:
        log.api.error(u"kiho not found: %s", kiho_id)
        return False, u"internal error"

    is_monk, is_brotherhood = api.character.is_monk()
    is_ninja = api.character.is_ninja()
    is_shugenja = api.character.is_shugenja()

    school_bonus = 0
    ring_ = api.data.get_ring(kiho_.element)
    ring_rank = api.character.ring_rank(kiho_.element)

    if is_ninja:
        ninja_schools = api.character.schools.get_schools_by_tag('ninja')
        ninja_rank = sum([api.character.schools.get_rank(x) for x in ninja_schools])

    if is_monk:
        monk_schools = api.character.schools.get_schools_by_tag('monk')
        school_bonus = sum([api.character.schools.get_rank(x) for x in monk_schools])

    against_mastery = school_bonus + ring_rank

    other_kiho = [api.data.powers.get_kiho(x) for x in get_all_kiho()]

    # check monks_walk_with_the_prophet
    if api.character.has_tag_or_rule('monks_walk_with_the_prophet'):
        # the first 3 kiho should be of the same element
        if 0 < len(other_kiho) < 3:
            first_kiho_element = other_kiho[0].element

            if first_kiho_element != kiho_.element:
                return False, api.tr("Your initial Kiho must be selected from the same element")
        if len(other_kiho) < 3:
            against_mastery += 1

    if is_brotherhood:
        return against_mastery >= kiho_.mastery, api.tr("Your {0} Ring or School Rank are not enough").format(ring_.text)
    elif is_monk:
        return against_mastery >= kiho_.mastery, api.tr("Your {0} Ring or School Rank are not enough").format(ring_.text)
    elif is_shugenja:
        return ring_rank >= kiho_.mastery, api.tr("Your {0} Ring Rank is not enough")
    elif is_ninja:
        return ninja_rank >= kiho_.mastery, api.tr("Your School Rank is not enough")

    return False, api.tr("You are not eligible")