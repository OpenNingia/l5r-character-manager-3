# -*- coding: utf-8 -*-
__author__ = 'Daniele'

import l5r.api as api
import l5r.api.character
import l5r.api.character.rankadv
import l5r.api.data
import l5r.api.data.powers
import l5r.api.rules
import l5r.models.advances
import l5r.models.charsnapshot

from l5r.api import get_context

from collections import namedtuple

from asq.initiators import query
from asq.selectors import a_

from l5r.util import log


def get_all_kiho():
    """returns all character kiho"""
    return query(get_context().pc.advans).where(lambda x: x.type == 'kiho').select(a_('kiho')).to_list()


def get_all_kata():
    """returns all character kata"""
    return query(get_context().pc.advans).where(lambda x: x.type == 'kata').select(a_('kata')).to_list()


def has_kata(kid):
    """returns true if the character had already learned the given kata"""
    return query(get_all_kata()).where(lambda x: x == kid).count() != 0


def has_kiho(kid):
    """returns true if the character had already learned the given kiho"""
    return query(get_all_kiho()).where(lambda x: x == kid).count() != 0


def check_kiho_eligibility(kiho_id):
    """returns if the character can acquire the kiho and if not, also returns a reason string"""

    # check eligibility
    kiho_ = api.data.powers.get_kiho(kiho_id)
    if not kiho_:
        log.api.error(u"kiho not found: %s", kiho_id)
        return False, u"internal error"

    is_monk, is_brotherhood = api.character.is_monk()
    is_ninja = api.character.is_ninja()
    is_shugenja = api.character.is_shugenja()

    ninja_rank = 0
    school_bonus = 0

    ring_ = api.data.get_ring(kiho_.element)
    ring_rank = api.character.ring_rank(kiho_.element)

    if is_ninja:
        ninja_schools = api.character.schools.get_schools_by_tag('ninja')
        ninja_rank = sum([api.character.schools.get_rank(x) for x in ninja_schools])

    if is_monk:
        monk_schools = api.character.schools.get_schools_by_tag('monk')
        school_bonus = sum([api.character.schools.get_rank(x) for x in monk_schools])
        if api.character.has_tag_or_rule('monks_the_way_of_fire'):
            if kiho_.element == 'fire':
                school_bonus += 1

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
        return ring_rank >= kiho_.mastery, api.tr("Your {0} Ring Rank is not enough").format(ring_.text)
    elif is_ninja:
        return ninja_rank >= kiho_.mastery, api.tr("Your School Rank is not enough")

    return False, api.tr("You are not eligible")


def _kata_source(kata_):
    """'<book>, p.<page>' citation for a kata DAL row; the book name
    alone when no page is set, or '' when the source is unknown. Mirrors
    the legacy KataDialog.update_book formatting."""
    try:
        pack = kata_.pack
    except Exception:
        pack = None
    if not pack:
        return u""
    name = getattr(pack, "display_name", "") or u""
    page = getattr(kata_, "page", 0) or 0
    if name and page:
        return u"{}, p.{}".format(name, page)
    return name


def get_all_buyable_kata():
    """Catalogue of kata the active character does not yet own, each
    bundled with everything a chooser needs to present and gate it:
    element (ring key + localised label), mastery, XP cost (== mastery),
    the Ring-rank gate, the per-requirement met flags, and an overall
    ``eligible`` verdict.

    Eligibility mirrors the gate the legacy KataDialog enforced on its
    Buy button: the character must match at least one (non role-play)
    requirement AND have a Ring rank in the kata's element of at least
    its mastery. Role-play ('more') requirements are advisory -- they are
    surfaced but never count toward the gate, exactly as the old
    RequirementsWidget.match_at_least_one ignored them.

    Returns a list of plain dicts (front-end agnostic), sorted by mastery
    then name."""
    pc = get_context().pc
    if pc is None:
        return []

    owned = set(get_all_kata())
    # One snapshot for the whole catalogue -- requirement matching is
    # read-only against it, so we don't rebuild it per kata.
    snap = l5r.models.charsnapshot.CharacterSnapshot(pc)
    dstore = api.data.model()

    out = []
    for kata_ in api.data.powers.kata():
        if kata_.id in owned:
            continue

        element = (kata_.element or "void").lower()
        ring_ = api.data.get_ring(kata_.element)
        element_label = ring_.text if ring_ else (kata_.element or "")
        mastery = int(kata_.mastery) if kata_.mastery is not None else 0

        have = api.character.ring_rank(kata_.element)
        ring_met = have >= mastery

        requirements = []
        any_testable = False
        any_met = False
        for r in kata_.require or []:
            roleplay = (r.type == 'more')
            met = False
            if not roleplay:
                any_testable = True
                met = bool(r.match(snap, dstore))
                if met:
                    any_met = True
            requirements.append({
                "text":     r.text or "",
                "met":      met,
                "roleplay": roleplay,
            })
        # No testable requirement => the "at least one" gate passes by
        # default, matching RequirementsWidget.match_at_least_one.
        reqs_ok = (not any_testable) or any_met

        out.append({
            "id":           kata_.id,
            "name":         kata_.name or kata_.id,
            "element":      element,
            "elementLabel": element_label,
            "mastery":      mastery,
            "cost":         mastery,
            "description":  getattr(kata_, "desc", "") or "",
            "source":       _kata_source(kata_),
            "requirements": requirements,
            "ringNeed": {
                "element": element,
                "label":   element_label,
                "needed":  mastery,
                "have":    int(have),
                "met":     ring_met,
            },
            "eligible":     ring_met and reqs_ok,
        })

    out.sort(key=lambda r: (r["mastery"], (r["name"] or "").lower()))
    return out


