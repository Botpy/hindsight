#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""Tests of deployment."""
from __future__ import print_function, division, unicode_literals

import mock

from asyncat.client import GithubError

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

    @mock.patch("hindsight.deployment.DeploymentHandler._find_pull",
                autospec=True)
    def test_pull_not_found(self, mock_find_pull):
        mock_find_pull.return_value = self.make_future(ValueError())

        resp = self._push()
        self.assertEqual(resp.code, 200)
        self.assertEqual(resp.body, b'OK')

        mock_find_pull.return_value = self.make_future(GithubError())
        resp = self._push()
        self.assertEqual(resp.code, 404)

    @mock.patch("hindsight.deployment.Repository", autospec=True)
    def test_find_pull_via_sha(self, mock_repo_cls):
        mock_repo = mock_repo_cls.return_value
        mock_repo.owner = "owner"
        mock_repo.label = "repo-label"

        resp = mock.create_autospec("tornado.httpclient.HTTPResponse")
        resp.data = {
            "total_count": 1,
            "items": [
                {
                    "number": 1
                }
            ]
        }
        mock_repo.search_pulls.return_value = self.make_future(resp)

        mock_pull_cls = mock.create_autospec("asyncat.repository.PullRequest")
        mock_pull = mock_pull_cls.return_value

        mock_repo.pull.return_value = self.make_future(mock_pull)
        mock_pull.create_comment.return_value = self.make_future(None)

        self._push()

        sha = '235f37b19e0cf864e2801714d0392bfe42025b72'
        mock_repo.search_pulls.assert_called_with(sha)
        mock_repo.pull.assert_called_with(1)
        self.assertTrue(mock_pull.create_comment.called)
