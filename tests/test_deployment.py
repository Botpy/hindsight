#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""Tests of deployment."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import base64

import mock

from asyncat.client import GithubError

from hindsight.finder import NoSuchPullRequest

from . import HindsightTestCase


class BuildbotTestCase(HindsightTestCase):
    """Tests for buildbot."""
    def _get_packets(self):
        """Returns test packets."""
        with open(self.get_file_path("_buildbot-packets.json")) as f:
            return f.read()

    def test_secret_mismatch(self):
        """Secret mismatch should returns 403."""
        resp = self.fetch("/deployment", body=self.make_body({
            "secret": "secret",
            "packets": self._get_packets()
        }), method="POST")
        self.assertEqual(resp.code, 403)

    def _push(self):
        """Push event."""
        return self.fetch("/deployment", body=self.make_body({
            "secret": "mock-secret",
            "packets": self._get_packets()
        }), method="POST")

    @mock.patch("hindsight.app.Application.find_pull", autospec=True)
    def test_pull_not_found(self, mock_find_pull):
        """Pull request not found."""
        mock_find_pull.return_value = self.make_future(NoSuchPullRequest())

        resp = self._push()
        self.assertEqual(resp.code, 200)
        self.assertEqual(resp.body, b'OK')

        mock_find_pull.return_value = self.make_future(GithubError())
        resp = self._push()
        self.assertEqual(resp.code, 404)

    @mock.patch("hindsight.finder.PullRequestFinder.find", autospec=True)
    def test_find_pull_via_sha(self, mock_find):
        """Find pull request via sha in event."""
        mock_pull_cls = mock.create_autospec("asyncat.repository.PullRequest")
        mock_pull = mock_pull_cls.return_value
        mock_pull.create_comment.return_value = self.make_future(None)

        mock_find.return_value = self.make_future(mock_pull)

        self._push()

        self.assertTrue(mock_pull.create_comment.called)


class Buildbot9TestCase(HindsightTestCase):
    """Buildbot 9 test case."""
    def _get_payload(self, type_="done"):
        """Returns test payload."""
        with open(self.get_file_path("_buildbot9-{}.json".format(type_))) as f:
            return f.read()

    def test_secret_mismatch(self):
        """Secret mismatch should returns 403."""
        resp = self.fetch(
            "/deployment",
            body=self._get_payload(),
            headers={
                "Authorization": "Basic {}".format(
                    base64.b64encode(
                        "buildbot:{}".format("secret").encode("utf8")
                    ).decode("utf8"),
                )
            },
            method="POST",
        )
        self.assertEqual(resp.code, 403)

    def _push(self, type_):
        """Push event."""
        return self.fetch(
            "/deployment",
            body=self._get_payload(type_),
            headers={
                "Authorization": "Basic {}".format(
                    base64.b64encode(
                        "buildbot:{}".format("mock-secret").encode("utf8"),
                    ).decode("utf8"),
                )
            },
            method="POST",
        )

    @mock.patch("hindsight.app.Application.find_pull", autospec=True)
    def test_pull_not_found(self, mock_find_pull):
        """Could not found pull request."""
        mock_find_pull.return_value = self.make_future(NoSuchPullRequest())

        resp = self._push("done")
        self.assertEqual(resp.code, 200)
        self.assertEqual(resp.body, b'OK')

        mock_find_pull.return_value = self.make_future(GithubError())
        resp = self._push("done")
        self.assertEqual(resp.code, 404)

    @mock.patch("hindsight.finder.PullRequestFinder.find", autospec=True)
    def test_find_pull_via_sha(self, mock_find):
        """Find pull request via sha in event."""
        mock_pull_cls = mock.create_autospec("asyncat.repository.PullRequest")
        mock_pull = mock_pull_cls.return_value
        mock_pull.create_comment.return_value = self.make_future(None)

        mock_find.return_value = self.make_future(mock_pull)

        self._push("done")

        self.assertTrue(mock_pull.create_comment.called)
