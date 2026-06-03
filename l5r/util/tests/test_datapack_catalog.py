# -*- coding: utf-8 -*-
# Tests for l5r.util.datapack_catalog (the official-repo catalogue + the
# host allow-list). No real network: urllib.request.urlopen is mocked.
__author__ = 'Daniele Simonetti'

import email.message
import io
import json
import unittest
import urllib.error
from unittest import mock

from l5r.util import datapack_catalog as cat


def _http_error(code, rate_remaining=None):
    hdrs = email.message.Message()
    if rate_remaining is not None:
        hdrs["X-RateLimit-Remaining"] = rate_remaining
    return urllib.error.HTTPError("http://x", code, "err", hdrs, None)


_SAMPLE = {
    "tag_name": "vTest",
    "assets": [
        {"name": "great_clan_pack-1.6.l5rcmpack",
         "browser_download_url": "https://github.com/o/r/great.l5rcmpack",
         "size": 222},
        {"name": "core_pack-5.0.l5rcmpack",
         "browser_download_url": "https://github.com/o/r/core.l5rcmpack",
         "size": 12345},
        {"name": "README.txt",
         "browser_download_url": "https://github.com/o/r/README.txt",
         "size": 10},
    ],
}


class TestParseVersion(unittest.TestCase):
    def test_parses(self):
        self.assertEqual("5.0", cat.parse_version("core_pack-5.0.l5rcmpack"))
        self.assertEqual("1.6", cat.parse_version("great_clan_pack-1.6.l5rcmpack"))
        self.assertEqual("1.2.3", cat.parse_version("x-1.2.3.zip"))

    def test_no_version(self):
        self.assertEqual("", cat.parse_version("weird.l5rcmpack"))
        self.assertEqual("", cat.parse_version(""))


class TestHostAllowed(unittest.TestCase):
    def test_allowed(self):
        self.assertTrue(cat.host_allowed(cat.RELEASES_API))
        self.assertTrue(cat.host_allowed("https://github.com/o/r/x.l5rcmpack"))
        self.assertTrue(cat.host_allowed(
            "https://objects.githubusercontent.com/x"))
        self.assertTrue(cat.host_allowed(
            "https://release-assets.githubusercontent.com/x"))

    def test_denied(self):
        self.assertFalse(cat.host_allowed("https://evil.example.com/x.l5rcmpack"))
        self.assertFalse(cat.host_allowed("not a url"))
        self.assertFalse(cat.host_allowed(""))


class TestFetchCatalog(unittest.TestCase):
    def test_filters_and_sorts_core_first(self):
        payload = io.BytesIO(json.dumps(_SAMPLE).encode("utf-8"))
        with mock.patch("urllib.request.urlopen", return_value=payload):
            entries = cat.fetch_catalog()

        # README.txt filtered out; two packs kept.
        self.assertEqual(2, len(entries))
        # Core sorts first.
        self.assertTrue(entries[0]["name"].startswith("core"))
        self.assertEqual("5.0", entries[0]["version"])
        self.assertEqual(12345, entries[0]["size"])
        self.assertTrue(entries[0]["url"].endswith("core.l5rcmpack"))
        self.assertEqual("great_clan_pack-1.6.l5rcmpack", entries[1]["name"])

    def test_rate_limit_raises(self):
        with mock.patch("urllib.request.urlopen",
                        side_effect=_http_error(403, rate_remaining="0")):
            with self.assertRaises(cat.RateLimitError):
                cat.fetch_catalog()

    def test_offline_raises(self):
        with mock.patch("urllib.request.urlopen",
                        side_effect=urllib.error.URLError("no network")):
            with self.assertRaises(cat.OfflineError):
                cat.fetch_catalog()

    def test_other_http_error_raises_catalog_error(self):
        with mock.patch("urllib.request.urlopen",
                        side_effect=_http_error(500)):
            with self.assertRaises(cat.CatalogError):
                cat.fetch_catalog()


if __name__ == "__main__":
    unittest.main()