def buy_kata(kata_id):
    """Purchase a kata for the active character.

    The XP cost equals the kata's mastery (4e RAW). Lifted from the
    legacy L5RCMCore.buy_kata into the api layer so the QWidget and QML
    front-ends share one purchase path. Returns a ``CMErrors``:
    INTERNAL_ERROR for an unknown id, NOT_ENOUGH_XP when unaffordable,
    NO_ERROR on success. Owns the dirty flag per the setter contract."""
    kata_ = api.data.powers.get_kata(kata_id)
    if not kata_:
        log.api.error(u"kata not found: %s", kata_id)
        return api.data.CMErrors.INTERNAL_ERROR

    adv = l5r.models.advances.KataAdv(kata_.id, kata_.id, kata_.mastery)
    adv.desc = api.tr(u'{0}, Cost: {1} xp').format(kata_.name, adv.cost)

    res = api.character.purchase_advancement(adv)
    if res == api.data.CMErrors.NO_ERROR:
        api.character.set_dirty_flag(True)
    return res


def remove_kata(kata_id):
    """Unlearn a kata: drop the advancement that granted it. Returns True
    when an entry was removed. Owns the dirty flag per the setter
    contract. A character owns any given kata at most once (the chooser
    filters out owned kata), so keying removal by kata id is unambiguous
    -- no opaque advancement handle needs to cross the UI boundary."""
    pc = get_context().pc
    if pc is None:
        return False
    target = None
    for adv in pc.advans or []:
        if adv.type == 'kata' and getattr(adv, 'kata', None) == kata_id:
            target = adv
            break
    if target is None:
        log.api.warning(u"remove_kata: character does not own kata %s", kata_id)
        return False
    if api.character.remove_advancement(target):
        api.character.set_dirty_flag(True)
        return True
    return False


def _kiho_source(kiho_):
    """'<book>, p.<page>' citation for a kiho DAL row; the book name
    alone when no page is set, or '' when the source is unknown. Mirrors
    _kata_source / the legacy KihoDialog.update_book."""
    try:
        pack = kiho_.pack
    except Exception:
        pack = None
    if not pack:
        return u""
    name = getattr(pack, "display_name", "") or u""
    page = getattr(kiho_, "page", 0) or 0
    if name and page:
        return u"{}, p.{}".format(name, page)
    return name


