# -*- coding: utf-8 -*-
# Copyright (C) 2014-2026 Daniele Simonetti
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# QML image provider that renders a QR transfer frame to a QImage on
# demand. Registered on the engine as "qr" (see app.py); QML requests a
# frame with:
#
#     Image { source: "image://qr/" + encodeURIComponent(frameText) }
#
# The frame text (one line of the QR_IMPORT_FORMAT wire format) is the
# image id; QML URL-encodes it (the `|`, `+`, `/`, `=` in the frame are
# not URL-safe) and we decode it back here. Keying the cache by the frame
# text means each distinct frame is rendered once and reused as the
# animation loops.
#
# The QR *modules* are pure black on white for maximum camera-scan
# reliability -- the parchment / ink-on-paper styling of the surrounding
# card carries the design language (the symbol itself must stay
# high-contrast or phones struggle to lock on from a screen).

from io import BytesIO
from urllib.parse import unquote

import segno

from qtpy.QtCore import QSize
from qtpy.QtGui import QImage
from qtpy.QtQuick import QQuickImageProvider

from l5r.util import log

# Error-correction level M: a good balance for on-screen scanning (the
# spec's recommendation). border=4 is the mandatory QR quiet zone.
_ERROR_LEVEL = u"m"
_QUIET_ZONE = 4
# Fallback symbol size when QML asks without a requestedSize.
_DEFAULT_PX = 360


class QrImageProvider(QQuickImageProvider):
    """Renders ``image://qr/<url-encoded-frame-text>`` to a black/white QR."""

    def __init__(self):
        super().__init__(QQuickImageProvider.ImageType.Image)

    def requestImage(self, id, requestedSize):
        text = unquote(id or u"")
        # An empty id (no character / no frames) yields a blank tile rather
        # than throwing -- QML guards against this, but be defensive.
        if not text:
            return QImage(), QSize(0, 0)

        try:
            qr = segno.make(text, error=_ERROR_LEVEL)
        except Exception as err:  # pragma: no cover - segno is robust
            log.app.error(u"QML UI: QR render failed: %s", err)
            return QImage(), QSize(0, 0)

        # Pick an integer module scale so the rendered symbol is at least
        # the requested edge (Image downsamples smoothly if it overshoots);
        # integer scaling keeps modules crisp and uniformly sized.
        target = requestedSize.width() if (
            requestedSize is not None and requestedSize.width() > 0) else _DEFAULT_PX
        modules = qr.symbol_size(scale=1, border=_QUIET_ZONE)[0]
        scale = max(1, -(-target // modules))  # ceil division

        # segno writes a PNG into any binary file-like object. Pure black
        # on white for scan reliability.
        buf = BytesIO()
        qr.save(buf, kind=u"png", scale=scale, border=_QUIET_ZONE,
                dark=u"#000000", light=u"#ffffff")

        img = QImage()
        img.loadFromData(buf.getvalue(), u"PNG")
        return img, QSize(img.width(), img.height())
