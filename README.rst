Hindsight
=========

Report something after a pull request has merged. Such as

- Deployment status


Implements this by using the search api to find which pull request the commit belongs:

    curl -vv https://api.github.com/search/issues?q=type:pr+repo:zzzeek/sqlalchemy+3e3554d37ca589218c13f9b2969801dccbbdfa2c
