# -*- coding: utf-8 -*-
# Copyright (C) 2014-2026 Daniele Simonetti
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Shared SimpleDescriptionDialog helpers used by the spell / tech /
# kata / kiho / skill double-click handlers. Lifted from
# l5r/sinks/sink_4.py during Phase 4.5 so each sink can call it.

import l5r.api as api
import l5r.api.data
import l5r.widgets as widgets


def get_element_ring_text(item):
    """Return the localized ring name for ``item.element``, or the raw
    string if no ring matches."""
    ring_ = api.data.get_ring(item.element)
    if not ring_:
        return item.element
    return ring_.text


def show_description_dialog(parent, title, subtitle, desc):
    """Pop up a SimpleDescriptionDialog with the given title / subtitle
    / body content."""
    dlg = widgets.SimpleDescriptionDialog(parent)
    dlg.description().set_title(title)
    dlg.description().set_subtitle(subtitle)
    dlg.description().set_content(desc)
    dlg.exec_()
