#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""Tests of deployment."""
from __future__ import print_function, division, unicode_literals

import mock

from . import HindsightTestCase


class BuildbotTestCase(HindsightTestCase):
    def _get_packets(self):
        with open(self.get_file_path("_buildbot-packets.json")) as f:
            return f.read()

    def test_secret_mismatch(self):
        resp = self.fetch("/deployment", body=self.make_body({
            "secret": "secret",
            "packets": self._get_packets()
        }), method="POST")
        self.assertEqual(resp.code, 403)

    @mock.patch("hindsight.deployment.DeploymentHandler._find_pull",
                autospec=True)
    def test_pull_not_found(self, mock_find_pull):
        mock_find_pull.return_value = self.make_future(ValueError())

        resp = self.fetch("/deployment", body=self.make_body({
            "secret": "mock-secret",
            "packets": self._get_packets()
        }), method="POST")
        self.assertEqual(resp.code, 200)
        self.assertEqual(resp.body, b'OK')