def get_all_buyable_kiho():
    """Catalogue of kiho the active character does not yet know, each
    bundled with everything a chooser needs to present and gate it:
    element (ring key + localised label), mastery, kiho type (Internal /
    Martial / Mystical), the class-scaled XP cost, a source citation, the
    character's standing on the kiho 'paths', and an overall ``eligible``
    verdict with a human reason when it fails.

    Unlike a kata (gated on requirements + Ring rank), a kiho is gated on
    *who you are*: only a Monk, Ninja or Shugenja may learn one, and then
    only when their Ring (Monks/Shugenja) or School rank (Ninja) is at
    least the kiho's mastery -- exactly the test the legacy KihoDialog
    enforced via check_kiho_eligibility. Tattoos share kiho storage but
    are a different concept (free, no element/mastery); they are filtered
    out here and offered by get_all_buyable_tattoo instead.

    Returns a list of plain dicts (front-end agnostic), sorted by mastery
    then name."""
    pc = get_context().pc
    if pc is None:
        return []

    owned = set(get_all_kiho())

    # The kiho 'path' is character-wide, not per-kiho -- resolve it once.
    is_monk, is_brotherhood = api.character.is_monk()
    is_ninja = api.character.is_ninja()
    is_shugenja = api.character.is_shugenja()
    if is_brotherhood:
        path_kind = "brotherhood"
    elif is_monk:
        path_kind = "monk"
    elif is_ninja:
        path_kind = "ninja"
    elif is_shugenja:
        path_kind = "shugenja"
    else:
        path_kind = "none"
    path_met = path_kind != "none"

    out = []
    for kiho_ in api.data.powers.kiho():
        if kiho_.type == 'tattoo' or kiho_.id in owned:
            continue

        element = (kiho_.element or "void").lower()
        ring_ = api.data.get_ring(kiho_.element)
        element_label = ring_.text if ring_ else (kiho_.element or "")
        mastery = int(kiho_.mastery) if kiho_.mastery is not None else 0
        kind = (kiho_.type or "").strip()

        eligible, reason_raw = check_kiho_eligibility(kiho_.id)
        # The Ring/School reason is only meaningful once the path gate is
        # met; when it isn't, the path line already explains the block, so
        # surface no rank reason (the front-end says "must be a Monk…").
        reason = reason_raw if (path_met and not eligible) else u""

        out.append({
            "id":           kiho_.id,
            "name":         kiho_.name or kiho_.id,
            "element":      element,
            "elementLabel": element_label,
            "mastery":      mastery,
            "type":         kind.lower(),
            "typeLabel":    kind.title(),
            "cost":         int(api.rules.calculate_kiho_cost(kiho_.id)),
            "description":  getattr(kiho_, "desc", "") or "",
            "source":       _kiho_source(kiho_),
            "path":         {"kind": path_kind, "met": path_met},
            "eligible":     bool(eligible),
            "reason":       reason,
        })

    out.sort(key=lambda r: (r["mastery"], (r["name"] or "").lower()))
    return out


def buy_kiho(kiho_id):
    """Purchase a kiho for the active character.

    The XP cost is class-scaled (api.rules.calculate_kiho_cost): a Monk
    of the Brotherhood pays the mastery, other Monks 1.5x, Shugenja and
    Ninja 2x. A character who has earned free kiho from a School rank
    spends one of those in place of XP. Lifted from the legacy
    L5RCMCore.buy_kiho into the api layer so the QWidget and QML
    front-ends share one purchase path. Returns a ``CMErrors``:
    INTERNAL_ERROR for an unknown id, NOT_ENOUGH_XP when unaffordable,
    NO_ERROR on success. Owns the dirty flag per the setter contract."""
    kiho_ = api.data.powers.get_kiho(kiho_id)
    if not kiho_:
        log.api.error(u"kiho not found: %s", kiho_id)
        return api.data.CMErrors.INTERNAL_ERROR

    cost = api.rules.calculate_kiho_cost(kiho_.id)
    adv = l5r.models.advances.KihoAdv(kiho_.id, kiho_.id, cost)

    # Monks may earn free kiho from a School rank -- spend one of those
    # before falling back to the experience pool. Decrementing only when
    # one is available drives the cost to 0, so the XP gate below always
    # passes in that case (no rollback path is needed).
    free_kiho = api.character.rankadv.get_gained_kiho_count()
    if free_kiho > 0:
        adv.cost = 0
        api.character.rankadv.set_gained_kiho_count(free_kiho - 1)
        log.api.info(u"free kiho left: %d", free_kiho - 1)

    adv.desc = api.tr(u'{0}, Cost: {1} xp').format(kiho_.name, adv.cost)

    res = api.character.purchase_advancement(adv)
    if res == api.data.CMErrors.NO_ERROR:
        api.character.set_dirty_flag(True)
    return res


