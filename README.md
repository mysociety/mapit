# MapIt

A web service to map postcodes to administrative boundaries and more.

MapIt was created and is maintained by [mySociety](https://github.com/mysociety/mapit), it's recommended you read their [README](https://github.com/mysociety/mapit/blob/master/README.rst) as well.

## Development

This fork of MapIt should avoid adding features, changing behaviours, or touching the code of MapIt itself. The only [differences against the original repo](https://github.com/mysociety/mapit/compare/master...alphagov:master) should only be to help integrate it into the GOV.UK stack. This allows our fork to be kept up to date with the mySociety version.

So far this includes;

 - [Pinning to specific versions of Python dependencies](https://github.com/alphagov/mapit/pull/1), for reliability
 - [Adding a Procfile](https://github.com/alphagov/mapit/pull/2), to standardise deployment with other apps
 - [A GOV.UK specific README](https://github.com/alphagov/mapit/pull/3), to provide context for GOV.UK developers

## Technical documentation

MapIt is a Python/Django application (backed by PostgreSQL), that provides
RESTful API for looking up postcodes, council boundaries, etc.

### Dependencies

MapIt has no dependencies on the rest of the GOV.UK stack, but does use PostgreSQL
with some geo-spatial extensions. For the GOV.UK VM these are documented in [puppet](https://github.gds/gds/puppet/blob/master/modules/govuk/manifests/apps/mapit.pp), or you can follow the [standalone install guide](http://mapit.poplus.org/docs/self-hosted/install/).

### Running the application

You'll need to be in a [virtualenv](http://docs.python-guide.org/en/latest/dev/virtualenvs/), and install dependencies with:

```pip install -r requirements.txt```

You can then run an instance of mapit with:

```manage.py runserver 127.0.0.1:3108```

## Licence

[GNU Affero GPL](LICENCE.txt)
