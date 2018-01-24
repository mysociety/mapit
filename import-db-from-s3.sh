#!/bin/bash
set -e

# get the data from s3
sudo -u deploy curl 'https://s3-eu-west-1.amazonaws.com/govuk-custom-formats-mapit-storage-production/source-data/2018-01/20180124-mapit.sql.gz' -o mapit.sql.gz
if ! echo "e036c72a637f48979e5f9ae957988eef61c12a82 mapit.sql.gz" | sha1sum -c -; then
  echo "SHA1 does not match downloaded file!"
  exit 1
fi

# drop the old db and bring up a new empty one
sudo -u postgres dropdb --if-exists mapit
sudo -u postgres createdb --owner mapit mapit
sudo -u postgres psql -c "CREATE EXTENSION postgis; CREATE EXTENSION postgis_topology;" mapit

# load up the downloaded data into this new db
zcat -f mapit.sql.gz | sudo -u postgres psql mapit
