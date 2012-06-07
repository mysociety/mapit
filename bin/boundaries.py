#!/usr/bin/env python

import xml.sax, os, errno, urllib, urllib2, sys, datetime, time
from xml.sax.handler import ContentHandler
from lxml import etree

# Suggested by http://stackoverflow.com/q/600268/223092
def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST:
            pass
        else:
            raise

def get_cache_filename(element_type, element_id):
    element_id = int(element_id, 10)
    subdirectory = "%03d" % (element_id % 1000,)
    script_directory = os.path.dirname(os.path.abspath(__file__))
    full_subdirectory = os.path.join(script_directory,
                                     '..',
                                     'data',
                                     'new-cache',
                                     element_type,
                                     subdirectory)
    mkdir_p(full_subdirectory)
    basename = "%s-%d.xml" % (element_type, element_id)
    return os.path.join(full_subdirectory, basename)

def get_name_from_tags(tags, element_type=None, element_id=None):
    # FIXME: Using the English name ('name:en') by default is just
    # temporary, for debugging purposes - should use ('name') in
    # preference for real use.
    if 'name:en' in tags:
        return tags['name:en']
    elif 'name' in tags:
        return tags['name']
    elif element_type and element_id:
        return "Unknown name for %s with ID %s" % (element_type, element_id)
    else:
        return "Unknown"

def get_non_contained_elements(elements):
    """Filter elements, keeping only those which are not a member of another"""
    contained_elements = set([])
    for e in elements:
        if e.get_element_name() == "relation":
            for member, role in e:
                contained_elements.add(member.name_id_tuple())
    return [e for e in elements if e not in contained_elements]

