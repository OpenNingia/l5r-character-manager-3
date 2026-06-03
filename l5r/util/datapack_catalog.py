# -*- coding: utf-8 -*-
# Copyright (C) 2014-2026 Daniele Simonetti
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Official datapack catalogue + downloader. Talks to the GitHub Releases
# API of the canonical datapack repository and streams .l5rcmpack assets
# to a temp file for the Library section to import.
#
# Stdlib ``urllib.request`` only -- the network surface here is two small
# functions, so a heavyweight HTTP dependency (requests + urllib3 +
# certifi + idna ...) would only add bundling weight to the cx_Freeze /
# AppImage / .deb builds for a cosmetic gain. TLS certificates are
# verified by urllib's default opener on every supported platform.
#
# Trust model: we only ever fetch from the pinned GitHub API URL, and the
# download URLs we follow come from GitHub's own JSON response (not user
# input). A final-host check after the redirect keeps a tampered release
# from steering the download to an arbitrary host (the practical
# mitigation for the ZIP-slip in l5rdal's extractall).

import json
import os
import re
import tempfile
import urllib.error
import urllib.request
from urllib.parse import urlparse

from l5r.util import log


# Canonical source. Only this repo's releases are offered (the user chose
# "official repository only" -- no custom URLs).
OFFICIAL_REPO = "OpenNingia/l5rcm-data-packs"
RELEASES_API = (
    "https://api.github.com/repos/%s/releases/latest" % OFFICIAL_REPO)

# Hosts we will talk to. The API lives on api.github.com; release assets
# 302-redirect from github.com to githubusercontent storage hosts.
ALLOWED_HOSTS = frozenset({
    "api.github.com",
    "github.com",
    "objects.githubusercontent.com",
    "release-assets.githubusercontent.com",
    "codeload.github.com",
})

HTTP_TIMEOUT = 15  # seconds, per request
# GitHub rejects API requests that carry no User-Agent.
USER_AGENT = "L5RCM-datapack-catalog"

_PACK_SUFFIXES = (".l5rcmpack", ".zip")
# "core_pack-5.0.l5rcmpack" -> "5.0"
_VERSION_RE = re.compile(r"-(\d[\d.]*)\.(?:l5rcmpack|zip)$", re.IGNORECASE)


class CatalogError(Exception):
    """Base for catalogue/download failures the proxy maps to a message."""


class RateLimitError(CatalogError):
    """GitHub returned 403 with the rate-limit headers exhausted."""


class OfflineError(CatalogError):
    """Could not reach the host (DNS / connection / timeout)."""


def host_allowed(url):
    """True when ``url``'s host is in the allow-list."""
    try:
        host = (urlparse(url).hostname or "").lower()
    except Exception:
        return False
    return host in ALLOWED_HOSTS


def parse_version(asset_name):
    """Extract the version from an asset filename, or "" if absent."""
    m = _VERSION_RE.search(asset_name or "")
    return m.group(1) if m else ""


def _request(url):
    return urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/vnd.github+json",
        },
    )


def _is_rate_limited(http_error):
    """A 403 whose X-RateLimit-Remaining header is 0 is a rate limit, not
    a permissions problem."""
    if http_error.code != 403:
        return False
    remaining = http_error.headers.get("X-RateLimit-Remaining")
    return remaining == "0" or remaining is None


def fetch_catalog():
    """Return the official datapacks as ``[{name, version, url, size}]``.

    Sorted Core-first, then alphabetically. Raises ``RateLimitError`` /
    ``OfflineError`` / ``CatalogError`` on failure -- never returns an
    empty list to mean "couldn't reach", so the caller can tell a genuine
    empty release from a network problem.
    """
    if not host_allowed(RELEASES_API):
        raise CatalogError("releases API host is not allow-listed")

    try:
        with urllib.request.urlopen(_request(RELEASES_API),
                                    timeout=HTTP_TIMEOUT) as resp:
            payload = json.load(resp)
    except urllib.error.HTTPError as ex:
        if _is_rate_limited(ex):
            log.app.warning(u"datapack catalog: GitHub rate limit hit")
            raise RateLimitError(str(ex))
        log.app.warning(u"datapack catalog: HTTP %s", ex.code)
        raise CatalogError("HTTP %s" % ex.code)
    except urllib.error.URLError as ex:
        log.app.warning(u"datapack catalog: offline (%s)", ex.reason)
        raise OfflineError(str(ex.reason))
    except (TimeoutError, OSError) as ex:
        log.app.warning(u"datapack catalog: connection error (%s)", ex)
        raise OfflineError(str(ex))
    except json.JSONDecodeError as ex:
        log.app.warning(u"datapack catalog: bad JSON (%s)", ex)
        raise CatalogError("malformed response")

    entries = []
    for asset in payload.get("assets", []) or []:
        name = asset.get("name", "")
        if not name.lower().endswith(_PACK_SUFFIXES):
            continue
        url = asset.get("browser_download_url", "")
        if not url:
            continue
        entries.append({
            "name": name,
            "version": parse_version(name),
            "url": url,
            "size": int(asset.get("size", 0) or 0),
        })

    entries.sort(key=lambda e: (not e["name"].lower().startswith("core"),
                                e["name"].lower()))
    log.app.info(u"datapack catalog: %d assets available", len(entries))
    return entries


def download_to_temp(url, progress_cb=None):
    """Stream ``url`` to a temp .l5rcmpack file and return its path.

    The caller owns the returned file (imports it, then deletes it).
    ``progress_cb(done_bytes, total_bytes)`` is called as bytes arrive
    (total is 0 when the server sends no Content-Length).

    The initial host is checked up front and, after urllib follows
    GitHub's redirect, the *final* host is re-checked -- the download URL
    came from the pinned API, so this guards against a tampered release
    redirecting us off the allow-listed hosts.
    """
    if not host_allowed(url):
        raise CatalogError("download host is not allow-listed")

    fd, tmp_path = tempfile.mkstemp(suffix=".l5rcmpack")
    try:
        with os.fdopen(fd, "wb") as out:
            try:
                resp = urllib.request.urlopen(_request(url),
                                              timeout=HTTP_TIMEOUT)
            except urllib.error.HTTPError as ex:
                if _is_rate_limited(ex):
                    raise RateLimitError(str(ex))
                raise CatalogError("HTTP %s" % ex.code)
            except urllib.error.URLError as ex:
                raise OfflineError(str(ex.reason))
            except (TimeoutError, OSError) as ex:
                raise OfflineError(str(ex))

            with resp:
                # Re-validate where we actually ended up after redirects.
                if not host_allowed(resp.geturl()):
                    raise CatalogError("redirected to a non-allow-listed host")
                total = int(resp.headers.get("Content-Length", 0) or 0)
                done = 0
                while True:
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    out.write(chunk)
                    done += len(chunk)
                    if progress_cb:
                        progress_cb(done, total)
    except BaseException:
        # Don't leak a half-written temp file on any failure.
        try:
            os.remove(tmp_path)
        except OSError:
            pass
        raise

    log.app.info(u"datapack catalog: downloaded %s (%d bytes)", url,
                 os.path.getsize(tmp_path))
    return tmp_path
