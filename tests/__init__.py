#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""Base class of test cases."""
from __future__ import print_function, division, unicode_literals

import os

try:
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlencode

from tornado import concurrent
from tornado import testing

from hindsight.app import Application


class HindsightTestCase(testing.AsyncHTTPTestCase):
    """Base class of test cases."""
    def get_file_path(self, filename):
        """Returns file's path in tests directory."""
        crt = os.path.abspath(os.path.dirname(__file__))
        return os.path.join(crt, filename)

    def get_app(self):
        """Override this method returns instance of
        :class:`tornado.web.Application`.
        """
        return Application(self.get_file_path("cfg.toml"))

    def make_future(self, result_or_exc):
        """Make future and set result or exception.

        :param result_or_exc: Result or exception
        """
        future = concurrent.Future()

        if isinstance(result_or_exc, BaseException):
            future.set_exception(result_or_exc)
        else:
            future.set_result(result_or_exc)

        return future

    def make_body(self, data):
        """Make request body with urlencoded format."""
        return urlencode(data)
