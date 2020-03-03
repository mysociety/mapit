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

1.  Checkout the [mapit](https://github.com/alphagov/mapit),
    [mapit-scripts](https://github.com/alphagov/mapit-scripts) and
    [govuk-docker](https://github.com/alphagov/govuk-docker) repos

2.  Prepare your Mapit installation in Docker by:
    1.  Running `make mapit` in the `govuk-docker` repo - this will build the image
        and install all the dependencies.
    2.  Reset the database by running `govuk-docker run mapit-app ./reset-db.sh`
        in the `mapit` repo (you can skip this step if you haven't run Mapit locally
        before) - this will drop any existing database, create a new empty one
        and migrate it to the empty schema. See the [Troubleshooting](#troubleshooting)
        section if you have issues.
    3.  Start your Docker container by running `govuk-docker up mapit-app`, and
        check you are able to access `mapit.dev.gov.uk` - it is expected that the
        frontend looks somewhat "broken", but we only need to worry about the
        database for importing data.

3.  Find the latest ONS Postcode Database, Boundary Line, and OSNI datasets.
    1.  MySociety may have mirrored the latest datasets on their cache
        server: <http://parlvid.mysociety.org/os/> so check there first.
    2.  ONSPD releases can be found via the Office for National
        Statistics (ONS) at
        <http://geoportal.statistics.gov.uk/datasets?q=ONS+Postcode+Directory+(ONSPD)&sort_by=name&sort_order=asc>
        or via
        <http://geoportal.statistics.gov.uk/> and selecting the latest ONSPD
        from the Postcodes product drop down.
    3.  Boundary Line releases can be found via the Ordnance Survey (OS)
        at
        <https://www.ordnancesurvey.co.uk/opendatadownload/products.html#BDLINE>
    4.  OSNI releases can be found via their Spatial NI site at
        <http://osni.spatial-ni.opendata.arcgis.com/>. Note that they
        don't have a single download and you have to fetch each dataset
        we want individually. We're looking for the latest releases from
        the OSNI Open Data Largescale Boundaries of the following:
        - [Wards 2012](http://osni-spatial-ni.opendata.arcgis.com/datasets/55cd419b2d2144de9565c9b8f73a226d_0)
        - [District Electoral Areas 2012](http://osni-spatial-ni.opendata.arcgis.com/datasets/981a83027c0e4790891baadcfaa359a3_4)
        - [Local Government Districts 2012](http://osni-spatial-ni.opendata.arcgis.com/datasets/a55726475f1b460c927d1816ffde6c72_2)
        - [Parliamentary Constituencies 2008](http://osni-spatial-ni.opendata.arcgis.com/datasets/563dc2ec3d9943428e3fe68966d40deb_3)
        - [NI Outline](http://osni-spatial-ni.opendata.arcgis.com/datasets/d9dfdaf77847401e81efc9471dcd09e1_0)
        If the boundaries are redrawn the name of the dataset may change to
        reflect the year of the legislation (e.g. there are Wards 1993 and
        Wards 2012 datasets at the moment, future legislation may introduce a
        Wards 2020 dataset).

        **Note:** the package of OSNI data that is mirrored on [mysociety's
        cache](http://parlvid.mysociety.org/os/) is currently a `.tar.gz` that
        contains all the all 5 shapefile downloads and a `metadata.json` file
        describing the source, release date, SRID and type.
        You should check that any new package has the same structure and if not,
        update `import-uk-onspd` accordingly.
        If you have to download your own copies of the OSNI data you should check
        the shapefiles have the correct SRID because they may change from the
        defaults. If they are incorrect the point lookup can fail (finding parents)
        or give incorrect results (postcodes).

        Use [`ogrinfo`](http://www.gdal.org/ogrinfo.html) to get the SRID of
        a shapefile:
        ```
        $ ogrinfo OSNI_Open_Data_Largescale_Boundaries__Parliamentary_Constituencies_2008.shp OSNI_Open_Data_Largescale_Boundaries__Parliamentary_Constituencies_2008 -so
        ```

        Look up the `GEOGCS` field on [this coordinate systems page](http://downloads.esri.com/support/documentation/ims_/Support_files/elements/pcs.htm)
        to find the SRID. Most likely SRIDs are 29902 (the NI  projection),
        29900 (the UK projection), 4326 (the web mercator projection used
        by google earth among others).

4.  Upload the latest ONS Postcode Database, Boundary Line, and OSNI datasets
    to the `govuk-custom-formats-mapit-storage-production` S3 bucket. The path
    should be of the format `source-data/<year-month>/<filename>`.

    **Note:** the uploaded `<filename>` must match the naming convention
    of the dataset files. This may not be case when initially downloaded.
    For example, the ONSPD download for November 2018 is `2018-11`.
    Files within `2018-11/data` are named `ONSPD_NOV_2018_UK.xxx`.
    Before uploading in S3, rename folder `2018-11` to `ONSPD_NOV_2018_UK`.

5.  Update the `import-uk-onspd` and `check-onsi-downloads` scripts in
    `mapit-scripts` to refer to the URLs of the new releases uploaded to S3 in
    the last step.

6.  In your Docker container run the `import-uk-onspd` script to import the data:

        $ ./import-uk-onspd

    You can run this from the `mapit-scripts` folder as it is configured to find
    your mapit installation

    This is a long process, it's importing 1000s of boundary objects and
    \~2.5 million postcodes, and can take up to 5 hours.

    **This script may fail**. The datasets will change over time to include
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
    success if you read [mysociety's documentation](https://mapit.mysociety.org/docs/)
    and at [Mapit's logged issues](https://github.com/mysociety/mapit/issues).
    If you do have to fix the import scripts, or create new ones, consider
    talking with mysociety developers to see if they're aware and if you can push
    those changes back upstream.

    If the script fails, it's likely you'll need to drop and recreate
    the database using the `reset-db.sh` script and run `import-uk-onspd`
    again. If you have database issues see the [troubleshooting](#troubleshooting)
    section.

7.  Check for missing codes.

    The ONS used to identify areas with SNAC codes (called ONS
    in mapit). They stopped doing this in 2011 and started using GSS
    codes instead. New areas will not receive SNAC codes, and (for the
    moment at least) much of GOV.UK relies on SNAC codes to link
    things up, for example [Frontend's AuthorityLookup](https://github.com/alphagov/frontend/blob/master/lib/authority_lookup.rb).

    The `import-uk-onspd` script's last action is to run a script to show missing codes. It's the line that reads

        $MANAGE mapit_UK_show_missing_codes

    This iterates over all area types we care about and lists those that
    are missing a GSS code (hopefully none) and how many are missing an
    ONS/SNAC code. If it lists any areas that are missing codes and you
    don't expect them (run the script on production or integration if
    you're not sure) you'll need to investigate.

    Ssh into one of the machines and run:

        $ cd /var/apps/mapit
        $ sudo -u deploy govuk_setenv mapit venv/bin/python manage.py mapit_UK_show_missing_codes

    Then compare the output with that generated in your VM.

    There is a also script in mapit:
    `mapit_gb/management/commands/mapit_UK_add_missing_codes.py` that
    you can update to add the codes once you work out if anything can
    be done.

    Once these have been updated, the API will return the new GSS code, albeit mislabelled as an ONS code.   

    Hopefully by the time the next releases happen GOV.UK will not rely
    on ONS/SNAC codes and this will cease being an issue.

    **Note** [Licensify](https://github.com/alphagov/licensify) also depends on knowledge of SNAC codes to build it's own API paths. It will be necessary to update this [file](https://github.com/alphagov/licensify/blob/master/common/app/uk/gov/gds/licensing/model/SnacCodes.scala) with the new GSS codes and corresponding area.

8.  Test some postcodes.

    If you've had users complaining that their postcode isn't
    recognised, then try _those_ postcodes and any other ones
    you know. If you don't know any postcodes, try this random one:

        $ curl http://mapit.dev.gov.uk/postcode/ME206QZ

    You should expect a `200` response with data present in the `areas`
    field of the response.

    Ensure you test postcodes from all parts of the UK, since Northern
    Ireland data has been loaded separately.

9.  Make PRs for any changes you had to make. You will have changed the
    `import-uk-onspd` and `check-osni-downloads` script in `mapit-scripts` to
    refer to new datasets. If anything failed you may have had to change other
    things in mapit too.

### Export new database to S3

Export the database you just built in your container:

    $ govuk-docker run mapit-app psql -U postgres pg_dump mapit | gzip > mapit.sql.gz

It should be \~500Mb in size. You'll want to give it a name that refers
to what data it contains. Perhaps `mapit-<%b%Y>.sql.gz` (using
`strftime` parlance) for a standard release, or
`mapit-<%b%Y>-<a-description-of-change>.sql.gz` if you've had to change
the data outside the normal dataset releases.

Arrange to have the file you just created uploaded to the
`govuk-custom-formats-mapit-storage-production` S3 bucket and ensure that
it's permission is set to `public`.

Once it's been uploaded change the URL and checksum (using
`sha1sum <your-mapit-file.sql.gz>`) reference in `import-db-from-s3.sh`
to refer to your new file. Submit change as a PR against
[Mapit](https://github.com/alphagov/mapit) and deploy once it's been approved.

### Update servers with new database

NB: THIS REQUIRES ACCESS TO GOV.UK PRODUCTION

Now that your changes have been deployed, you can test the new database in
`AWS staging` before moving to production.

Once you have tested that a new mapit node works as expected, you can
update each mapit node in turn using a [fabric
script](https://github.com/alphagov/fabric-scripts/blob/master/mapit.py#L10):

    $ fab $environment -H <ip_address> mapit.update_database_via_app

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
request still result in a `302 Redirect`, and that what it redirects to
is a `200 OK`. It means we can't really expect all `200 OK` messages
regardless of the URL to remain `200 OK` - because the import will
change ids.

You can test the new database using one of the options:
1. [Generating some test data](#generating-some-test-data)
2. [Running the test samples script](#running-the-test-samples-script)

### Generating some test data

The best source of testing data for postcode lookups is Production, so
let's grab all the relevant responses from yesterday's log:

    $ your laptop> ssh <mapit_production_machine>
    $ mapit-1> sudo awk '$9==200 {print "http://localhost:3108" $7}' /var/log/nginx/mapit-access.log.1 >mapit-200s
    $ mapit-1> sudo awk '$9==404 {print "http://localhost:3108" $7}' /var/log/nginx/mapit-access.log.1 >mapit-404s
    $ mapit-1> sudo awk '$9==302 {print "http://localhost:3108" $7}' /var/log/nginx/mapit-access.log.1 >mapit-302s

Download the files via the jumpbox, e.g.

    $ scp -r -oProxyJump=jumpbox.production.govuk.digital <ip_address>:mapit-200s ~/Downloads/

Then copy the three files (mapit-200s, mapit-404s, mapit-302s) to the server you're testing on, e.g.

    $ scp -v -r -oProxyJump=jumpbox.staging.govuk.digital ~/Downloads/mapit-302s <ip_address>:~

In the server you want to test run the following:

1. Test that all the 200s are still 200s:

        $ while read line; do curl -sI $line | grep HTTP/1.1 ; done <mapit-200s | sort | uniq -c
          27916 HTTP/1.1 200 OK
2. Test that all the old 404s are either 200s or 404s:

        $ while read line; do curl -sI $line | grep HTTP/1.1 ; done <mapit-404s | sort | uniq -c
          104 HTTP/1.1 200 OK
          331 HTTP/1.1 404 Not Found
3. Test that all the 302s are still 302s:

        $ while read line; do curl -sI $line | grep HTTP/1.1 ; done <mapit-302s | sort | uniq -c
          807 HTTP/1.1 302 Found
4. Check that the 200s are still returning areas:

        $ while read line; do curl $line | python -c "import sys, json; data = json.load(sys.stdin); print '${line} found' if len(data['areas']) > 0 else '${line} missing'"; done <mapit-200s

**Note**: Checking the 200's can take around 30 minutes. You can also see the CPU and load on this [Grafana graph](https://grafana.blue.staging.govuk.digital/dashboard/file/machine.json?refresh=1m&orgId=1) and select the machine.

This process has been automated somewhat via the following [fabric
script](https://github.com/alphagov/fabric-scripts/blob/master/mapit.py#L51):

    $ fab $environment -H <ip_address> mapit.check_database_upgrade

**Note**: This replays yesterday's traffic from the machine you
run it on rather than replaying traffic from production. Useful when
upgrading production environments, perhaps less so for upgrading other
environments.

### Running the test samples script

For a more comprehensive test, you can use the `test-samples.sh`
script, which needs to be run before and after a database upgrade:

    $ your laptop> ssh mapit-1.production
    $ mapit-1> /var/apps/mapit/test-samples.sh sample

Perform the database import in the usual way, and then run the script
in "check" mode, to download the postcode data again and diff the
results:

    $ your laptop> ssh mapit-1.production
    $ mapit-1> /var/apps/mapit/test-samples.sh check

Once you have tested the updated mapit node works as expected, you can update
the other mapit nodes, and then the same on production.

## Things you might have to fix

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

## Troubleshooting

### Unable to drop the database when running the ./reset-db.sh script

1. Log into the database

2. Prevent future connections by running

        $ REVOKE CONNECT ON DATABASE mapit FROM public;
3. Terminate all connections to the database except your own:

        $ SELECT pid, pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = current_database() AND pid <> pg_backend_pid();

Failing that, stop `collectd`, it probably connects again the moment the old connection gets terminated:

    $sudo service collectd stop

### Hitting exceptions where an area has a missing parent or spelt incorrectly

If you see something similar to:

  ```
  get() returned more than one area -- it returned 2!
  ```

  ```
  /var/govuk/mapit/mapit/management/find_parents.py:49
  Exception: Area Moray [9325] (SPC) does not have a parent?
  ```

Compare the entry with the database in `integration` or `production` to identify what information is missing or needs to be corrected. Searching for the data on https://mapit.mysociety.org might also be helpful.
