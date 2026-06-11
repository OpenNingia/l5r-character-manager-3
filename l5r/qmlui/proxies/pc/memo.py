# -*- coding: utf-8 -*-
# Copyright (C) 2014-2026 Daniele Simonetti
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Memoization for PcProxy slice projections.
#
# QML reads a QVariantList / QVariantMap property through a live value
# wrapper, not a detached JS copy: every element access on the QML side
# (`xs.length`, `xs[i]`, `m.key`) re-invokes the Python getter. A section
# that loops over a projection therefore pays O(N) getter calls per
# refresh -- and without a cache each call rebuilds the projection from
# the advancement history, turning one purchase into an O(N^2) walk
# (root cause of the "seconds per advancement" freeze, 2026-06-11).
#
# The deal: getters serve a per-instance cached projection; the slice
# drops the cache right before emitting its notify signal, so QML never
# observes a stale value.

import functools


def memoize(fn):
    """Serve the projection built by ``fn`` from a per-instance cache.

    Stack between ``@Property`` and the getter::

        @Property("QVariantList", notify=thingsChanged)
        @memoize
        def things(self): ...

    Pair every ``thingsChanged.emit()`` with ``invalidate(self, "things")``
    in the emitting handler. Getters must return a non-None value ([] / {}
    sentinels are fine and are cached too -- any state change that could
    alter them also fires the notify signal, which invalidates).
    """
    slot = "_memo_" + fn.__name__

    @functools.wraps(fn)
    def wrapper(self):
        value = getattr(self, slot, None)
        if value is None:
            value = fn(self)
            setattr(self, slot, value)
        return value

    return wrapper


def invalidate(obj, *names):
    """Drop the cached projections for ``names`` (getter function names)."""
    for name in names:
        setattr(obj, "_memo_" + name, None)
