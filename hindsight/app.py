#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""Server of zenref to handle Github Webhook"""
from __future__ import print_function, division, unicode_literals

import sys
import collections

import toml

from tornado import web
from tornado import httpserver
from tornado import ioloop
from tornado import log

from asyncat.client import AsyncGithubClient

from . import deployment
from . import finder


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
        return finder.PullRequestFinder(repo, sha).find()


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
