# -*- coding: utf-8 -*-
# Copyright (C) 2014-2026 Daniele Simonetti
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# L5RCMContext — explicit holder for the mutable state the API layer
# operates on (active character, data store, locale, etc.).
#
# Introduced in Phase 5 of the 2026 modernization as the replacement
# for the old module-level singleton (``__api = L5RCMAPI()`` in
# l5r/api/__init__.py).
#
# How it's used:
#
#   * Production startup binds the default context once (in
#     l5r/api/__init__.py at import time): a fresh L5RCMContext is
#     pushed onto the ``_current`` ContextVar.
#
#   * API implementations (l5r.api.character.*, l5r.api.data.*,
#     l5r.api.rules.*) read it via ``get_context().X`` — no ctx is
#     threaded through call sites.
#
#   * Tests scope an isolated context with the ``use()`` context
#     manager:
#
#         with l5r.api.context.use(my_ctx):
#             api.character.set_family('doji')
#
#     Inside the ``with``, every API call reads from ``my_ctx``. On
#     exit, the previous context is restored. ContextVars are also
#     async-/thread-safe out of the box.

import contextlib
import contextvars
from typing import Iterator

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


# --- ContextVar machinery ---------------------------------------------------
#
# ``_current`` holds the active L5RCMContext for this Python execution
# context (thread, asyncio task, etc.). It is bound to a production
# L5RCMContext instance at import time in l5r/api/__init__.py, so any
# call to ``get_context()`` from production code returns that instance
# unless a ``use()`` block has scoped a different one.

_current: contextvars.ContextVar["L5RCMContext"] = contextvars.ContextVar("l5rcm_context")


def get_context() -> "L5RCMContext":
    """Return the active L5RCMContext.

    Raises LookupError if no context has been bound yet -- which in
    practice can only happen if ``l5r.api`` was never imported.
    """
    return _current.get()


@contextlib.contextmanager
def use(ctx: "L5RCMContext") -> Iterator["L5RCMContext"]:
    """Scope an alternative context for the duration of a block.

    Typical use is in tests::

        with l5r.api.context.use(my_ctx):
            api.character.set_family('doji')
            ...
        # the previous context is restored here

    Nesting is supported; the inner context wins until its ``with``
    block exits.
    """
    token = _current.set(ctx)
    try:
        yield ctx
    finally:
        _current.reset(token)
