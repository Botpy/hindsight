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
from asyncat.client import GithubError

from .finder import NoSuchPullRequest


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

    def get_name(self):
        """Returns the name of current builder.  Returns ``None`` if current
        CI do not support.
        """
        raise NotImplementedError()     # pragma: no cover

    def get_status(self):
        """Returns the status of current build.

        :rtype: :class:`BuildStatus`
        """
        raise NotImplementedError()     # pragma: no cover

    def get_sha(self):
        """Returns the sha of current build."""
        raise NotImplementedError()     # pragma: no cover

    def is_valid(self):
        """Returns True if current build is valid."""
        return True


class BaseCIWebhook(object):
    def __init__(self, handler):
        """Initialize

        :type handler: :class:`tornado.web.RequestHandler`

        """
        self.handler = handler

    def make_build(self):
        """Returns a object that represents a build.

        :rtype: :class:`BaseCIBuild`
        """
        raise NotImplementedError()     # pragma: no cover

    def get_secret(self):
        """Returns secret in request."""
        raise NotImplementedError()


class BuildbotBuild(BaseCIBuild):
    """Represents a build of buildbot."""
    def prepare(self):
        self.event = self.payload["event"]
        self.info = self.payload["payload"]["build"]
        self.properties = dict(x[:2] for x in self.info['properties'])
        self.sha = (self.properties["revision"] or
                    self.properties.get("got_revision"))

    def get_name(self):
        return self.properties["buildername"]

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
        """Iterates builds.

        :rtype: :class:`BuildbotBuild`
        """
        packets = json.loads(self.handler.get_argument("packets"))
        for payload in packets:
            if payload["event"] not in ["buildStarted", "buildFinished"]:
                continue

            build = BuildbotBuild(payload)
            if not build.get_sha():
                continue
            yield build

    def make_build(self):
        """Make :class:`BuildbotBuild`.

        :rtype: :class:`BuildbotBuild`
        """

        started_build = None
        finished_build = None

        for build in self.iter_builds():
            status = build.get_status()
            if status is BuildStatus.pending:
                started_build = build
            elif status in [BuildStatus.success, BuildStatus.failure]:
                finished_build = build

        # Buildbot pushs all event in one payload, so we need to skip
        # started event if payload includes finished event.
        return finished_build or started_build


class DeploymentHandler(web.RequestHandler):
    @gen.coroutine
    def post(self):
        hook = BuildbotWebhook(self)

        build = hook.make_build()

        if build is not None:
            yield self._on_build(hook, build)

        self.write("OK")

    def _get_repo(self, hook, build):
        """Returns :class:`asyncat.repository.Repository` via
        :class:`BaseCIWebhook` and :class:`BaseCIBuild`.
        """

        secret = hook.get_secret()

        try:
            config = self.application.find_repo_config(secret,
                                                       build.get_name())
        except KeyError:
            gen_log.warn("Could not find config with secret: %s.", secret)
            self.write("Secret mismatch.")
            raise web.HTTPError(403)

        return Repository(self.application.github_client, config["owner"],
                          config["name"])

    @gen.coroutine
    def _on_build(self, hook, build):
        repo = self._get_repo(hook, build)

        gen_log.info("Try find pull requset via %s in %s/%s", build.get_sha(),
                     repo.owner, repo.label)

        try:
            pull = yield self.application.find_pull(repo, build.get_sha())
        except (GithubError, NoSuchPullRequest) as e:
            gen_log.error("Could not find any pull request via %s in %s/%s",
                          build.get_sha(), repo.owner, repo.label,
                          exc_info=True)
            if isinstance(e, GithubError):
                raise web.HTTPError(404)
            return

        gen_log.info("Found pull request #%s via %s in %s/%s", pull.num,
                     build.get_sha(), repo.owner, repo.label)

        comment = "Deployment status {}".format(build.get_status())
        yield pull.create_comment(comment)
