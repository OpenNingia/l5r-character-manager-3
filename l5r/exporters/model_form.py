# -*- coding: utf-8 -*-
# Copyright (C) 2014-2026 Daniele Simonetti
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# UI-agnostic stand-in for the QWidget main window that the FDF exporters
# read character data from (``set_form``). The exporters pull a handful of
# things off the form: the clan / family / school labels, the three
# initiative fields, the free-text notes, and seven Qt view-models
# (merits, flaws, melee / ranged / arrow weapons, skills, spells).
#
# ModelExportForm rebuilds all of that from the *active character* via the
# api + the same view-model classes the QWidget tabs use, so the QML front
# end (or any headless caller) can drive l5r.exporters.sheet without a
# QWidget. The QWidget path keeps passing its live window unchanged.

from qtpy.QtGui import QTextDocument

import l5r.api as api
import l5r.api.character
import l5r.api.character.schools
import l5r.api.data.clans
import l5r.api.data.families
import l5r.api.data.schools
import l5r.api.rules
import l5r.models as models


class _Text(object):
    """Minimal stand-in for the QWidget labels / read-only text fields the
    exporters read via ``.text()`` / ``.get_plain_text()``."""

    __slots__ = ("_value",)

    def __init__(self, value):
        self._value = value or ""

    def text(self):
        return self._value

    def get_plain_text(self):
        return self._value


def _clan_name():
    clan_ = api.data.clans.get(api.character.get_clan())
    return clan_.name if clan_ else ""


def _family_name():
    family_ = api.data.families.get(api.character.get_family())
    return family_.name if family_ else ""


def _school_name():
    sid = api.character.schools.get_first()
    if not sid:
        return ""
    school_ = api.data.schools.get(sid)
    return school_.name if school_ else ""


def _plain_text(html):
    """Strip rich-text markup the way the QWidget notes editor does.

    pc.extra_notes is stored as HTML (the editor's ``toHtml()``); the FDF
    exporter wants plain text. The QWidget path gets it via
    ``QTextEdit.toPlainText()`` -- replicate that exactly with a throwaway
    QTextDocument so the QML/headless export matches and no raw HTML leaks
    into the sheet.
    """
    if not html:
        return ""
    doc = QTextDocument()
    doc.setHtml(html)
    return doc.toPlainText()


class ModelExportForm(object):
    """Duck-typed `form` for the FDF exporters, built from the active PC.

    NB: the view-models are QObjects -- construct this on the GUI thread
    (the QML export slot does) and hand it to the export worker, mirroring
    how the QWidget's own view-models live on the GUI thread while the
    fill / merge runs on a worker.
    """

    def __init__(self):
        pc = api.character.model()

        # clan / family / school (FDFExporter.get_*_name read these labels)
        self.lb_pc_clan = _Text(_clan_name())
        self.lb_pc_family = _Text(_family_name())
        self.lb_pc_school = _Text(_school_name())

        # initiative -- same source as l5r.ui.refresh
        self.tx_base_init = _Text(
            api.rules.format_rtk_t(api.rules.get_base_initiative()))
        self.tx_mod_init = _Text(
            api.rules.format_rtk_t(api.rules.get_init_modifiers()))
        self.tx_cur_init = _Text(
            api.rules.format_rtk_t(api.rules.get_tot_initiative()))

        # free-text notes -- stored as HTML; strip to plain text (see above)
        self.tx_pc_notes = _Text(_plain_text(pc.extra_notes if pc else ""))

        # view-models, populated from the active character (the same classes
        # the QWidget tabs build; parentless since they're transient here)
        self.merits_view_model = self._build(models.PerkViewModel('merit'), pc)
        self.flaws_view_model = self._build(models.PerkViewModel('flaws'), pc)
        self.melee_view_model = self._build(
            models.WeaponTableViewModel('melee', None), pc)
        self.ranged_view_model = self._build(
            models.WeaponTableViewModel('ranged', None), pc)
        self.arrow_view_model = self._build(
            models.WeaponTableViewModel('arrow', None), pc)
        self.sk_view_model = self._build(models.SkillTableViewModel(None), pc)
        self.sp_view_model = self._build(models.SpellTableViewModel(None), pc)

    @staticmethod
    def _build(view_model, pc):
        view_model.update_from_model(pc)
        return view_model
