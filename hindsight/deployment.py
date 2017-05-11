#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""Deployment webhook."""
from __future__ import print_function, division, unicode_literals

import json

import enum

from tornado import web
from tornado import gen
from tornado.log import gen_log

from asyncat.repository import Repository


class BuildStatus(enum.Enum):
    unknow = "unknow"
    pending = "pending"
    success = "success"
    failure = "failure"


class BaseCIBuild(object):
    """Base class the ci builds."""
    def __init__(self, payload):
        """Initialize.

        :param payload: build's payload
        """
        self.payload = payload
        self.prepare()

    def get_status(self):
        """Returns the status of current build.

        :rtype: :class:`BuildStatus`
        """
        raise NotImplementedError()

    def get_sha(self):
        """Returns the sha of current build."""
        raise NotImplementedError()

    def is_valid(self):
        """Returns True if current build is valid."""
        return True


class BaseCIWebhook(object):
    def __init__(self, handler):
        """Initialize

        :type handler: :class:`tornado.web.RequestHandler`

        """
        self.handler = handler

    def iter_builds(self):
        """Iterates builds in current hook."""
        raise NotImplementedError()

    def get_secret(self):
        """Returns secret in request."""
        raise NotImplementedError()


class BuildbotBuild(BaseCIBuild):
    """Represents a build of buildbot."""
    def prepare(self):
        self.event = self.payload["event"]
        self.info = self.payload["payload"]["build"]
        self.properties = dict(x[:2] for x in self.info['properties'])
        self.sha = self.properties["revision"]

    def get_status(self):
        if self.event == "buildFinished":
            if "successful" in self.info["text"] or self.info["results"] == 0:
                return BuildStatus.success
            else:
                return BuildStatus.failure
        elif self.event == "buildStarted":
            return BuildStatus.pending

        return BuildStatus.unknow

    def get_sha(self):
        return self.sha

    def is_valid(self):
        return bool(self.sha)


class BuildbotWebhook(BaseCIWebhook):
    def get_secret(self):
        return self.handler.get_argument("secret")

    def iter_builds(self):
        packets = json.loads(self.handler.get_argument("packets"))

        for payload in packets:
            yield BuildbotBuild(payload)


class DeploymentHandler(web.RequestHandler):
    @gen.coroutine
    def post(self):
        hook = BuildbotWebhook(self)
        secret = hook.get_secret()

        try:
            config = self.application.find_repo_config(secret)
        except KeyError:
            gen_log.warn("Could not find config with secret: %s.", secret)
            self.write("Secret mismatch.")
            self.set_status(403)
            return

        repo = Repository(self.github_client, config["owner"], config["name"])

        futures = []

        for build in hook.iter_builds():
            pull = self._find_pull(repo, build)
            futures.append(pull.create_comment(
                "Deployment status {}".format(build.get_status())))

        yield futures

    @gen.coroutine
    def _find_pull(self, repo, build):
        """Find pull reuqest via build.

        :type repo: :class:`asyncat.repository.Repository`
        :type build: :class:`BaseCIBuild`
        """
        # Try use build's sha to find pull request.
        resp = yield repo.search_pulls(build.get_sha())
        if resp.data["total_count"] == 1:
            pull = yield repo.pull(resp.data["items"][0]["number"])
            raise gen.Return(pull)

        # Try use parent commit to find pull request.
        commit = yield repo.commit(build.get_sha())

        for parent in commit.c["parents"]:
            resp = yield repo.search_pulls(parent["sha"])
            if resp.data["total_count"] == 1:
                pull = yield repo.pull(resp.data["items"][0]["number"])
                raise gen.Return(pull)
