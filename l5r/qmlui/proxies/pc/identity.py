# -*- coding: utf-8 -*-
# Copyright (C) 2014-2026 Daniele Simonetti
#
# Identity slice of PcProxy: name, clan, family, first school, and the
# composite window-title string. Also exposes a `progression` bundle
# (insight, rank, XP, XP limit) -- everything that updates whenever the
# character's advancement history changes.

from qtpy.QtCore import Property, Signal

import l5r.api as api
import l5r.api.character
import l5r.api.character.schools
import l5r.api.data
import l5r.api.data.schools

from l5r.l5rcmcore import APP_DESC, APP_VERSION
from l5r.qmlui.proxies.pc.memo import invalidate, memoize


class IdentityMixin:
    nameChanged = Signal()
    clanChanged = Signal()
    familyChanged = Signal()
    schoolChanged = Signal()
    progressionChanged = Signal()
    displayTitleChanged = Signal()
    canEditOriginChanged = Signal()
    # Fires whenever the origin (family/clan/school) changes -- drives the
    # Character section's origin summary line and its family+school bonuses.
    originChanged = Signal()

    def _wire_identity(self, bus):
        bus.name_changed.connect(self._on_name_changed)
        bus.family_changed.connect(self._on_family_changed)
        bus.clan_changed.connect(self._on_clan_changed)
        bus.dirty_changed.connect(self._on_dirty_changed_for_title)
        bus.character_refreshed.connect(self._on_character_refreshed_identity)
        bus.model_replaced.connect(self._on_model_replaced_identity)

    def _on_name_changed(self, _value):
        self.nameChanged.emit()
        self.displayTitleChanged.emit()

    def _on_family_changed(self, _value):
        self.familyChanged.emit()
        # Family change recomputes school context-relative bits too.
        invalidate(self, "progression")
        self.progressionChanged.emit()
        self.canEditOriginChanged.emit()
        self.originChanged.emit()

    def _on_clan_changed(self, _value):
        self.clanChanged.emit()
        self.displayTitleChanged.emit()
        self.originChanged.emit()

    def _on_dirty_changed_for_title(self, _value):
        self.displayTitleChanged.emit()

    def _on_character_refreshed_identity(self):
        self.schoolChanged.emit()
        invalidate(self, "progression")
        self.progressionChanged.emit()
        self.canEditOriginChanged.emit()
        self.originChanged.emit()

    def _on_model_replaced_identity(self):
        self.nameChanged.emit()
        self.familyChanged.emit()
        self.clanChanged.emit()
        self.schoolChanged.emit()
        invalidate(self, "progression")
        self.progressionChanged.emit()
        self.displayTitleChanged.emit()
        self.canEditOriginChanged.emit()
        self.originChanged.emit()

    @Property(str, notify=nameChanged)
    def name(self):
        pc = api.character.model()
        return pc.name if pc else ""

    @Property(str, notify=familyChanged)
    def family(self):
        family_ = api.data.families.get(api.character.get_family())
        return family_.name if family_ else ""

    @Property(str, notify=clanChanged)
    def clan(self):
        clan_ = api.data.clans.get(api.character.get_clan())
        return clan_.name if clan_ else ""

    @Property(str, notify=clanChanged)
    def clanId(self):
        """Lowercase clan id (e.g. ``crane``), as opposed to ``clan``
        which is the localized display name. Drives ClanTheme.setClan
        on the QML side -- the §5 accent lookup keys on the id, not the
        translated name."""
        return api.character.get_clan() or ""

    @Property(str, notify=schoolChanged)
    def school(self):
        sid = api.character.schools.get_first()
        if not sid:
            return ""
        school_ = api.data.schools.get(sid)
        return school_.name if school_ else ""

    @Property(bool, notify=originChanged)
    def originComplete(self):
        """True once both a family (clan) and a first school are set."""
        return bool(api.character.get_family()
                    and api.character.schools.get_first())

    @Property(str, notify=originChanged)
    def familyTrait(self):
        """The +1 starting trait granted by the family, as a (lowercase)
        trait id -- "" when no family. The QML maps it to a localized label."""
        family_ = api.data.families.get(api.character.get_family())
        return (getattr(family_, "trait", "") or "") if family_ else ""

    @Property(str, notify=originChanged)
    def schoolTrait(self):
        """The +1 starting trait granted by the first school, as a trait id."""
        school_ = api.data.schools.get(api.character.schools.get_first())
        return (getattr(school_, "trait", "") or "") if school_ else ""

    @Property(bool, notify=canEditOriginChanged)
    def canEditOrigin(self):
        """Origin (clan/family/school) edits stay open until the first *paid*
        advancement -- api.character.can_edit_origin gates on spent XP, not the
        advancement count, so choosing the school (which appends the cost-0
        rank-1 advancement) doesn't lock out the family, while the origin still
        freezes the instant XP is spent (issue #448). Exposed as a NOTIFY
        property (not a one-shot Slot call) so the edit icons re-enable/disable
        when the active character is replaced or refreshed (issue #433)."""
        return bool(api.character.model() and api.character.can_edit_origin())

    @Property("QVariantMap", notify=progressionChanged)
    @memoize
    def progression(self):
        return {
            "insight": api.character.insight(),
            "rank": api.character.insight_rank(),
            "xp": api.character.xp(),
            "xpLimit": api.character.xp_limit(),
            "rawXpLimit": api.character.model().exp_limit
                if api.character.model() else 0,
        }

    @Property(str, notify=displayTitleChanged)
    def displayTitle(self):
        pc = api.character.model()
        base = "{} v{}".format(APP_DESC, APP_VERSION)
        if not pc or not pc.name:
            return base
        clan = api.character.get_clan() or ""
        body = "{} [{}]".format(pc.name, clan) if clan else pc.name
        suffix = " *" if pc.unsaved else ""
        return "{} — {}{}".format(base, body, suffix)
