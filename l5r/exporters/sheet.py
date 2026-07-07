# -*- coding: utf-8 -*-
# Copyright (C) 2014-2026 Daniele Simonetti
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# UI-agnostic PDF sheet export. Factored out of l5rcmcore.L5RCMCore so the
# QWidget and QML front-ends share ONE implementation instead of each
# re-deriving the multi-template fill / flatten / merge dance.
#
# The character data the FDF exporters need still comes from a `form`
# object (they read it via ``set_form``). The legacy QWidget passes its
# main window (its live view-models + labels); any other caller passes a
# ModelExportForm built from the active character (see
# l5r.exporters.model_form), which export_pdf also constructs by default.

import os
import shutil
from tempfile import mkstemp
from types import NoneType

from pypdf import PdfReader, PdfWriter
from pypdf.generic import ArrayObject, NameObject

import l5r.api as api
import l5r.api.character
import l5r.api.character.powers
import l5r.api.character.skills
import l5r.api.character.spells
import l5r.models as models

from l5r.exporters.fdfexporter import (
    FDFExporterAll,
    FDFExporterBushi,
    FDFExporterCourtier,
    FDFExporterMonk,
    FDFExporterShugenja,
    FDFExporterSkills,
    FDFExporterSpells,
    FDFExporterWeapons,
)
from l5r.exporters.npc import FDFExporterTwoNPC
from l5r.exporters.model_form import ModelExportForm
from l5r.util import log
from l5r.util.fsutil import get_app_file


# --- low-level pdf helpers (moved verbatim from L5RCMCore) ---------------

def _create_form_fields(form, exporter):
    exporter.set_form(form)
    exporter.set_model(api.character.model())
    return exporter.get_fields()

def _strip_form_widgets(writer, exception_list=None):
    """Remove form widget annotations and /AcroForm from a flattened PDF.

    pypdf's ``update_page_form_field_values(..., flatten=True)`` bakes the
    appearance stream into the page contents but leaves the widget
    annotations in place, so the now-empty field overlays still render on
    top. Drop them to get a truly flattened, no-form output.
    """
    if exception_list is None: exception_list = []

    for p in writer.pages:
        if "/Annots" not in p:
            continue
        kept = []
        for a in p["/Annots"]:
            obj = a.get_object()
            fieldName = obj.get("/T")
            if obj.get("/Subtype") != "/Widget" or fieldName in exception_list:
                kept.append(a)
        p[NameObject("/Annots")] = ArrayObject(kept)
    if "/AcroForm" in writer._root_object:
        del writer._root_object[NameObject("/AcroForm")]


def _fill_pdf(form_fields, source_pdf, target_pdf, target_suffix=None, exception_list=None):
    basen = os.path.splitext(os.path.basename(target_pdf))[0]
    based = os.path.dirname(target_pdf)

    if target_suffix:
        target_pdf = os.path.join(based, basen) + '_%s.pdf' % target_suffix
    else:
        target_pdf = os.path.join(based, basen) + '.pdf'

    reader = PdfReader(source_pdf)
    writer = PdfWriter()
    writer.append(reader)

    writer.update_page_form_field_values(
        None,
        form_fields,
        auto_regenerate=False,
        flatten=True,
    )

    _strip_form_widgets(writer,exception_list)

    with open(target_pdf, "wb") as output_stream:
        writer.write(output_stream)

    log.app.info('created pdf %s', target_pdf)
    return True


def _try_remove(fpath):
    try:
        os.remove(fpath)
        log.app.debug('deleted temp file: {0}'.format(fpath))
    except Exception:
        log.app.error('cannot delete temp file: {0}'.format(fpath),
                      exc_info=1, stack_info=True)


def _merge_pdf(input_files, output_file):
    try:
        merger = PdfWriter()
        for pdf in input_files:
            merger.append(pdf)
        merger.write(output_file)
        merger.close()
    finally:
        for f in input_files:
            _try_remove(f)


def _write_pdf(form, source, exporter, temp_files):
    source_pdf = get_app_file(source)
    form_fields = _create_form_fields(form, exporter)
    exception_list = []

    fd, fpath = mkstemp(suffix='.pdf')
    os.fdopen(fd, 'wb').close()
    
    if type(exporter) is FDFExporterShugenja: 
        exception_list = exporter.get_unused_spell_slots()

    _fill_pdf(form_fields, source_pdf, fpath, exception_list=exception_list)
    temp_files.append(fpath)