class OSMElement(object):

    def __init__(self, element_id, element_content_missing=False, element_name=None):
        self.element_id = element_id
        self.missing = element_content_missing
        self.element_name = element_name

    def get_id(self):
        return self.element_id

    def get_element_name(self):
        # This should be overriden by any subclass, but when we're
        # creating members that are missing, we might set the name:
        return self.element_name or "BUG"

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

    def get_name(self):
        return get_name_from_tags(self.tags, self.get_element_name(), self.element_id)

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

    def get_missing_elements(self, to_append_to=None):
        if to_append_to is None:
            to_append_to = []
        if self.element_content_missing:
            to_append_to.append(self.name_id_tuple())
        return to_append_to

    @staticmethod
    def xml_wrapping():
        osm = etree.Element("osm", attrib={"version": "0.6",
                                           "generator": "mySociety Boundary Extractor"})
        note = etree.SubElement(osm, "note")
        note.text = "The data included in this document is from www.openstreetmap.org. It has there been collected by a large group of contributors. For individual attribution of each item please refer to http://www.openstreetmap.org/api/0.6/[node|way|relation]/#id/history"
        return osm

    def xml_add_tags(self, xml_element):
        for k, v in sorted(self.tags.items()):
            etree.SubElement(xml_element, 'tag', attrib={'k': k, 'v': v})

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

    def to_xml(self, parent_element=None, write_nodes_with_way=False):
        if parent_element is None:
            parent_element = OSMElement.xml_wrapping()
        node = etree.SubElement(parent_element,
                                'node',
                                attrib={'id': self.element_id,
                                        'lat': self.lat,
                                        'lon': self.lon})
        self.xml_add_tags(node)
        return parent_element

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

    def __len__(self):
        return len(self.nodes)

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

    def bounding_box_tuple(self):
        """Returns a tuple of floats representing a bounding box of this Way

        Each tuple is (min_lat, min_lon, max_lat, max_lon).  If the
        longitude of any node is less than -90 degrees, 360 is added
        to every node, to deal with ways that cross the -180 degree
        meridian"""

        longitudes = [float(n.lon) for n in self]
        latitudes = [float(n.lat) for n in self]

        if any(x for x in longitudes if x < -90):
            longitudes = [x + 360 for x in longitudes]

        min_lon = min(longitudes)
        max_lon = max(longitudes)

        min_lat = min(latitudes)
        max_lat = max(latitudes)

        return (min_lat, min_lon, max_lat, max_lon)

    def __repr__(self):
        return "way(%s) with %d nodes" % (self.element_id, len(self.nodes))

    def get_missing_elements(self, to_append_to=None):
        to_append_to = OSMElement.get_missing_elements(self, to_append_to)
        for node in self:
            node.get_missing_elements(to_append_to)
        return to_append_to

    def to_xml(self, parent_element=None, write_nodes_with_way=False):
        if parent_element is None:
            parent_element = OSMElement.xml_wrapping()
        if write_nodes_with_way:
            for node in self:
                node.to_xml(parent_element, write_nodes_with_way)
        way = etree.SubElement(parent_element,
                               'way',
                               attrib={'id': self.element_id})
        for node in self:
            etree.SubElement(way, 'nd', attrib={'ref': node.element_id})
        self.xml_add_tags(way)
        return parent_element

    def reconstruct_missing(self, parser, id_to_node):
        still_missing = []
        for i, node in enumerate(self.nodes):
            if not node.element_content_missing:
                continue
            node_id = node.element_id
            found_node = None
            if node_id in id_to_node:
                found_node = id_to_node[node_id]
            else:
                # Ask the parser to try to fetch it from its filesystem cache:
                found_node = parser.get_known_or_fetch('node', node_id)
            if found_node and not found_node.element_content_missing:
                self.nodes[i] = found_node
            else:
                still_missing.append(node)
        return still_missing

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

    def get_missing_elements(self, to_append_to=None):
        to_append_to = OSMElement.get_missing_elements(self, to_append_to)
        for member, role in self:
            if role not in OSMXMLParser.IGNORED_ROLES:
                member.get_missing_elements(to_append_to)
        return to_append_to

    def to_xml(self, parent_element=None, write_nodes_with_way=False):
        if parent_element is None:
            parent_element = OSMElement.xml_wrapping()
        relation = etree.SubElement(parent_element,
                                    'relation',
                                    attrib={'id': self.element_id})
        for member, role in self:
            etree.SubElement(relation,
                             'member',
                             attrib={'type': member.get_element_name(),
                                     'ref': member.element_id,
                                     'role': role})
        self.xml_add_tags(relation)
        return parent_element

    def reconstruct_missing(self, parser, id_to_node):
        still_missing = []
        for i, t in enumerate(self.children):
            member, role = t
            if role in OSMXMLParser.IGNORED_ROLES:
                continue
            if not member.element_content_missing:
                continue
            element_type = member.get_element_name()
            element_id = member.element_id
            found_element = None
            if element_type == 'node':
                if element_id in id_to_node:
                    found_element = id_to_node[element_id]
            if not found_element:
                # Ask the parser to try to fetch it from its filesystem cache:
                found_element = parser.get_known_or_fetch(element_type, element_id)
            if found_element and not found_element.element_content_missing:
                self.children[i] = (found_element, role)
            else:
                still_missing.append(member)
        return still_missing

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
    IGNORED_TAGS = set(('osm', 'note', 'meta', 'bound'))
    IGNORED_ROLES = set(('subarea', 'defaults', 'apply_to'))

    def __init__(self, fetch_missing=True, callback=None, cache=True):
        self.top_level_elements = []
        self.current_top_level_element = None
        # These dictionaries map ids to already discovered elements:
        self.known_nodes = {}
        self.known_ways = {}
        self.known_relations = {}
        self.fetch_missing = fetch_missing
        self.callback = callback
        self.cache = cache

    def clear_caches(self):
        self.known_nodes.clear()
        self.known_ways.clear()
        self.known_relations.clear()

    # FIXME: make this a decorator
    def raise_if_callback(self):
        if self.callback:
            raise Exception, "When parsed with a callback, no top level elements are kept in memory"

    def __iter__(self):
        self.raise_if_callback()
        for e in self.top_level_elements:
            yield e

    def __len__(self):
        self.raise_if_callback()
        return len(self.top_level_elements)

    def empty(self):
        self.raise_if_callback()
        return 0 == len(self.top_level_elements)

    def raise_if_sub_level(self, name):
        if self.current_top_level_element is not None:
            raise UnexpectedElementException(name, "Should never get a new <%s> when still in a top-level element" % (name,))

    def raise_if_top_level(self, name):
        if self.current_top_level_element is None:
            raise UnexpectedElementException(name, "Should never get a new <%s> when not in a top-level element" % (name,))

    def raise_unless_expected_parent(self, name, expected_parent):
        if self.current_top_level_element.get_element_name() != expected_parent:
            raise UnexpectedElementException(name, "Didn't expect to find <%s> in a <%s>" % (name, expected_parent))

    def get_known_or_fetch(self, element_type, element_id):
        """Return an OSM Node, Way or Relation, fetching it if necessary"""
        element_id = str(element_id)
        if self.cache:
            d = {'node': self.known_nodes,
                 'way': self.known_ways,
                 'relation': self.known_relations}[element_type]
            if element_id in d:
                return d[element_id]
        result = None
        # See if it is in the on-disk cache:
        cache_filename = get_cache_filename(element_type, element_id)
        if os.path.exists(cache_filename):
            parser = parse_xml(cache_filename, fetch_missing=self.fetch_missing)
            for e in parser.top_level_elements:
                if e.name_id_tuple() == (element_type, element_id):
                    result = e
                    break
            if not result:
                raise Exception, "Failed to find expected element in:" + cache_filename
        if not result:
            if self.fetch_missing:
                result = fetch_osm_element(element_type, element_id)
                if not result:
                    return None
            else:
                return OSMElement.make_missing_element(element_type, element_id)
        if self.cache:
            d[element_id] = result
        return result

    def startElement(self, name, attr):
        if name in OSMXMLParser.IGNORED_TAGS:
            return
        elif name in OSMXMLParser.VALID_TOP_LEVEL_ELEMENTS:
            self.raise_if_sub_level(name)
            element_id = attr['id']
            if name == "node":
                self.current_top_level_element = Node(element_id, attr['lat'], attr['lon'])
                if self.cache:
                    self.known_nodes[element_id] = self.current_top_level_element
            elif name == "way":
                self.current_top_level_element = Way(element_id)
                if self.cache:
                    self.known_ways[element_id] = self.current_top_level_element
            elif name == "relation":
                self.current_top_level_element = Relation(element_id)
                if self.cache:
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
                    else:
                        t = (OSMElement.make_missing_element(member_type, attr['ref']), attr['role'])
                        if self.fetch_missing:
                            print >> sys.stderr, "Ignoring member %s(%s) that couldn't be found" % (member_type, attr['ref'])
                    self.current_top_level_element.children.append(t)
            elif name == "nd":
                self.raise_unless_expected_parent(name, 'way')
                node = self.get_known_or_fetch('node', attr['ref'])
                if not node:
                    if self.fetch_missing:
                         print >> sys.stderr, "A node (%s) was referenced that couldn't be found" % (attr['ref'],)
                    node = OSMElement.make_missing_element('node', attr['ref'])
                self.current_top_level_element.nodes.append(node)
            else:
                raise "Unhandled element <%s>" % (name,)

    def endElement(self, name):
        if name in OSMXMLParser.VALID_TOP_LEVEL_ELEMENTS:
            if self.callback:
                self.callback(self.current_top_level_element, self)
            else:
                self.top_level_elements.append(self.current_top_level_element)
            self.current_top_level_element = None

