# MapIt - postcode and boundary lookup

## Introduction

[MapIt](https://github.com/alphagov/mapit) is a product of
[MySociety](https://mysociety.org) which we use within GOV.UK to allow
people to enter their postcode and be pointed to their local services.

It is composed of broadly 2 things:

1.  A database of postcodes and the location of their geographical
    centre
2.  A database of administrative entities (e.g. local councils) and
    their boundaries on a map

When a user enters a postcode on GOV.UK, MapIt will look it up to find
the geographical centre and then return information about the
administrative entities that postcode belongs to. We then use this
information to refer the user to local services provided by those
entities.

## Error Alerting

Errors from the web application are emailed to the `BUG_EMAIL` addresses in [alphagov-deployment](https://github.digital.cabinet-office.gov.uk/gds/alphagov-deployment/blob/master/mapit/settings)

You can access these via Google groups.

## Updating Datasets

Datasets for boundary lines are published twice a year (in May and
October) and postcodes are released four times a year (in February, May,
August and November). This means over time our database will become more
and more out of date and users will start to complain. When they do (or
before if possible) we should update the data.

To update a live mapit server we:

1.  [Generate a new database](#generate-a-new-database)
2.  [Export new database to S3](#export-new-database-to-s3)
3.  [Update servers with new database](#update-servers-with-new-database)

### Generate a new database

1.  Checkout the [Mapit](https://github.com/alphagov/mapit) repo to your
    dev VM if you don't have it already.
2.  Prepare your mapit repo so that you can run the importer scripts:
    a)  Run `govuk_setenv mapit startup.sh` - this will install all dependencies and run
        the server, once the server is running you can kill it, we just
        wanted the dependencies installed.
    b)  Prepare your database for importing new data by running the
        following to create an empty database and migrate it to the
        empty mapit schema:

            $ sudo -u postgres dropdb mapit
            $ sudo -u postgres createdb --owner mapit mapit
            $ sudo -u postgres psql -c "CREATE EXTENSION postgis; CREATE EXTENSION postgis_topology;" mapit
            $ govuk_setenv mapit .venv/bin/python ./manage.py migrate

3.  Checkout the [mapit-scripts](https://github.com/alphagov/mapit-scripts)
    repo to your dev VM if you don't have it already.

4.  Find the latest ONS Postcode Database, Boundary Line, and
    OSNI datasets.
    a)  MySociety may have mirrored the latest datasets on their cache
        server: <http://parlvid.mysociety.org/os/> so check there first.
    b)  ONSPD releases can be found via the Office for National
        Statistics (ONS) at
        <http://geoportal.statistics.gov.uk/datasets?q=ONS+Postcode+Directory+(ONSPD)&sort_by=name&sort_order=asc>
        or via
        <http://geoportal.statistics.gov.uk/> and selecting the latest ONSPD
        from the Postcodes product drop down.
    c)  Boundary Line releases can be found via the Ordnance Survey (OS)
        at
        <https://www.ordnancesurvey.co.uk/business-and-government/products/boundary-line.html>
    d)  OSNI releases can be found via their Spatial NI site at
        <http://osni.spatial-ni.opendata.arcgis.com/>. Note that they
        don't have a single download and you have to fetch each dataset
        we want individually. We're looking for the latest releases from
        the OSNI Open Data Largescale Boundaries of the following:
        i.   [Wards 2012](http://osni-spatial-ni.opendata.arcgis.com/datasets/55cd419b2d2144de9565c9b8f73a226d_0)
        ii.  [District Electoral Areas 2012](http://osni-spatial-ni.opendata.arcgis.com/datasets/981a83027c0e4790891baadcfaa359a3_4)
        iii. [Local Government Districts 2012](http://osni-spatial-ni.opendata.arcgis.com/datasets/a55726475f1b460c927d1816ffde6c72_2)
        iv.  [Parliamentary Constituencies 2008](http://osni-spatial-ni.opendata.arcgis.com/datasets/563dc2ec3d9943428e3fe68966d40deb_3)
        v.   [NI Outline](http://osni-spatial-ni.opendata.arcgis.com/datasets/d9dfdaf77847401e81efc9471dcd09e1_0)
        If the boundaries are redrawn the name of the dataset may change to
        reflect the year of the legislation (e.g. there are Wards 1993 and
        Wards 2012 datasets at the moment, future legislation may introduce a
        Wards 2020 dataset).

5.  Update the `import-uk-onspd` script in `mapit-scripts` to refer to
    the urls and filenames of the new releases instead of the old ones.

    Note that the package of OSNI data that is mirrored on mysociety's
    cache is currently a `.tar.gz` that contains all the all 5 shapefile
    downloads and a `metadata.json` file describing the source, release
    date, SRID and type. You should check that any new package has the
    same structure and if not, update `import-uk-onspd` accordingly. If
    you have to download your own copies of the OSNI data you should
    check the shapefiles to find out the SRID because they may change
    from the defaults and it is important to import the shapefiles with
    the correct SRID or parts of the import process that rely on point
    lookup can fail (finding parents) or give incorrect
    results (postcodes).

    Use [`ogrinfo`](http://www.gdal.org/ogrinfo.html) to get the SRID of
    a shapefile:
    ```
    $ ogrinfo OSNI_Open_Data_Largescale_Boundaries__Parliamentary_Constituencies_2008.shp OSNI_Open_Data_Largescale_Boundaries__Parliamentary_Constituencies_2008 -so
    ```

    Look up the `GEOGCS` field on [this coordinate systems page](http://downloads.esri.com/support/documentation/ims_/Support_files/elements/pcs.htm)
    to find the SRID. Most likely SRIDs are 29902 (the NI  projection),
    29900 (the UK projection), 4326 (the web mercator projection used
    by google earth among others).

6.  Run the `import-uk-onspd` script to import the data:

        $ ./import-uk-onspd

    You can run this from the `mapit-scripts` folder, it will find your
    mapit installation (assuming it's in the expected dev VM places -
    you can tell it where your mapit installation is if it's not in the
    standard place).

    This is a long process, it's importing 1000s of boundary objects and
    \~2.5 million postcodes.

    This script may fail. The datasets will change over time to include
    more data that we can't import (or don't want to import). For
    example the October 2015 Boundary Line release included new
    ceremonial and historical boundaries that can't be imported by mapit
    because the shape files have the wrong kind of data, so we need to
    exclude those files from the shape files we import. It also included
    Parish data that couldn't be imported because two parishes had the
    same gss code. We didn't need parish data so we also removed them
    from the import - it's likely that "standard" mapit will release a
    fix for these.

    If the scripts fail you'll have to investigate why and possibly
    update it to change how we import the data. Sorry! You may have some
    success if you read mysociety's documentation here:
    <http://mapit.poplus.org/docs/self-hosted/import/uk/> If you do have
    to fix the import scripts, or create new ones, consider talking with
    mysociety developers to see if they're aware and if you can push
    those changes back upstream.

    If the script fails, it's likely you'll need to drop and recreate
    the database and run the scripts again from scratch. Idempotency is
    patchy.

7.  Check for missing codes.

    The ONS used to identify areas with snac codes (called ons
    in mapit). They stopped doing this in 2011 and started using GSS
    codes instead. New areas will not receive snac codes, and (for the
    moment at least) much of GOV.UK relies on snac codes to link
    things up.

    To find out how many objects are missing a code run the following:

        $ govuk_setenv mapit .venv/bin/python ./manage.py mapit_UK_show_missing_codes

    This iterates over all area types we care about and lists those that
    are missing a GSS code (hopefully none) and how many are missing an
    ONS/snac code. If it lists any areas that are missing codes and you
    don't expect them (run the script on production or integration if
    you're not sure) you'll need to investigate.

    There is a script in mapit:
    `mapit_gb/management/commands/mapit_UK_add_missing_codes.py` that
    you can upate to add the codes once you work out if anything can
    be done.

    Hopefully by the time the next releases happen GOV.UK will not rely
    on ONS/snac codes and this will cease being an issue.
8.  Test some postcodes.

    If you've had users complaining that their postcode isn't
    recognised, then try _those_ postcodes and any other ones
    you know. If you don't know any postcodes, try this random one:

        $ curl http://mapit.dev.gov.uk/postcode/ME206QZ

    You should expect a `200` response with useful looking JSON in
    the body.
9.  Make PRs for any changes you had to make. You will have changed the
    `import-uk-onspd` script in `mapit-scripts` to refer to new
    datasets. If anything failed you may have had to change other things
    in mapit too.

### Export new database to S3

Export the database you just built on your Dev VM:

    $ sudo -u postgres pg_dump mapit | gzip > mapit.sql.gz

It should be \~250Mb in size. You'll want to give it a name that refers
to what data it contains. Perhaps `mapit-<%b%Y>.sql.gz` (using
`strftime` parlance) for a standard release, or
`mapit-<%b%Y>-<a-description-of-change>.sql.gz` if you've had to change
the data outside the normal dataset releases.

Arrange to have the file you just created uploaded to the
`govuk-custom-formats-mapit-storage-production` S3 bucket.

Once it's been uploaded change the URL and checksum (using
`sha1sum <your-mapit-file.sql.gz>`) reference in `import-db-from-s3.sh`
to refer to your new file. You can submit this change as a PR against
[Mapit](https://github.com/alphagov/mapit) and when it's been merged
book a deploy.

### Update servers with new database

NB: THIS REQUIRES ACCESS TO GOV.UK PRODUCTION

Once you have tested that a new mapit node works as expected, you can
update each mapit node in turn using a Fabric script:

    $ fab $environment -H mapit-1.api mapit.update_database_via_app

We can happily survive with one mapit-server in an environment while
this is done.

## Testing a server

We have two expectations for an updated Mapit database:

### For Postcodes

1.  It returns a `200 OK` status for all postcode requests that
    previously returned `200 OK`. The ONSPD is a complete set of all
    postcodes, live and terminated and we import the whole thing so
    postcodes should never be "deleted". If a request for a postcode
    previously succeeded, it should still succeed.
2.  It returns either a `404 Not Found` or a `200 OK` for all postcode
    requests that previously returned `404 Not Found`. As postcodes are
    released every 3 months, people may have searched for one that did
    not exist previously that is in our new dataset (now `200 OK`).
    However if they searched for a bad postcode, or something that is
    not a postcode at all, we would still expect that to
    `404 Not Found`.

### For Areas

A url of the form `/area/<ons-or-gss-code` will result in a
`302 Redirect` to a url `/area/<internal-id>`. Unfortunately these are
hard to tell apart as while GSS codes are easily distinguishable (they
start with a letter, and are 9 characters long) from an internal
database id (a number), the same is not true of ONS codes (a number /
character combination that could be 2, 4, 6, 8, or 10 characters long
and depending on the length, may only be numbers).

As part of the import process it's quite likely that the internal ids
will have changed. We should therefore check that all `302 Redirect`
request still result in a `302 Redirect` and that what it redirects to
is a `200 OK`. It means we can't really expect all `200 OK` messages
regardless of the URL to remain `200 OK` - because the import will
change ids.

### Generating some test data

The best source of testing data for postcode lookups is Production, so
let's grab all the relevant responses from yesterday's log:

    $ your laptop> ssh mapit-1.api.production
    $ mapit-1> sudo awk '$9==200 {print "http://localhost:3108" $7}' /var/log/nginx/mapit.publishing.service.gov.uk-access.log.1 >mapit-200s
    $ mapit-1> sudo awk '$9==404 {print "http://localhost:3108" $7}' /var/log/nginx/mapit.publishing.service.gov.uk-access.log.1 >mapit-404s
    $ mapit-1> sudo awk '$9==302 {print "http://localhost:3108" $7}' /var/log/nginx/mapit.publishing.service.gov.uk-access.log.1 >mapit-302s

Copy the three files (mapit-200s, mapit-404s, mapit-302s) to the server
you want to test and run the following:

    # Test that all the 200s are still 200s:
    $ while read line; do curl -sI $line | grep HTTP/1.1 ; done <mapit-200s | sort | uniq -c
       1000 HTTP/1.1 200 OK
    # Test that all the old 404s are either 200s or 404s:
    $ while read line; do curl -sI $line | grep HTTP/1.1 ; done <mapit-404s | sort | uniq -c
         43 HTTP/1.1 200 OK
        384 HTTP/1.1 404 NOT FOUND
    # Test that all the 200s are still 200s:
    $ while read line; do curl -sI $line | grep HTTP/1.1 ; done <mapit-302s | sort | uniq -c
        419 HTTP/1.1 302 OK

    # Check that the 200s are still returning areas:
    $ while read line; do curl $line | python -c "import sys, json; data = json.load(sys.stdin); print '${line} found' if len(data['areas']) > 0 else '${line} missing'"; done <mapit-200s

This process has been automated somewhat via the following fabric
script:

    $ fab $environment -H mapit-1.api mapit.check_database_upgrade

Note however that this replays yesterdays traffic from the machine you
run it on rather than replaying traffic from production. Useful when
upgrading production environments, perhaps less so for upgrading other
environments.

Things you might have to fix
----------------------------

The Office for National Statistics maintains a series of codes that represent a
wide range of geographical areas of the UK. MapIt includes these and they are
unique to each area, but an area can change code, for example when boundaries
change. If this happens, you might have to change some of our apps to use the
new codes instead of the old ones.

Our forked repo of MapIt contains a file [``mapit_gb/data/authorities.json``]
(https://github.com/alphagov/mapit/blob/master/mapit_gb/data/authorities.json)
which contains a list of Local Authorities, their slugs and their GSS codes.
During the import (invoked by the `import-uk-onspd` script), the GSS codes are
used to match to the areas in MapIt that represent LocalAuthorities and the
slugs are added to each of the areas. These GSS codes need to be kept up to date
in case they change. An example of doing this is [frontend PR 948]
(https://github.com/alphagov/frontend/pull/948) (when the file was still
residing in Frontend,[it has been moved it to MapIt since]
(https://github.com/alphagov/mapit/pull/20)).

The Business Support API uses GSS codes to match business support schemes to
local authorities so that we provide relevant ones for a location. This data
comes from Publisher. When we update MapIt, Publisher reads straight away from
the new MapIt data, so new business support schemes will automatically get new
codes. There are existing business support schemes though tagged to old GSS
codes, so for any that have changed, you will need to create a migration to
migrate the old GSS codes to new GSS codes for each affected council. An example
of doing this is [publisher PR 475](https://github.com/alphagov/publisher/pull/475).
