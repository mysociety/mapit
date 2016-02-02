#!/bin/bash
set -e

# get the data from s3
sudo -u deploy curl 'https://gds-public-readable-tarballs.s3.amazonaws.com/mapit-postgres93-Jan2016.sql.gz' -o mapit.sql.gz
if ! echo "1120be001e65283a1a1c50d73f93ddd093f91c17 mapit.sql.gz" | sha1sum -c -; then
  echo "SHA1 does not match downloaded file!"
  exit 1
fi

# drop the old db and bring up a new empty one
sudo -u postgres dropdb --if-exists mapit
sudo -u postgres createdb --owner mapit mapit
sudo -u postgres psql -c "CREATE EXTENSION postgis; CREATE EXTENSION postgis_topology;" mapit

# load up the downloaded data into this new db
zcat -f mapit.sql.gz | sudo -u postgres psql mapit
