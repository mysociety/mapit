#!/usr/bin/env python

# This script checks whether a representative latitude / longitude in
# each capital city of the world is contained in a level 2 admin area
# in MapIt Global.  This is a simple sanity check for finding any
# unclosed country boundaries.
#
# There are two dependencies from PyPi needed for this script, which
# can be installed with:
#
#   pip install requests
#   pip install SPARQLWrapper

from collections import defaultdict
import json
import re
import requests
import time
import urllib
from SPARQLWrapper import SPARQLWrapper, JSON

def name_from_url(url):
    """Extract everything after the last slash in the URL"""

    url_as_str = url.encode('ascii')
    unquoted = urllib.unquote(re.sub(r'^.*/', '', url_as_str))
    return unquoted.decode('utf-8')

def tuple_mean(index, tuples):
    """Return the mean along a given index in a sequence of tuples"""

    return sum(t[index] for t in tuples) / float(len(tuples))

# Get a list of coordinates for capital cities
# The filter for only selecting current countries (as opposed to
# historical ones) was from here:
#  http://answers.semanticweb.com/questions/2155/sparql-query-to-get-a-distinct-set-of-current-countries-from-dbpedia

sparql = SPARQLWrapper("http://dbpedia.org/sparql")
sparql.setQuery("""
    PREFIX o: <http://dbpedia.org/ontology/>
    PREFIX p: <http://dbpedia.org/property/>
    PREFIX geo: <http://www.w3.org/2003/01/geo/wgs84_pos#>

    SELECT ?lon ?lat ?country ?capital WHERE {
        ?country p:capital ?capital .
        ?country rdf:type o:Country .
        ?capital geo:lat ?lat .
        ?capital geo:long ?lon .
        OPTIONAL {?country p:yearEnd ?yearEnd}
        FILTER (!bound(?yearEnd))
    } ORDER BY ?country
""")
sparql.setReturnFormat(JSON)
results = sparql.query().convert()

coordinates_for_places = defaultdict(list)

for result in results["results"]["bindings"]:
    lat = float(result['lat']['value'])
    lon = float(result['lon']['value'])
    country = name_from_url(result['country']['value'])
    capital = name_from_url(result['capital']['value'])
    coordinates_for_places[(capital, country)].append((lon, lat))

sorted_mapping = sorted(coordinates_for_places.items(),
                        key=lambda t: (t[0][1], t[0][0]))

total_capitals = 0
capitals_with_no_country = 0

for place, coords in sorted_mapping:
    city, country = (name_from_url(x) for x in place)
    print u"{0} ({1})".format(city, country).encode('utf-8')
    mean_lon = tuple_mean(0, coords)
    mean_lat = tuple_mean(1, coords)
    mapit_url_format = "http://global.mapit.mysociety.org/point/4326/{0},{1}"
    mapit_url = mapit_url_format.format(mean_lon, mean_lat)
    print "  browse on MapIt Global:", mapit_url + ".html"
    r = requests.get(mapit_url, headers={'User-Agent': 'TestingCapitals/1.0'})
    mapit_result = json.loads(r.text)
    level_2_areas = [a for a in mapit_result.values() if a['type'] == 'O02']
    if level_2_areas:
        print "  In these level 2 areas:"
        for a in level_2_areas:
            print "    ", a['name'].encode('utf-8')
    else:
        print "  ### No level 2 areas found!"
        capitals_with_no_country += 1
    total_capitals += 1
    # Sleep so we don't hit MapIt's rate limiting:
    time.sleep(1)

print "{0} capitals had no country in MapIt Global (out of {1})".format(
    capitals_with_no_country,
    total_capitals)