def _commit(temp_files, export_file):
    if os.path.exists(export_file):
        os.remove(export_file)

    if len(temp_files) > 1:
        _merge_pdf(temp_files, export_file)
    elif len(temp_files) == 1:
        shutil.move(temp_files[0], export_file)


# --- public API ----------------------------------------------------------

def export_pdf(export_file, form=None):
    """Render the active character to ``export_file`` (a .pdf path).

    Mirrors the legacy ``L5RCMCore.export_as_pdf`` exactly: a generic sheet,
    then a class-specific sheet, plus extra spell / skill / weapon pages as
    the character needs them, each flattened and merged into one document.

    ``form`` feeds the FDF exporters; pass ``None`` to build a
    ModelExportForm from the active character (the headless / QML path).
    """
    if form is None:
        form = ModelExportForm()

    pc = api.character.model()
    temp_files = []

    # GENERIC SHEET
    _write_pdf(form, 'sheet_all.pdf', FDFExporterAll(), temp_files)

    # SAMURAI MONKS ALSO FIT IN THE BUSHI CHARACTER SHEET
    is_monk, is_brotherhood = api.character.is_monk()
    is_samurai_monk = is_monk and not is_brotherhood
    is_shugenja = api.character.is_shugenja()
    is_bushi = api.character.is_bushi()
    is_courtier = api.character.is_courtier()
    is_ninja = api.character.is_ninja()
    spell_offset = 0
    spell_count = len(api.character.spells.get_all())
    kihos = api.character.powers.get_all_kiho()
    kiho_count = min(12, len(kihos))

    # SHUGENJA/BUSHI/MONK SHEET
    if is_shugenja:
        _write_pdf(form, 'sheet_shugenja.pdf', FDFExporterShugenja(), temp_files)
    elif is_bushi:
        _write_pdf(form, 'sheet_bushi.pdf', FDFExporterBushi(), temp_files)
    elif is_ninja:
        _write_pdf(form, 'sheet_bushi.pdf', FDFExporterBushi(), temp_files)
    elif is_samurai_monk:
        _write_pdf(form, 'sheet_bushi.pdf', FDFExporterBushi(), temp_files)
    elif is_monk:
        _write_pdf(form, 'sheet_monk.pdf', FDFExporterMonk(), temp_files)
    elif is_courtier:
        _write_pdf(form, 'sheet_courtier.pdf', FDFExporterCourtier(), temp_files)

    if kiho_count > 0:
        _write_pdf(form, 'sheet_monk.pdf', FDFExporterMonk(), temp_files)

    # SPELLS -- as many extra spell sheets as needed
    if is_shugenja:
        while spell_count > 0:
            _exporter = FDFExporterSpells(spell_offset)
            _write_pdf(form, 'sheet_spells.pdf', _exporter, temp_files)
            spell_offset += _exporter.spell_per_page
            spell_count -= _exporter.spell_per_page

    # DEDICATED SKILL SHEET
    skill_count = len(api.character.skills.get_all())
    skill_offset = 0
    while skill_count > 0:
        _exporter = FDFExporterSkills(skill_offset)
        _write_pdf(form, 'sheet_skill.pdf', _exporter, temp_files)
        skill_offset += _exporter.skills_per_page
        skill_count -= _exporter.skills_per_page

    # WEAPONS
    weapons_count = len(pc.weapons)
    weapons_offset = 0
    if weapons_count > 2:
        while weapons_count > 0:
            _exporter = FDFExporterWeapons(weapons_offset)
            _write_pdf(form, 'sheet_weapons.pdf', _exporter, temp_files)
            weapons_offset += _exporter.weapons_per_page
            weapons_count -= _exporter.weapons_per_page

    _commit(temp_files, export_file)


def export_npc(npc_files, export_file, form=None):
    """Render NPC sheets (two per page) from saved character files.

    ``FDFExporterTwoNPC`` swaps the active model to each NPC as it builds
    fields (it ignores ``form``), so this leaves the last NPC as the active
    model -- same behaviour as the legacy path.
    """
    temp_files = []

    pcs = []
    for f in npc_files:
        c = l5r.models.AdvancedPcModel()
        if c.load_from(f):
            pcs.append(c)

    _write_pdf(form, 'sheet_npc.pdf', FDFExporterTwoNPC(pcs), temp_files)
    _commit(temp_files, export_file)
