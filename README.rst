Hindsight
=========

Becase of this `PR<https://github.com/servo/homu/pull/96>`_ and created this project.

Report something after a pull request has merged. Such as

- Deployment status


Implements this by using the search api to find which pull request the commit belongs:

    curl -vv https://api.github.com/search/issues?q=type:pr+repo:zzzeek/sqlalchemy+3e3554d37ca589218c13f9b2969801dccbbdfa2c


Usage
------

Install in virtualenv

.. code:: shell

    $ virtualenv .venv
    $ . .venv/bin/action
    $ pip install -U -r requirements.txt

Copy config file

.. code:: shell

    $ cp cfg.toml.example cfg.toml
    $ $EDITOR cfg.toml

Run server

.. code:: shell

    python -m hindsight.app cfg.toml
