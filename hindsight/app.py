#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""Server of zenref to handle Github Webhook"""
from __future__ import print_function, division, unicode_literals

import sys

import toml

from tornado import web
from tornado import httpserver
from tornado import ioloop
from tornado import log

from asycat.client import AsyncGithubClient

from . import deployment


class Application(web.Application):
    """Application."""
    def __init__(self, config_file):
        """Use config file to initialize application."""
        with open(config_file) as f:
            self.config = toml.load(f)

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

    def find_repo_config(self, secret):
        """Use secret to find repo config."""
        return self.config["repo"][self._secrets_map[secret]]


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
    main()
