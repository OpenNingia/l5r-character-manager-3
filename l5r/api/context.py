# -*- coding: utf-8 -*-
# Copyright (C) 2014-2026 Daniele Simonetti
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# L5RCMContext — explicit holder for the mutable state the API layer
# operates on (active character, data store, locale, etc.). Introduced
# in Phase 5 of the 2026 modernization as the replacement for the
# module-level __api singleton in l5r/api/__init__.py.
#
# During the transition __api remains an instance of this class, and
# the l5r.api.character / l5r.api.data submodules still read it via the
# module-level alias. As call sites get migrated, they will pass a
# context explicitly instead.

import l5rdal as dal


class L5RCMContext:
    """Container for the L5RCM session state.

    Holds the active character model (``pc``), the loaded data store
    (``ds``), the active locale, the datapack blacklist, the in-flight
    rank advancement, and the translation provider.
    """

    def __init__(self, app=None):
        # character model
        self.pc = None

        # data access (l5rdal.Data)
        self.ds = None

        # culture locale
        self.locale = None

        # data pack blacklist
        self.blacklist = []

        # current rank advancement
        self.current_rank_adv = None

        # translation provider (anything with a .tr() method, typically the QApplication)
        self.translation_provider = app

    def reload(self, get_user_data_path):
        """Rebuild self.ds from the user's datapack directories.

        ``get_user_data_path`` is passed in from l5r/api/__init__.py to
        avoid a circular import; it returns the absolute path of a file
        under the user's L5RCM data directory.
        """
        locations = [get_user_data_path('core.data'),
                     get_user_data_path('data')]
        if self.locale:
            locations += [get_user_data_path('data.' + self.locale)]

        if not self.ds:
            self.ds = dal.Data(locations, self.blacklist)
        else:
            self.ds.rebuild(locations, self.blacklist)

    def tr(self, *args, **kwargs):
        if not self.translation_provider:
            return args[0]
        return self.translation_provider.tr(*args, **kwargs)
