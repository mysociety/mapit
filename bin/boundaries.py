#!/usr/bin/python

import xml.sax, os, errno, urllib, urllib2, sys, datetime, time
from xml.sax.handler import ContentHandler

# Suggested by http://stackoverflow.com/q/600268/223092
def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST:
            pass
        else:
            raise

class OSMElement(object):

    def __init__(self, element_id, element_content_missing=False):
        self.element_id = element_id
        self.missing = element_content_missing

    def get_id(self):
        return self.element_id

    def __eq__(self, other):
        if type(other) is type(self):
            return self.element_id == other.element_id
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.element_id)

    def name_id_tuple(self):
        return (self.get_element_name(), self.element_id)

    @property
    def element_content_missing(self):
        return self.missing

    @staticmethod
    def make_missing_element(element_type, element_id):
        if element_type == "node":
            return Node(element_id, element_content_missing=True)
        elif element_type == "way":
            return Way(element_id, element_content_missing=True)
        elif element_type == "relation":
            return Relation(element_id, element_content_missing=True)
        else:
            raise Exception, "Unknown element name '%s'" % (element_type,)

class Node(OSMElement):

    """Represents an OSM node as returned via the Overpass API"""

    def __init__(self, node_id, latitude=None, longitude=None, element_content_missing=False):
        super(Node, self).__init__(node_id, element_content_missing)
        self.lat = latitude
        self.lon = longitude
        self.tags = {}

    def get_element_name(self):
        return 'node'

    def pretty(self, indent=0):
        i = u" "*indent
        result = i + u"node (%s) lat: %s, lon: %s" % (self.element_id, self.lat, self.lon)
        for k, v in sorted(self.tags.items()):
            result += u"\n%s  %s => %s" % (i, k, v)
        return result

    def lon_lat_tuple(self):
        return (self.lon, self.lat)

    def __repr__(self):
        return "node(%s) lat: %s, lon: %s" % (self.element_id, self.lat, self.lon)

class Way(OSMElement):

    """Represents an OSM way as returned via the Overpass API"""

    def __init__(self, way_id, nodes=None, element_content_missing=False):
        super(Way, self).__init__(way_id, element_content_missing)
        self.nodes = nodes or []
        self.tags = {}

    def get_element_name(self):
        return 'way'

    def __iter__(self):
        for n in self.nodes:
            yield n

    def pretty(self, indent=0):
        i = u" "*indent
        result = i + u"way (%s)" % (self.element_id)
        for k, v in sorted(self.tags.items()):
            result += u"\n%s  %s => %s" % (i, k, v)
        for node in self.nodes:
            result += u"\n" + node.pretty(indent + 2)
        return result

    @property
    def first(self):
        return self.nodes[0]

    @property
    def last(self):
        return self.nodes[-1]

    def closed(self):
        return self.first == self.last

    def join(self, other):
        """Try to join another way to this one.  It will succeed if
        they can be joined at either end, and otherwise returns None.
        """
        if self.closed():
            raise Exception, "Trying to join a closed way to another"
        if other.closed():
            raise Exception, "Trying to join a way to a close way"
        if self.first == other.first:
            new_nodes = list(reversed(other.nodes))[0:-1] + self.nodes
        elif self.first == other.last:
            new_nodes = other.nodes[0:-1] + self.nodes
        elif self.last == other.first:
            new_nodes = self.nodes[0:-1] + other.nodes
        elif self.last == other.last:
            new_nodes = self.nodes[0:-1] + list(reversed(other.nodes))
        else:
            raise Exception, "Trying to join two ways with no end point in common"
        return Way(None, new_nodes)

    def __repr__(self):
        return "way(%s) with %d nodes" % (self.element_id, len(self.nodes))

