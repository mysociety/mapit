# MapIt

A web service to map postcodes to administrative boundaries and more.

MapIt was created and is maintained by [mySociety](https://github.com/mysociety/mapit), it's recommended you read their [README](https://github.com/mysociety/mapit/blob/master/README.rst) as well.

## Nomenclature

- **Area**: a set of points that define an area that represents a geopolitical boundary of some sort.  A country, a parliamentary constituency, a national park, a civil parish, etc.
- **Postcode**: an identifier for a small geographical area usually derived from postal data.  Postcodes don't have boundaries, instead they have a lat/lng point which is the centroid of their area.  The **Area**s for that **Postcode** are looked up by doing a geo search for those that contain the point.
- **Generation**: because areas change over time we add **Area**s to generations.  If an area is in one generation but not another it is likely because legislation was enacted between those generations that meant it ceased to exist (often it is replaced by another similar but not exactly the same Area).  Unless specified in the request mapit only searches in the current generation.
- **Type**: to identify what an area is it has a type.  For example European parliamentary constituencies are type 'EUR' compared to Westminister parliamentary constituencies of type 'WMC'.
- **CodeType**: Areas have codes to allow them to be identified, issued by the ONS.  Prior to 2011 these were SNAC codes (stored as type 'ons') (see: http://www.ons.gov.uk/ons/guide-method/geography/products/names--codes-and-look-ups/standard-names-and-codes/index.html), since 2011 these are GSS codes (stored as type 'gss') (see: http://neighbourhood.statistics.gov.uk/dissemination/Info.do?m=0&s=1460381709047&enc=1&page=nessgeography/new-geography-codes-and-naming-policy-from-1-january-2011.htm&nsjs=true&nsck=false&nssvg=false&nswid=1212)
- **ONSPD**: The Office for National Statistics Postcode Database - one of the open data sources we use to import data. We get UK postcodes from this.
- **Boundary Line**: The Ordnance Survey boundary line data - one of the open data sources we use to import data.  We get GB Areas from this.
- **OSNI**: The Ordnance Survey of Northern Ireland - one of the providers of the open data sources we use to import data.  We get NI Areas from them.

## Technical documentation

MapIt is a Python/Django application (backed by PostgreSQL), that provides
RESTful API for looking up postcodes, council boundaries, etc.

### Dependencies

MapIt has no dependencies on the rest of the GOV.UK stack.

- [puppet](https://github.com/alphagov/govuk-puppet/blob/master/modules/govuk/manifests/apps/mapit.pp) - definitions for the postgres and geo-spatial extensions used.
- [mapit-scripts](https://github.com/alphagov/mapit-scripts) - scripts we use when importing data.  The data sets are released between 4 and 2 times per year, these scripts automate the process of rebuilding the db to reflect this.

### Running the application

`GOVUK_ENV=development ./startup.sh`

Or if you use the GDS development VM you can run this application with Bowler: `bowl mapit`.

To run any other management commands (`.venv/bin/python ./manage.py ...`), you'll need the `GOVUK_ENV` environment variable set.

### Importing data

Please see [the importing data instructions](./IMPORTING-DATA.md)

### Running the test suite

`GOVUK_ENV=development .venv/bin/python ./manage.py test mapit mapit_gb`

Include any other edge cases, e.g parallel test runner in Whitehall

### Why a fork?

This fork of MapIt should avoid adding features, changing behaviours, or touching the code of MapIt itself. The only [differences against the original repo](https://github.com/mysociety/mapit/compare/master...alphagov:master) should only be to help integrate it into the GOV.UK stack. This allows our fork to be kept up to date with the mySociety version.

So far this includes;

 - [Pinning to specific versions of Python dependencies](https://github.com/alphagov/mapit/pull/1), for reliability
 - [Adding a Procfile](https://github.com/alphagov/mapit/pull/2) and [unicornherder](https://github.com/alphagov/mapit/pull/12), to standardise deployment with other apps
 - [A GOV.UK specific README](https://github.com/alphagov/mapit/pull/3), to provide context for GOV.UK developers
 - [Importing a DB from S3](import-db-from-s3.sh), to simplify bringing new servers online with the same data

If we need to change the code itself, we should communicate with mysociety to try and push the work back upstream so everyone benefits.

### Example API output


#### To fetch information about all European parliamentary constituencies:

`curl http://mapit.dev.gov.uk/areas/EUR.json -H 'Content-type: application/json'`

```json
{
  "9558":
  {
    "parent_area": null,
    "generation_high": 1,
    "all_names": {},
    "id": 9558,
    "codes": {
      "ons": "06",
      "gss": "E15000006",
      "unit_id": "41425"
    },
    "name": "Eastern",
    "country": "E",
    "type_name": "European region",
    "generation_low": 1,
    "country_name": "England",
    "type": "EUR"
  },
  "9559": {
    "parent_area": null,
    "generation_high": 1,
    "all_names": {},
    "id": 9559,
    "codes": {
      "ons": "04",
      "gss": "E15000004",
      "unit_id": "41423"
    },
    "name": "East Midlands",
    "country": "E",
    "type_name": "European region",
    "generation_low": 1,
    "country_name": "England",
    "type": "EUR"
  },
  "9560": {
    "parent_area": null,
    "generation_high": 1,
    "all_names": {},
    "id": 9560,
    "codes": {
      "ons": "07",
      "gss": "E15000007",
      "unit_id": "41428"
    },
    "name": "London",
    "country": "E",
    "type_name":
    "European region",
    "generation_low": 1,
    "country_name": "England",
    "type": "EUR"
  },
  "9566": {
    "parent_area": null,
    "generation_high": 1,
    "all_names": {},
    "id": 9566,
    "codes": {
      "ons": "01",
      "gss": "E15000001",
      "unit_id": "41422"
    },
    "name": "North East",
    "country": "E",
    "type_name": "European region",
    "generation_low": 1,
    "country_name": "England",
    "type": "EUR"
  },
  "12233": {
    "parent_area": null,
    "generation_high": 1,
    "all_names": {},
    "id": 12233,
    "codes": {
      "osni_oid": "EUR-1",
      "gss": "N07000001"
    },
    "name": "Northern Ireland",
    "country": "N",
    "type_name": "European region",
    "generation_low": 1,
    "country_name": "Northern Ireland",
    "type": "EUR"
  },
  "9561": {
    "parent_area": null,
    "generation_high": 1,
    "all_names": {},
    "id": 9561,
    "codes": {
      "ons": "02",
      "gss": "E15000002",
      "unit_id": "41431"
    },
    "name": "North West",
    "country": "E",
    "type_name": "European region",
    "generation_low": 1,
    "country_name": "England",
    "type": "EUR"
  },
  "9562": {
    "parent_area": null,
    "generation_high": 1,
    "all_names": {},
    "id": 9562,
    "codes": {
      "gss": "S15000001",
      "unit_id": "41429"
    },
    "name": "Scotland",
    "country": "S",
    "type_name": "European region",
    "generation_low": 1,
    "country_name": "Scotland",
    "type": "EUR"
  },
  "9565": {
    "parent_area": null,
    "generation_high": 1,
    "all_names": {},
    "id": 9565,
    "codes": {
      "ons": "08",
      "gss": "E15000008",
      "unit_id": "41421"
    },
    "name": "South East",
    "country": "E",
    "type_name": "European region",
    "generation_low": 1,
    "country_name": "England",
    "type": "EUR"
  },
  "9568": {
    "parent_area": null,
    "generation_high": 1,
    "all_names": {},
    "id": 9568,
    "codes": {
      "ons": "09",
      "gss": "E15000009",
      "unit_id": "41427"
    },
    "name": "South West",
    "country": "E",
    "type_name": "European region",
    "generation_low": 1,
    "country_name": "England",
    "type": "EUR"
  },
  "9567": {
    "parent_area": null,
    "generation_high": 1,
    "all_names": {},
    "id": 9567,
    "codes": {
      "ons": "10",
      "gss": "W08000001",
      "unit_id": "41424"
    },
    "name": "Wales",
    "country": "W",
    "type_name": "European region",
    "generation_low": 1,
    "country_name": "Wales",
    "type": "EUR"
  },
  "9563": {
    "parent_area": null,
    "generation_high": 1,
    "all_names": {},
    "id": 9563,
    "codes": {
      "ons": "05",
      "gss": "E15000005",
      "unit_id": "41426"
    },
    "name": "West Midlands",
    "country": "E",
    "type_name": "European region",
    "generation_low": 1,
    "country_name": "England",
    "type": "EUR"
  },
  "9564": {
    "parent_area": null,
    "generation_high": 1,
    "all_names": {},
    "id": 9564,
    "codes": {
      "ons": "03",
      "gss": "E15000003",
      "unit_id": "41430"
    },
    "name": "Yorkshire and the Humber",
    "country": "E",
    "type_name": "European region",
    "generation_low": 1,
    "country_name": "England",
    "type": "EUR"
  }
}
```

#### To fetch information about a single postcode:

`curl http://mapit.dev.gov.uk/postcode/sw1a+1aa.json -H 'Content-type: application/json'`

```json
{
  "wgs84_lat": 51.50086373251905,
  "coordsyst": "G",
  "shortcuts": {
    "WMC": 11135,
    "ward": 7037,
    "council": 1974
  },
  "wgs84_lon": -0.14320717529002294,
  "postcode": "SW1A 1AA",
  "easting": 528978,
  "areas": {
    "1974": {
      "parent_area": null,
      "generation_high": 1,
      "all_names": {},
      "id": 1974,
      "codes": {
        "ons": "00BK",
        "gss": "E09000033",
        "unit_id": "11164"
      },
      "name": "City of Westminster Borough Council",
      "country": "E",
      "type_name": "London borough",
      "generation_low": 1,
      "country_name": "England",
      "type": "LBO"
    },
    "9582": {
      "parent_area": 1750,
      "generation_high": 1,
      "all_names": {},
      "id": 9582,
      "codes": {
        "ons": "",
        "gss": "E32000014",
        "unit_id": "41449"
      },
      "name": "West Central",
      "country": "E",
      "type_name": "London Assembly constituency",
      "generation_low": 1,
      "country_name": "England",
      "type": "LAC"
    },
    "1750": {
      "parent_area": null,
      "generation_high": 1,
      "all_names": {},
      "id": 1750,
      "codes": {
        "unit_id": "41441"
      },
      "name": "Greater London Authority",
      "country": "E",
      "type_name": "Greater London Authority",
      "generation_low": 1,
      "country_name": "England",
      "type": "GLA"
    },
    "9560": {
      "parent_area": null,
      "generation_high": 1,
      "all_names": {},
      "id": 9560,
      "codes": {
        "ons": "07",
        "gss": "E15000007",
        "unit_id": "41428"
      },
      "name": "London",
      "country": "E",
      "type_name": "European region",
      "generation_low": 1,
      "country_name": "England",
      "type": "EUR"
    },
    "7037": {
      "parent_area": 1974,
      "generation_high": 1,
      "all_names": {},
      "id": 7037,
      "codes": {
        "ons": "00BKGQ",
        "gss": "E05000644",
        "unit_id": "11162"
      },
      "name": "St James's",
      "country": "E",
      "type_name": "London borough ward",
      "generation_low": 1,
      "country_name": "England",
      "type": "LBW"
    },
    "11135": {
      "parent_area": null,
      "generation_high": 1,
      "all_names": {},
      "id": 11135,
      "codes": {
        "ons": "B11",
        "gss": "E14000639",
        "unit_id": "25040"
      },
      "name": "Cities of London and Westminster",
      "country": "E",
      "type_name": "UK Parliament constituency",
      "generation_low": 1,
      "country_name": "England",
      "type": "WMC"
    }
  },
  "northing": 179626
}
```

#### To search for areas by name:

`curl https://mapit.integration.publishing.service.gov.uk/areas/owl.json -H 'Content-type: application/json'`

```json
{
  "8197": {
    "parent_area": 2027,
    "generation_high": 1,
    "all_names": {},
    "id": 8197,
    "codes": {
      "ons": "00MANK",
      "gss": "E05002284",
      "unit_id": "397"
    },
    "name": "Owlsmoor",
    "country": "E",
    "type_name": "Unitary Authority ward (UTW)",
    "generation_low": 1,
    "country_name": "England",
    "type": "UTW"
  }
}
```

## Licence

[GNU Affero GPL](LICENSE.txt)
