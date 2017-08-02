#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""Tests of deployment."""
from __future__ import print_function, division, unicode_literals

import mock

from asyncat.client import GithubError

from hindsight.finder import NoSuchPullRequest

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

    def _push(self):
        return self.fetch("/deployment", body=self.make_body({
            "secret": "mock-secret",
            "packets": self._get_packets()
        }), method="POST")

    @mock.patch("hindsight.app.Application.find_pull", autospec=True)
    def test_pull_not_found(self, mock_find_pull):
        mock_find_pull.return_value = self.make_future(NoSuchPullRequest())

        resp = self._push()
        self.assertEqual(resp.code, 200)
        self.assertEqual(resp.body, b'OK')

        mock_find_pull.return_value = self.make_future(GithubError())
        resp = self._push()
        self.assertEqual(resp.code, 404)

    @mock.patch("hindsight.finder.PullRequestFinder.find", autospec=True)
    def test_find_pull_via_sha(self, mock_find):
        mock_pull_cls = mock.create_autospec("asyncat.repository.PullRequest")
        mock_pull = mock_pull_cls.return_value
        mock_pull.create_comment.return_value = self.make_future(None)

        mock_find.return_value = self.make_future(mock_pull)

        self._push()

        self.assertTrue(mock_pull.create_comment.called)