class Relation(OSMElement):

    """Represents an OSM relation as returned via the Overpass API"""

    def __init__(self, relation_id, element_content_missing=False):
        super(Relation, self).__init__(relation_id, element_content_missing)
        # A relation has an ordered list of children, which we store
        # as a list of tuples.  The first element of each tuple is a
        # Node, Way or Relation, and the second is a "role" string.
        self.children = []
        self.tags = {}

    def __iter__(self):
        for c in self.children:
            yield c

    def get_element_name(self):
        return 'relation'

    def pretty(self, indent=0):
        i = u" "*indent
        result = i + u"relation (%s)" % (self.element_id)
        for k, v in sorted(self.tags.items()):
            result += u"\n%s  %s => %s" % (i, k, v)
        for child, role in self.children:
            result += u"\n%s  child %s" % (i, child.get_element_name())
            result += u" with role '%s'" % (role)
            result += u"\n" + child.pretty(indent + 4)
        return result

    def way_iterator(self, inner=False):
        for child, role in self.children:
            if inner:
                if role not in ('enclave', 'inner'):
                    continue
            else:
                if role and role != 'outer':
                    continue
            if child.get_element_name() == 'way':
                yield child
            elif child.get_element_name() == 'relation':
                for sub_way in child.way_iterator(inner):
                    yield sub_way

    def __repr__(self):
        return "relation(%s) with %d children" % (self.element_id, len(self.children))

class UnexpectedElementException(Exception):
    def __init__(self, element_name, message=None):
        self.element_name = element_name
        if message is None:
            self.message = "The element name was '%s'" % (element_name)
        else:
            self.message = message
    def __str__(self):
        return self.message

class OSMXMLParser(ContentHandler):

    """A SAX-based parser for data from OSM's Overpass API

    This builds a structure of Node, Way and Relation objects that
    represent the returned data, fetching missing elements as
    necessary.  Typically one would then call get_known_or_fetch on
    this object to get back data for a particular element."""

    VALID_TOP_LEVEL_ELEMENTS = set(('node', 'relation', 'way'))
    VALID_RELATION_MEMBERS = set(('node', 'relation', 'way'))
    IGNORED_TAGS = set(('osm', 'note', 'meta'))
    IGNORED_ROLES = set(('subarea',))

    def __init__(self, fetch_missing=True):
        self.top_level_elements = []
        self.current_top_level_element = None
        # These dictionaries map ids to already discovered elements:
        self.known_nodes = {}
        self.known_ways = {}
        self.known_relations = {}
        self.fetch_missing = fetch_missing

    def __iter__(self):
        for e in self.top_level_elements:
            yield e

    def __len__(self):
        return len(self.top_level_elements)

    def empty(self):
        return 0 == len(self.top_level_elements)

    def raise_if_sub_level(self, name):
        if self.current_top_level_element:
            raise UnexpectedElementException(name, "Should never get a new <%s> when still in a top-level element" % (name,))

    def raise_if_top_level(self, name):
        if not self.current_top_level_element:
            raise UnexpectedElementException(name, "Should never get a new <%s> when not in a top-level element" % (name,))

    def raise_unless_expected_parent(self, name, expected_parent):
        if self.current_top_level_element.get_element_name() != expected_parent:
            raise UnexpectedElementException(name, "Didn't expect to find <%s> in a <%s>" % (name, expected_parent))

    def get_known_or_fetch(self, element_type, element_id):
        """Return an OSM Node, Way or Relation, fetching it if necessary"""
        element_id = str(element_id)
        d = {'node': self.known_nodes,
             'way': self.known_ways,
             'relation': self.known_relations}[element_type]
        if element_id in d:
            return d[element_id]
        if not self.fetch_missing:
            return OSMElement.make_missing_element(element_type, element_id)
        o = fetch_osm_element(element_type, element_id)
        if not o:
            return None
        d[element_id] = o
        return o

    def startElement(self, name, attr):
        if name in OSMXMLParser.IGNORED_TAGS:
            return
        elif name in OSMXMLParser.VALID_TOP_LEVEL_ELEMENTS:
            self.raise_if_sub_level(name)
            element_id = attr['id']
            if name == "node":
                self.current_top_level_element = Node(element_id, attr['lat'], attr['lon'])
                self.known_nodes[element_id] = self.current_top_level_element
            elif name == "way":
                self.current_top_level_element = Way(element_id)
                self.known_ways[element_id] = self.current_top_level_element
            elif name == "relation":
                self.current_top_level_element = Relation(element_id)
                self.known_relations[element_id] = self.current_top_level_element
            else:
                assert "Unhandled top level element %s" % (name,)
        else:
            # These must be sub-elements:
            self.raise_if_top_level(name)
            if name == "tag":
                k, v = attr['k'], attr['v']
                self.current_top_level_element.tags[k] = v
            elif name == "member":
                self.raise_unless_expected_parent(name, 'relation')
                member_type = attr['type']
                if member_type not in OSMXMLParser.VALID_RELATION_MEMBERS:
                    raise "Unknown member type '%s' in <relation>" % (member_type,)
                if attr['role'] not in OSMXMLParser.IGNORED_ROLES:
                    member = self.get_known_or_fetch(member_type, attr['ref'])
                    if member:
                        t = (member, attr['role'])
                        self.current_top_level_element.children.append(t)
                    else:
                        if self.fetch_missing:
                            print >> sys.stderr, "Ignoring member %s(%s) that couldn't be found" % (member_type, attr['ref'])
            elif name == "nd":
                self.raise_unless_expected_parent(name, 'way')
                node = self.get_known_or_fetch('node', attr['ref'])
                if not node:
                    raise Exception, "A node (%s) was referenced that couldn't be found" % (attr['ref'],)
                self.current_top_level_element.nodes.append(node)
            else:
                raise "Unhandled element <%s>" % (name,)

    def endElement(self, name):
        if name in OSMXMLParser.VALID_TOP_LEVEL_ELEMENTS:
            self.top_level_elements.append(self.current_top_level_element)
            self.current_top_level_element = None

