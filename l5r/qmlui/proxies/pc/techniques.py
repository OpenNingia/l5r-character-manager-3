# -*- coding: utf-8 -*-
# Copyright (C) 2014-2026 Daniele Simonetti
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Techniques slice of PcProxy: the school techniques the character has
# learned, projected for TechniquesSection.qml.
#
# Techniques are not bought directly -- a character gains exactly one
# per insight rank as a consequence of school-rank advancement. So this
# slice is read-only (no AppController action); it mirrors the legacy
# TechViewModel, which walks insight ranks 1..9 and asks the schools API
# which technique was learned at each. Doing it that way (rather than
# enumerating a school's techs) lets api.character.schools.get_tech_by_rank
# resolve alternate-path replacements for us.
#
# A coarse `techniquesChanged` signal fires on character_refreshed and
# model_replaced, mirroring SkillsMixin.

from qtpy.QtCore import Property, Signal

import l5r.api as api
import l5r.api.character
import l5r.api.character.schools
import l5r.api.data
import l5r.api.data.schools

from l5r.qmlui.proxies.pc.memo import invalidate, memoize
from l5r.util import log


# Highest insight rank to probe. The legacy TechViewModel uses the same
# 1..9 window; ranks beyond a school's length simply return no tech.
_MAX_INSIGHT_RANK = 10


class TechniquesMixin:
    techniquesChanged = Signal()

    def _wire_techniques(self, bus):
        bus.character_refreshed.connect(self._on_character_refreshed_techniques)
        bus.model_replaced.connect(self._on_model_replaced_techniques)

    def _on_character_refreshed_techniques(self):
        invalidate(self, "techniques")
        self.techniquesChanged.emit()

    def _on_model_replaced_techniques(self):
        invalidate(self, "techniques")
        self.techniquesChanged.emit()

    @Property("QVariantList", notify=techniquesChanged)
    @memoize
    def techniques(self):
        pc = api.character.model()
        if not pc:
            return []

        rows = []
        for insight_rank in range(1, _MAX_INSIGHT_RANK):
            try:
                tech_id = api.character.schools.get_tech_by_rank(insight_rank)
                if not tech_id:
                    continue
                school, tech = api.data.schools.get_technique(tech_id)
            except Exception:
                # Datapack not loaded, or a character file referencing a
                # school/tech from a pack the user removed. Skip the row
                # rather than break the whole list.
                log.api.debug(
                    u"techniques proxy: could not resolve tech at insight %d",
                    insight_rank, exc_info=1)
                continue
            if not (school and tech):
                continue

            rows.append({
                "id":          tech_id,
                "name":        tech.name or "",
                "schoolName":  school.name or "",
                "schoolId":    school.id or "",
                # Insight rank at which the technique was gained (1..9).
                "insightRank": int(insight_rank),
                # The technique's own rank within its school.
                "techRank":    int(tech.rank) if tech.rank is not None else 0,
                "description": tech.desc or "",
            })
        return rows