def remove_kiho(kiho_id):
    """Unlearn a kiho: drop the advancement that granted it. Returns True
    when an entry was removed. Owns the dirty flag per the setter
    contract. A character owns any given kiho at most once (the chooser
    filters out owned ones), so keying removal by id is unambiguous -- the
    id namespace also tells a proper kiho apart from a tattoo (both are
    KihoAdv), so no power-type lookup is needed here."""
    pc = get_context().pc
    if pc is None:
        return False
    target = None
    for adv in pc.advans or []:
        if adv.type == 'kiho' and getattr(adv, 'kiho', None) == kiho_id:
            target = adv
            break
    if target is None:
        log.api.warning(u"remove_kiho: character does not own kiho %s", kiho_id)
        return False
    if api.character.remove_advancement(target):
        api.character.set_dirty_flag(True)
        return True
    return False


def _tattoo_source(kiho_):
    """'<book>, p.<page>' citation for a tattoo (kiho) DAL row; the book
    name alone when no page is set, or '' when the source is unknown.
    Mirrors _kata_source / the legacy TattooDialog.update_book."""
    try:
        pack = kiho_.pack
    except Exception:
        pack = None
    if not pack:
        return u""
    name = getattr(pack, "display_name", "") or u""
    page = getattr(kiho_, "page", 0) or 0
    if name and page:
        return u"{}, p.{}".format(name, page)
    return name


def get_all_tattoo():
    """ids of the tattoos the active character bears.

    A tattoo shares storage with a kiho -- both are KihoAdv entries
    (adv.type == 'kiho') -- so they are told apart by the kind of power
    they reference: a tattoo's DAL row has type == 'tattoo'. This returns
    only the tattoo ids, leaving the proper kiho to the kiho slice."""
    out = []
    for kid in get_all_kiho():
        k = api.data.powers.get_kiho(kid)
        if k and k.type == 'tattoo':
            out.append(kid)
    return out


def get_all_buyable_tattoo():
    """Catalogue of tattoos the active character does not yet bear, each
    bundled with what a chooser needs: id, name, prose description and a
    source citation.

    Tattoos are the mystic marks of the Togashi Order. Unlike kiho they
    carry no element, mastery or XP cost -- they are free. The legacy
    TattooDialog nominally gated them on Togashi membership, but that
    check was disabled in practice (always eligible), so every unowned
    tattoo is offered here. Returns plain dicts, sorted by name."""
    pc = get_context().pc
    if pc is None:
        return []

    owned = set(get_all_tattoo())
    out = []
    for k in api.data.powers.kiho():
        if k.type != 'tattoo' or k.id in owned:
            continue
        out.append({
            "id":          k.id,
            "name":        k.name or k.id,
            "description": getattr(k, "desc", "") or "",
            "source":      _tattoo_source(k),
        })
    out.sort(key=lambda r: (r["name"] or "").lower())
    return out


def buy_tattoo(tattoo_id):
    """Acquire a tattoo for the active character.

    Tattoos are free (4e RAW: the Togashi ise zumi bear them at no XP
    cost), so this appends a zero-cost KihoAdv directly rather than
    routing through purchase_advancement. Lifted from the legacy
    L5RCMCore.buy_tattoo so the QWidget and QML front-ends share one
    path. Returns a ``CMErrors``: INTERNAL_ERROR for an unknown id,
    NO_ERROR on success. Owns the dirty flag per the setter contract."""
    kiho_ = api.data.powers.get_kiho(tattoo_id)
    if not kiho_:
        log.api.error(u"tattoo not found: %s", tattoo_id)
        return api.data.CMErrors.INTERNAL_ERROR

    adv = l5r.models.advances.KihoAdv(kiho_.id, kiho_.id, 0)
    adv.desc = api.tr(u'{0} Tattoo').format(kiho_.name)

    api.character.append_advancement(adv)
    api.character.set_dirty_flag(True)
    return api.data.CMErrors.NO_ERROR


def remove_tattoo(tattoo_id):
    """Remove a tattoo: drop the KihoAdv that granted it. Returns True
    when an entry was removed. Owns the dirty flag per the setter
    contract. A character bears any given tattoo at most once (the
    chooser filters out owned ones), so keying removal by id is
    unambiguous -- no opaque advancement handle needs to cross the UI
    boundary."""
    pc = get_context().pc
    if pc is None:
        return False
    target = None
    for adv in pc.advans or []:
        if adv.type == 'kiho' and getattr(adv, 'kiho', None) == tattoo_id:
            target = adv
            break
    if target is None:
        log.api.warning(u"remove_tattoo: character does not bear tattoo %s", tattoo_id)
        return False
    if api.character.remove_advancement(target):
        api.character.set_dirty_flag(True)
        return True
    return False
