#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""Server of zenref to handle Github Webhook"""
from __future__ import print_function, division, unicode_literals

import sys
import collections

import toml

from tornado import gen
from tornado import web
from tornado import httpserver
from tornado import ioloop
from tornado import log

from asyncat.client import AsyncGithubClient

from . import deployment


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


class Application(web.Application):
    """Application."""
    def __init__(self, config_file):
        """Use config file to initialize application."""
        with open(config_file) as f:
            self.config = toml.load(f)

        self._secret_builder_to_repo = collections.defaultdict(dict)

        for name, config in self.config["repo"].items():
            secret = config["secret"]
            builder = config.get("builder")

            self._secret_builder_to_repo[secret][builder] = name

        self._secrets_map = {
            config["secret"]: name
            for name, config in self.config["repo"].items()
        }

        access_token = self.config["github"]["access_token"]
        self.github_client = AsyncGithubClient(access_token)

        super(Application, self).__init__(
            [
                (r'/deployment', deployment.DeploymentHandler),
            ],
            **self.config["server"])

    def find_repo_config(self, secret, builder=None):
        """Use secret and builder to find repo config."""
        name = self._secret_builder_to_repo[secret][builder]
        return self.config["repo"][name]

    def find_pull(self, repo, sha):
        """Find pull request in repository via commit sha.

        :rtype: :class:`asyncat.repository.PullRequest`
        """
        return PullRequestFinder(repo, sha).find()


def main():
    app = Application(sys.argv[1])

    http_server = httpserver.HTTPServer(app)
    address, port = app.config["server"]["listen"].split(":")
    http_server.listen(int(port), address)
    http_server.start()
    print("Start server on {}".format(app.config["server"]["listen"]))
    log.enable_pretty_logging()
    ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()      # pragma: no cover
