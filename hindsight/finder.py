#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""Pull request finder."""
from __future__ import print_function, division, unicode_literals

from tornado import gen
from tornado import log


class NoSuchPullRequest(Exception):
    pass


class PullRequestFinder(object):
    """Find pull request via commit sha."""
    def __init__(self, repo, sha):
        """Initialize

        :type repo: :class:`asyncat.repository.Repository`
        :param str sha: commit sha
        """
        self.repo = repo
        self.sha = sha

    @gen.coroutine
    def _find(self, sha):
        """Find pull reuqest via commit sha.

        :param str sha: commit sha
        :rtype: :class:`asyncat.Repository.PullRequest`
        """
        # Try use build's sha to find pull request.
        resp = yield self.repo.search_pulls(sha)
        if resp.data["total_count"] == 1:
            pull = yield self.repo.pull(resp.data["items"][0]["number"])
            raise gen.Return(pull)

    @gen.coroutine
    def find(self):
        pull = yield self._find(self.sha)

        if pull is None:
            # Try use parent commit to find pull request.
            commit = yield self.repo.commit(self.sha)

            # The current commit is merge commit if that have two parents,
            # if so use the last one to find the pull requeust, because
            # the extra merge commit can also merge the pull request.
            if len(commit.c["parents"]) == 2:
                parent = commit.c["parents"][1]
                log.gen_log.info("Try use <%s> parent commit <%s> find pull",
                                 self.sha, parent["sha"])
                pull = yield self._find(parent["sha"])

        if pull is None:
            exc = NoSuchPullRequest(self.sha)
        else:
            exc = gen.Return(pull)

        raise exc