class MinimalOSMXMLParser(ContentHandler):

    """Only extract ID and tags from top-level elements"""

    def __init__(self, handle_element):
        self.handle_element = handle_element
        self.current_tags = None
        self.current_element_type = None
        self.current_element_id = None

    def startElement(self, name, attr):
        if name in OSMXMLParser.VALID_TOP_LEVEL_ELEMENTS:
            self.current_element_type = name
            self.current_element_id = attr['id']
            self.current_tags = {}
        elif name == "tag":
            self.current_tags[attr['k']] = attr['v']

    def endElement(self, name):
        if name in OSMXMLParser.VALID_TOP_LEVEL_ELEMENTS:
            self.handle_element(self.current_element_type,
                                self.current_element_id,
                                self.current_tags)
            self.current_element_type = None
            self.current_element_id = None
            self.current_tags = None

def get_total_seconds(td):
    """A replacement for timedelta.total_seconds(), that's only in Python >= 2.7"""
    return td.microseconds * 1e-6 + td.seconds + td.days * (24.0 * 60 * 60)

class RateLimitedPOST:

    last_post = None
    min_time_between = datetime.timedelta(seconds=0.5)

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
    filename = get_cache_filename(element_type, element_id)
    if not os.path.exists(filename):
        url = "http://www.overpass-api.de/api/interpreter"
        data = '[timeout:3600];(%s(%s);>;);out;' % arguments
        values = {'data': data}
        RateLimitedPOST.request(url, values, filename)
    return filename

def parse_xml_minimal(filename, element_handler):
    parser = MinimalOSMXMLParser(element_handler)
    with open(filename) as fp:
        xml.sax.parse(fp, parser)

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
    def __init__(self, detailed_error=None):
        self.detailed_error = detailed_error

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
        raise UnclosedBoundariesException, endpoints_to_ways.pretty()
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