def get_total_seconds(td):
    """A replacement for timedelta.total_seconds(), that's only in Python >= 2.7"""
    return td.microseconds * 1e-6 + td.seconds + td.days * (24.0 * 60 * 60)

class RateLimitedPOST:

    last_post = None
    min_time_between = datetime.timedelta(seconds=2)

    @staticmethod
    def request(url, values, filename):
        if RateLimitedPOST.last_post:
            since_last = datetime.datetime.now() - RateLimitedPOST.last_post
            if since_last < RateLimitedPOST.min_time_between:
                difference = RateLimitedPOST.min_time_between - since_last
                time.sleep(get_total_seconds(difference))
        encoded_values = urllib.urlencode(values)
        request = urllib2.Request(url, encoded_values)
        print "making request to url:", url
        response = urllib2.urlopen(request)
        with open(filename, "w") as fp:
            fp.write(response.read())
        RateLimitedPOST.last_post = datetime.datetime.now()

def fetch_cached(element_type, element_id):
    global last_overpass_fetch
    arguments = (element_type, element_id)
    if element_type not in ('relation', 'way', 'node'):
        raise Exception, "Unknown element type '%s'" % (element_type,)
    d = os.path.dirname(os.path.abspath(__file__))
    cache_directory = os.path.realpath(os.path.join(d, '..', 'data', 'new-cache'))
    mkdir_p(cache_directory)
    filename = os.path.join(cache_directory,"%s-%s.xml" % arguments)
    if not os.path.exists(filename):
        url = "http://www.overpass-api.de/api/interpreter"
        data = '''
(
  %s(%s);
  >;
);
out;
''' % arguments
        values = {'data': data}
        RateLimitedPOST.request(url, values, filename)
    return filename

def parse_xml(filename, fetch_missing=True):
    parser = OSMXMLParser(fetch_missing)
    with open(filename) as fp:
        xml.sax.parse(fp, parser)
    return parser

