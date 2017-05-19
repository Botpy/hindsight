#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""Application test cases."""
from __future__ import print_function, division, unicode_literals

import mock

from tornado import testing

from hindsight.app import PullRequestFinder, NoSuchPullRequest, main

from . import HindsightTestCase


class PullRequestFinderTestCase(HindsightTestCase):
    """Tests PullRequestFinder"""
    def setUp(self):
        """Override setUp."""
        super(PullRequestFinderTestCase, self).setUp()
        self.mock_repo_cls = mock.create_autospec(
            "asyncat.repository.Repository", autospec=True)

        self.mock_repo = self.mock_repo_cls.return_value
        self.mock_repo.owner = "owner"
        self.mock_repo.label = "repo-label"

        pull_spec = "asyncat.repository.PullRequest"
        self.mock_pull_cls = mock.create_autospec(pull_spec)
        self.mock_pull = self.mock_pull_cls.return_value

        self.mock_repo.pull.return_value = self.make_future(self.mock_pull)
        self.finder = PullRequestFinder(self.mock_repo, "sha")

    @testing.gen_test
    def test_find_via_sha(self):
        resp = mock.create_autospec("tornado.httpclient.HTTPResponse")
        resp.data = {
            "total_count": 1,
            "items": [
                {
                    "number": 1
                }
            ]
        }
        self.mock_repo.search_pulls.return_value = self.make_future(resp)
        resp = yield self.finder.find()
        self.mock_repo.search_pulls.assert_called_with("sha")
        self.mock_repo.pull.assert_called_with(1)

    @testing.gen_test
    def test_find_via_parent(self):
        def _search_side(sha):
            resp = mock.create_autospec("tornado.httpclient.HTTPResponse")

            if sha == "sha":
                resp.data = {"total_count": 0}
            else:
                resp.data = {
                    "total_count": 1,
                    "items": [
                        {
                            "number": 2
                        }
                    ]
                }
            return self.make_future(resp)

        self.mock_repo.search_pulls.side_effect = _search_side

        commit = mock.create_autospec("asyncat.repository.Commit")
        commit.c = {
            "parents": [
                {
                    "sha": "sha1"
                }
            ]
        }
        self.mock_repo.commit.return_value = self.make_future(commit)
        yield self.finder.find()
        self.mock_repo.search_pulls.assert_called_with("sha1")
        self.mock_repo.pull.assert_called_with(2)

    @testing.gen_test
    def test_not_found(self):
        resp = mock.create_autospec("tornado.httpclient.HTTPResponse")
        resp.data = {"total_count": 0}

        self.mock_repo.search_pulls.return_value = self.make_future(resp)

        commit = mock.create_autospec("asyncat.repository.Commit")
        commit.c = {"parents": []}
        self.mock_repo.commit.return_value = self.make_future(commit)

        with self.assertRaises(NoSuchPullRequest):
            yield self.finder.find()


def test_main():
    """Main fucntion."""
    import sys

    with mock.patch("hindsight.app.ioloop.IOLoop",
                    autospec=True) as mock_ioloop_cls:
        mock_ioloop = mock_ioloop_cls.return_value
        mock_ioloop_cls.current.return_value = mock_ioloop

        with mock.patch.object(sys, "argv", ["hindsight", "tests/cfg.toml"]):

            main()

        assert mock_ioloop.start.called
