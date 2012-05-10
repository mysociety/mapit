#!/usr/bin/python

import xml.sax, os, errno, urllib, urllib2, sys
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

class Node:

    def __init__(self, node_id, latitude, longitude):
        self.node_id = node_id
        self.lat = latitude
        self.lon = longitude
        self.tags = {}

    def get_element_name(self):
        return 'node'

    def __eq__(self, other):
        if type(other) is type(self):
            return self.node_id == other.node_id
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def pretty(self, indent=0):
        i = u" "*indent
        result = i + u"node (%s) lat: %s, lon: %s" % (self.node_id, self.lat, self.lon)
        for k, v in sorted(self.tags.items()):
            result += u"\n%s  %s => %s" % (i, k, v)
        return result

    def __hash__(self):
        return hash(self.node_id)

    def __repr__(self):
        return "node (%s) lat: %s, lon: %s" % (self.node_id, self.lat, self.lon)

class Way:

    def __init__(self, way_id, nodes=None):
        self.way_id = way_id
        self.nodes = nodes or []
        self.tags = {}

    def get_element_name(self):
        return 'way'

    def __eq__(self, other):
        if type(other) is type(self):
            return self.way_id == other.way_id
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def pretty(self, indent=0):
        i = u" "*indent
        result = i + u"way (%s)" % (self.way_id)
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

class Relation:

    def __init__(self, relation_id):
        self.relation_id = relation_id
        # A relation has an ordered list of children, which we store
        # as a list of tuples.  The first element of each tuple is a
        # Node, Way or Relation, and the second is a "role" string.
        self.children = []
        self.tags = {}

    def get_element_name(self):
        return 'relation'

    def __eq__(self, other):
        if type(other) is type(self):
            return self.relation_id == other.relation_id
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def pretty(self, indent=0):
        i = u" "*indent
        result = i + u"relation (%s)" % (self.relation_id)
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

class OSMXMLParser(ContentHandler):

    VALID_TOP_LEVEL_ELEMENTS = set(('node', 'relation', 'way'))
    VALID_RELATION_MEMBERS = set(('node', 'relation', 'way'))
    IGNORED_TAGS = set(('osm', 'note', 'meta'))

    def __init__(self):
        self.top_level_elements = []
        self.current_top_level_element = None
        # These dictionaries map ids to already discovered elements:
        self.known_nodes = {}
        self.known_ways = {}
        self.known_relations = {}

    def raise_if_sub_level(self, name):
        if self.current_top_level_element:
            raise Exception, "Should never get a new <%s> when still in a top-level element" % (name,)

    def raise_if_top_level(self, name):
        if not self.current_top_level_element:
            raise Exception, "Should never get a new <%s> when not in a top-level element" % (name,)

    def raise_unless_expected_parent(self, name, expected_parent):
        if self.current_top_level_element.get_element_name() != expected_parent:
            raise Exception, "Didn't expect to find <%s> in a <%s>" % (name, expected_parent)

    def get_known_or_fetch(self, element_type, element_id):
        d = {'node': self.known_nodes,
             'way': self.known_ways,
             'relation': self.known_relations}[element_type]
        if element_id in d:
            return d[element_id]
        o = fetch_osm_element(element_type, element_id)
        d[element_id] = o
        return o

    def startElement(self, name, attr):
        if name in OSMXMLParser.IGNORED_TAGS:
            return
        elif name in OSMXMLParser.VALID_TOP_LEVEL_ELEMENTS:
            self.raise_if_sub_level(name)
            if name == "node":
                node_id = attr['id']
                self.current_top_level_element = Node(node_id, attr['lat'], attr['lon'])
                self.known_nodes[node_id] = self.current_top_level_element
            elif name == "way":
                way_id = attr['id']
                self.current_top_level_element = Way(way_id)
                self.known_ways[way_id] = self.current_top_level_element
            elif name == "relation":
                relation_id = attr['id']
                self.current_top_level_element = Relation(relation_id)
                self.known_relations[relation_id] = self.current_top_level_element
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
                member = self.get_known_or_fetch(member_type, attr['ref'])
                t = (member, attr['role'])
                self.current_top_level_element.children.append(t)
            elif name == "nd":
                self.raise_unless_expected_parent(name, 'way')
                node = self.get_known_or_fetch('node', attr['ref'])
                self.current_top_level_element.nodes.append(node)
            else:
                raise "Unhandled element <%s>" % (name,)

    def endElement(self, name):
        if name in OSMXMLParser.VALID_TOP_LEVEL_ELEMENTS:
            self.top_level_elements.append(self.current_top_level_element)
            self.current_top_level_element = None

def fetch_cached(element_type, element_id):
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
        encoded_values = urllib.urlencode(values)
        request = urllib2.Request(url, encoded_values)
        response = urllib2.urlopen(request)
        with open(filename, "w") as fp:
            fp.write(response.read())
    return filename

def parse_xml(filename):
    parser = OSMXMLParser()
    with open(filename) as fp:
        xml.sax.parse(fp, parser)
    return parser

def fetch_osm_element(element_type, element_id):
    """Fetch and parse a particular OSM element recursively

    More data is fetched from the API if required.  'element_type'
    should be one of 'relation', 'way' or 'node'."""
    # Make sure we have the XML file for that relation, node or way:
    filename = fetch_cached(element_type, element_id)
    parsed = parse_xml(filename)
    return parsed.get_known_or_fetch(element_type, element_id)

if __name__ == "__main__":
    # Try Orkney as an example:
    # orkney_relation = fetch_osm_element('relation', '375982')
    # guernsey_relation = fetch_osm_element('relation', '1711291')
    south_cambridgeshire = fetch_osm_element('relation', '295353')