def fetch_osm_element(element_type, element_id, fetch_missing=True):
    """Fetch and parse a particular OSM element recursively

    More data is fetched from the API if required.  'element_type'
    should be one of 'relation', 'way' or 'node'."""
    element_id = str(element_id)
    print "fetch_osm_element(%s, %s)" % (element_type, element_id)
    # Make sure we have the XML file for that relation, node or way:
    filename = fetch_cached(element_type, element_id)
    try:
        parsed = parse_xml(filename, fetch_missing)
    except UnexpectedElementException, e:
        # If we failed to parse the file, move it out of the way (so
        # for transient errors we can just try again) and re-raise the
        # exception:
        new_filename = filename+".broken"
        os.rename(filename, new_filename)
        raise
    # Sometimes we seem to have an empty element returned, in which
    # case just return None:
    if not len(parsed):
        return None
    return parsed.get_known_or_fetch(element_type, element_id)

class EndpointToWayMap:

    """A class for mapping endpoints to the Way they're on

    This is useful for quickly checking finding which Ways (if any)
    you can join another Way to."""

    def __init__(self):
        self.endpoints = {}

    def add_way(self, way):
        if self.get_from_either_end(way):
            raise Exception, "Call to add_way would overwrite existing way(s)"
        self.endpoints[way.first] = way
        self.endpoints[way.last] = way

    def remove_way(self, way):
        del self.endpoints[way.first]
        del self.endpoints[way.last]

    def get_from_either_end(self, way):
        return [ self.endpoints[e] for e in (way.first, way.last)
                 if e in self.endpoints ]

    def pretty(self, indent=0):
        i = " "*indent
        result = i + "EndpointToWayMap:"
        for k, v in self.endpoints.items():
            result += "\n%s  endpoint: %s" % (i, k.pretty())
            result += "\n%s    way.first: %r" % (i, v.first)
            result += "\n%s    way.last: %r" % (i, v.last)
        return result

    def number_of_endpoints(self):
        return len(self.endpoints)

class UnclosedBoundariesException(Exception):
    pass

def join_way_soup(ways):
    """Join an iterable collection of ways into closed ways

    Two ways can be joined when the share a start or end node.  This
    function will try to join the given ways into a series of closed
    loops.  If there are any unclosed loops left at the end, they are
    reported to standard error and an exception is thrown.
    """
    closed_ways = []
    endpoints_to_ways = EndpointToWayMap()
    for way in ways:
        if way.closed():
            closed_ways.append(way)
            continue
        # Are there any existing ways we can join this to?
        to_join_to = endpoints_to_ways.get_from_either_end(way)
        if to_join_to:
            joined = way
            for existing_way in to_join_to:
                joined = joined.join(existing_way)
                endpoints_to_ways.remove_way(existing_way)
                if joined.closed():
                    closed_ways.append(joined)
                    break
            if not joined.closed():
                endpoints_to_ways.add_way(joined)
        else:
            endpoints_to_ways.add_way(way)
    if endpoints_to_ways.number_of_endpoints():
        print >> sys.stderr, endpoints_to_ways.pretty().encode('utf-8')
        raise UnclosedBoundariesException, "There were some unclosed paths left."
    return closed_ways

def main():

    # Try some useful examples:

    example_relation_ids = (
        '375982', # Orkney - relation contains sub-relations for islands
        '1711291', # Guernsey
        '295353') # South Cambridgeshire - has an hole (inner ways)

    for relation_id in example_relation_ids:

        print "Fetching the relation", relation_id
        parsed_relation = fetch_osm_element('relation', relation_id)

        print "Outer boundaries:"
        for way in parsed_relation.way_iterator(False):
            print way
        print "Inner boundaries:"
        for way in parsed_relation.way_iterator(True):
            print way

        inner_ways = list(parsed_relation.way_iterator(True))
        closed_inner_ways = join_way_soup(inner_ways)
        print "They made up %d closed inner way(s)" % (len(closed_inner_ways),)

        outer_ways = list(parsed_relation.way_iterator(False))
        closed_outer_ways = join_way_soup(outer_ways)
        print "They made up %d closed outer way(s)" % (len(closed_outer_ways),)

if __name__ == "__main__":
    main()
