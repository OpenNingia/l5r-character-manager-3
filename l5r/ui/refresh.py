# -*- coding: utf-8 -*-
# Copyright (C) 2014-2026 Daniele Simonetti
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Master model -> UI refresh routine. Extracted from l5r/main.py during
# the Phase 4 split — no behaviour changes. Touches widgets across many
# tabs (each tab mixin owns those widgets); update_from_model is the
# orchestrator that pushes the current PC + rules state into the UI
# after any state-changing action.

import l5r.api as api
import l5r.api.character
import l5r.api.character.spells
import l5r.api.data
import l5r.api.rules

from l5r.l5rcmcore.qtsignalsutils import QtSignalLock


class ModelRefreshMixin:
    """The big update_from_model orchestrator."""

    def update_from_model(self):

        with QtSignalLock(self.pers_info_widgets + [self.tx_pc_name]):

            self.tx_pc_name.setText(self.pc.name)
            self.set_clan(self.pc.clan)
            self.set_family(api.character.get_family())
            self.set_school(api.character.schools.get_current())

            for w in self.pers_info_widgets:
                if hasattr(w, 'link'):
                    w.setText(self.pc.get_property(w.link))

        pc_xp = api.character.xp()
        self.tx_pc_exp.setText('{0} / {1}'.format(pc_xp, api.character.xp_limit()))

        # rings
        for i, r in enumerate(api.data.rings()):
            self.rings[i][1].setText(str(api.character.ring_rank(r)))

        # traits
        for i, t in enumerate(api.data.traits()):
            self.attribs[i][1].setText(str(api.character.trait_rank(t)))

        # pc rank
        self.tx_pc_rank.setText(str(api.character.insight_rank()))
        self.tx_pc_ins .setText(str(api.character.insight()))

        # pc flags
        with QtSignalLock(self.pc_flags_points + self.pc_flags_rank + [self.void_points]):

            self.set_honor(api.character.honor())
            self.set_glory(api.character.glory())
            self.set_infamy(api.character.infamy())
            self.set_status(api.character.status())
            self.set_taint(api.character.taint())

            self.set_void_points(self.pc.void_points)

        # armor
        self.tx_armor_nm .setText(str(api.character.get_armor_name()))
        self.tx_base_tn  .setText(str(api.character.get_base_tn()))
        self.tx_armor_tn .setText(str(api.character.get_armor_tn()))
        self.tx_armor_rd .setText(str(api.character.get_full_rd()))
        self.tx_cur_tn   .setText(str(api.character.get_full_tn()))
        # armor description
        self.tx_armor_nm.setToolTip(str(api.character.get_armor_desc()))

        self.display_health()
        self.update_wound_penalties()
        self.wnd_lb.setTitle(
            self.tr("Health / Wounds (x%d)") % self.pc.health_multiplier)

        # initiative
        self.tx_base_init.setText(
            api.rules.format_rtk_t(api.rules.get_base_initiative()))
        self.tx_mod_init.setText(
            api.rules.format_rtk_t(api.rules.get_init_modifiers()))
        self.tx_cur_init.setText(
            api.rules.format_rtk_t(api.rules.get_tot_initiative()))

        # affinity / deficiency
        affinities_ = []
        for a in api.character.spells.affinities():
            ring_ = api.data.get_ring(a)
            if not ring_:
                affinities_.append(a)
            else:
                affinities_.append(ring_.text)

        deficiencies_ = []
        for a in api.character.spells.deficiencies():
            ring_ = api.data.get_ring(a)
            if not ring_:
                deficiencies_.append(a)
            else:
                deficiencies_.append(ring_.text)

        self.lb_affin.setText(u', '.join(affinities_))
        self.lb_defic.setText(u', '.join(deficiencies_))

        # money
        with QtSignalLock([self.money_widget]):
            self.money_widget.set_value(api.character.get_money())

        self.hide_nicebar()

        self.check_new_skills()
        self.check_affinity_wc()
        self.check_rank_advancement()
        self.check_school_new_spells()
        self.check_free_kihos()

        # Origin (family/school) edits stay open until the first *paid*
        # advancement -- gating on spent XP, not the advancement count, so
        # choosing the school (which appends the cost-0 rank-1 advancement)
        # doesn't lock out the family, while still freezing the origin the
        # instant XP is spent (issue #448).
        can_edit_origin = api.character.can_edit_origin()
        self.bt_edit_family.setEnabled(can_edit_origin)
        self.bt_edit_school.setEnabled(can_edit_origin)

        # Update view-models
        self.sk_view_model    .update_from_model(self.pc)
        self.ma_view_model    .update_from_model(self.pc)
        self.adv_view_model   .update_from_model(self.pc)
        self.th_view_model    .update_from_model(self.pc)
        self.merits_view_model.update_from_model(self.pc)
        self.flaws_view_model .update_from_model(self.pc)
        self.sp_view_model    .update_from_model(self.pc)
        self.melee_view_model .update_from_model(self.pc)
        self.ranged_view_model.update_from_model(self.pc)
        self.arrow_view_model .update_from_model(self.pc)
        self.mods_view_model  .update_from_model(self.pc)
        self.ka_view_model    .update_from_model(self.pc)
        self.ki_view_model    .update_from_model(self.pc)
        self.equip_view_model .update_from_model(self.pc)

        # update table views to fit new contents
        for v in self.table_views:
            v.setVisible(False)
            v.resizeColumnsToContents()
            v.setVisible(True)
