#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""Application test cases."""
from __future__ import print_function, division, unicode_literals

import mock

from hindsight.app import main


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
