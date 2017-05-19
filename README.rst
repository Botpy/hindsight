.. image:: https://travis-ci.org/coldnight/hindsight.svg?branch=master
    :target: https://travis-ci.org/coldnight/hindsight

.. image:: https://codecov.io/gh/coldnight/hindsight/branch/master/graph/badge.svg
  :target: https://codecov.io/gh/coldnight/hindsight

Hindsight
=========

Becase of this `PR <https://github.com/servo/homu/pull/96>`_ and created this project.

Report something after a pull request has merged. Such as

- Deployment status


Implements this by using the search api to find which pull request the commit belongs:

    curl -vv https://api.github.com/search/issues?q=type:pr+repo:asyncat/demo+1a00a4f061e2e141f7fe2386b8758ef9b549397c


Usage
------

How to install
^^^^^^^^^^^^^^

.. code:: shell

    $ git clone https://github.com/coldnight/hindsight
    $ cd hindsight
    $ virtualenv .venv
    $ . .venv/bin/activate
    $ pip install -U -r requirements.txt


How to configure
^^^^^^^^^^^^^^^^

1. Copy `cfg.toml.example` to `cfg.toml`, and edit it accordingly.

2. Add a Webhook to your continuous integration service:

    hindsight supports deployment via buildbot, insert the following code to the `master.cfg` file:

    .. code:: python

        from buildbot.status.status_push import HttpStatusPush

        c['status'].append(HttpStatusPush(
            serverUrl='http://HOST:PORT/deployment',
            extra_post_params={'secret': 'repo.NAME.secret in cfg.toml'},
        ))



How to run
^^^^^^^^^^

.. code:: shell

    python -m hindsight.app cfg.toml
