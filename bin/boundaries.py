#!/usr/bin/env python

import xml.sax, os, errno, urllib, urllib2, sys, datetime, time, shutil
from xml.sax.handler import ContentHandler
import yaml
from lxml import etree
from tempfile import mkdtemp, NamedTemporaryFile
from StringIO import StringIO
from subprocess import Popen, PIPE

with open(os.path.join(
        os.path.dirname(__file__), '..', 'conf', 'general.yml')) as f:
    config = yaml.load(f)

# Suggested by http://stackoverflow.com/q/600268/223092
def mkdir_p(path):
    """Create a directory (and parents if necessary) like mkdir -p

    For example:

    >>> test_directory = mkdtemp()
    >>> new_directory = os.path.join(test_directory, "foo", "bar")
    >>> mkdir_p(new_directory)
    >>> os.path.exists(new_directory)
    True
    >>> os.path.isdir(new_directory)
    True

    There should be no error if the directory already exists:

    >>> mkdir_p(new_directory)

    But if there is another error, e.g. permissions prevent the
    directory from being created:

    >>> os.chmod(new_directory, 0)
    >>> new_subdirectory = os.path.join(new_directory, "baz")
    >>> mkdir_p(new_subdirectory) #doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
      ...
    OSError: [Errno 13] Permission denied: '/tmp/tmp64Q8MJ/foo/bar/baz'

    Remove the temporary directory created for these doctests:
    >>> os.chmod(new_directory, 0755)
    >>> shutil.rmtree(test_directory)
    """

    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST:
            pass
        else:
            raise

def get_query_relation_and_dependents(element_type, element_id):
    return """<osm-script timeout="3600">
  <union into="_">
    <id-query into="_" ref="%s" type="%s"/>
    <recurse from="_" into="_" type="down"/>
  </union>
  <print from="_" limit="" mode="body" order="id"/>
</osm-script>
""" % (element_id, element_type)

def get_query_relations_and_ways(required_tags):
    has_kv = "\n".join('      <has-kv k="%s" modv="" v="%s"/>' % (k,v)
                       for k, v in required_tags.items())
    return """<osm-script timeout="3600">
  <union into="_">
    <query into="_" type="relation">
%s
    </query>
    <query into="_" type="way">
%s
    </query>
  </union>
  <print from="_" limit="" mode="body" order="id"/>
</osm-script>""" % (has_kv, has_kv)

def get_from_overpass(query_xml, filename):
    if not os.path.exists(filename):
        if config.get('LOCAL_OVERPASS'):
            return get_osm3s(query_xml, filename)
        else:
            return get_remote(query_xml, filename)

def get_osm3s(query_xml, filename):
    with open(filename, 'w') as file_output:
        p = Popen(["osm3s_query",
                   "--concise",
                   "--db-dir=" + config['OVERPASS_DB_DIRECTORY']],
                  stdin=PIPE,
                  stdout=file_output)
        p.communicate(query_xml)
        if p.returncode != 0:
            raise Exception, "The osm3s_query failed"

def get_remote(query_xml, filename):
    url = config['OVERPASS_SERVER']
    values = {'data': query_xml}
    encoded_values = urllib.urlencode(values)
    request = urllib2.Request(url, encoded_values)
    response = urllib2.urlopen(request)
    with open(filename, "w") as fp:
        fp.write(response.read())

def get_cache_filename(element_type, element_id, cache_directory=None):
    if cache_directory is None:
        script_directory = os.path.dirname(os.path.abspath(__file__))
        cache_directory = os.path.join(script_directory,
                                       '..',
                                       'data',
                                       'new-cache')
    element_id = int(element_id, 10)
    subdirectory = "%03d" % (element_id % 1000,)
    full_subdirectory = os.path.join(cache_directory,
                                     element_type,
                                     subdirectory)
    mkdir_p(full_subdirectory)
    basename = "%s-%d.xml" % (element_type, element_id)
    return os.path.join(full_subdirectory, basename)

def get_name_from_tags(tags, element_type=None, element_id=None):
    """Given an OSMElement, return a readable name if possible

    If there's a name tag (typically the local spelling of the
    element), then use that:

    >>> tags = {'name': 'Deutschland',
    ...         'name:en': 'Federal Republic of Germany'}
    >>> get_name_from_tags(tags, 'relation', '51477')
    'Deutschland'

    Or fall back to the English name, if that's the only option:

    >>> tags = {'name:en': 'Freedonia', 'relation': '345678'}
    >>> get_name_from_tags(tags)
    'Freedonia'

    Otherwise, use the type and ID to form a readable name:

    >>> get_name_from_tags({}, 'node', '65432')
    'Unknown name for node with ID 65432'

    Or if we've no information at all, just return 'Unknown':

    >>> get_name_from_tags({})
    'Unknown'

    """

    if 'name' in tags:
        return tags['name']
    elif 'name:en' in tags:
        return tags['name:en']
    elif 'place_name' in tags:
        return tags['place_name']
    elif element_type and element_id:
        return "Unknown name for %s with ID %s" % (element_type, element_id)
    else:
        return "Unknown"

def get_non_contained_elements(elements):
    """Filter elements, keeping only those which are not a member of another

    As an example, you can do the following:

    >>> top = Relation("13")
    >>> sub = Relation("14")
    >>> top.children.append((sub, ''))
    >>> lone = Way("15")
    >>> get_non_contained_elements([top, sub, lone])
    [Relation(id="13", members=1), Way(id="15", nodes=0)]


    """
    contained_elements = set([])
    for e in elements:
        if e.element_type == "relation":
            for member, role in e:
                contained_elements.add(member)
    return [e for e in elements if e not in contained_elements]

class OSMElement(object):

    def __init__(self, element_id, element_content_missing=False, element_type=None):
        self.element_id = element_id
        self.element_type = element_type or "BUG"
        self.missing = element_content_missing

    def __lt__(self, other):
        return int(self.element_id, 10) < int(other.element_id, 10)

    def __eq__(self, other):
        """Define equality of OSMElements as same (OSM) type and ID

        For example, they should be equal even if one is of the base
        class and one the subclass:

        >>> missing = OSMElement('42', element_content_missing=True, element_type='node')
        >>> real = Node('42')
        >>> missing == real
        True

        But non-OSMElements aren't equal:

        >>> real == ('node', '42')
        False

        And elements of different type aren't equal:
        >>> real == Relation('42')
        False

        """
        if not isinstance(other, OSMElement):
            return False
        if self.element_type == other.element_type:
            return self.element_id == other.element_id
        return False

    def __ne__(self, other):
        """Inequality is just the negation of equality

        >>> Node('42') != Relation('42')
        True

        >>> Node('42') != Node('8')
        True

        """
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.element_id)

    def name_id_tuple(self):
        """Return the OSM type and ID as a tuple

        This is sometimes useful for a lower-memory representation of
        elements.  (Debatably - this should be considered for removal.)
        FIXME: also should rename this to type_id_tuple

        >>> n = Node('123456', latitude="52", longitude="0")
        >>> n.tags['name'] = 'Cambridge'
        >>> n.name_id_tuple()
        ('node', '123456')
        """

        return (self.element_type, self.element_id)

    def get_name(self):
        """Get a human-readable name for the element, if possible

        >>> germany = Relation("51477")
        >>> tags = {'name': 'Deutschland',
        ...         'name:en': 'Federal Republic of Germany'}
        >>> germany.tags.update(tags)
        >>> germany.get_name()
        'Deutschland'
        """
        return get_name_from_tags(self.tags, self.element_type, self.element_id)

    @property
    def element_content_missing(self):
        return self.missing

    @staticmethod
    def make_missing_element(element_type, element_id):
        """Create an element for which we only know the type and ID

        It is useful to be able to represent OSM elements that we've
        just seen mentioned as members of relations, but haven't
        actually parsed.  You can use this static method to create a
        node of such a type:

        >>> OSMElement.make_missing_element('node', '42')
        Node(id="42", missing)
        >>> OSMElement.make_missing_element('way', '7')
        Way(id="7", missing)
        >>> OSMElement.make_missing_element('relation', '13')
        Relation(id="13", missing)
        >>> OSMElement.make_missing_element('other', '2')
        Traceback (most recent call last):
          ...
        Exception: Unknown element name 'other'
        """

        if element_type == "node":
            return Node(element_id, element_content_missing=True)
        elif element_type == "way":
            return Way(element_id, element_content_missing=True)
        elif element_type == "relation":
            return Relation(element_id, element_content_missing=True)
        else:
            raise Exception, "Unknown element name '%s'" % (element_type,)

    def __repr__(self):
        """A returns simple repr-style representation of the OSMElement

        For example:

        >>> OSMElement('23', element_type='node')
        OSMElement(id="23", type="node")

        >>> OSMElement('25', element_content_missing=True, element_type='relation')
        OSMElement(id="25", type="relation", missing)
        """

        if self.element_content_missing:
            return 'OSMElement(id="%s", type="%s", missing)' % (self.element_id,
                                                                self.element_type)
        else:
            return 'OSMElement(id="%s", type="%s")' % (self.element_id,
                                                       self.element_type)

    def get_missing_elements(self, to_append_to=None):
        """Return a list of element type, id tuples of missing elements

        In the case of an element without children, this should either
        return an empty list or a list with this element in it,
        depending on whether it's marked as missing or not:

        >>> missing = OSMElement('42', element_content_missing=True, element_type="node")
        >>> missing.get_missing_elements()
        [('node', '42')]
        >>> present = OSMElement('42', element_type="node")
        >>> present.get_missing_elements()
        []

        If to_append_to is supplied, the missing elements should be
        appended to that array, and the same array returned:

        >>> l = []
        >>> result = missing.get_missing_elements(l)
        >>> l is result
        True
        >>> l
        [('node', '42')]
        """
        if to_append_to is None:
            to_append_to = []
        if self.element_content_missing:
            to_append_to.append(self.name_id_tuple())
        return to_append_to

    @staticmethod
    def xml_wrapping():
        """Get an XML element that OSM nodes/ways/relations can be added to

        The returned object is an etree.Element, which can be
        pretty-printed with etree.tostring:

        >>> print etree.tostring(OSMElement.xml_wrapping(), pretty_print=True),
        <osm version="0.6" generator="mySociety Boundary Extractor">
          <note>The data included in this document is from www.openstreetmap.org. It has there been collected by a large group of contributors. For individual attribution of each item please refer to http://www.openstreetmap.org/api/0.6/[node|way|relation]/#id/history</note>
        </osm>
        """

        osm = etree.Element("osm", attrib={"version": "0.6",
                                           "generator": "mySociety Boundary Extractor"})
        note = etree.SubElement(osm, "note")
        note.text = "The data included in this document is from www.openstreetmap.org. It has there been collected by a large group of contributors. For individual attribution of each item please refer to http://www.openstreetmap.org/api/0.6/[node|way|relation]/#id/history"
        return osm

    def xml_add_tags(self, xml_element):
        """Add the tags from this OSM element to an XML element

        >>> n = Node('42')
        >>> n.tags.update({'name': 'Venezia',
        ...                'name:en': 'Venice'})
        >>> xe = etree.Element('example')
        >>> n.xml_add_tags(xe)
        >>> print etree.tostring(xe, pretty_print=True),
        <example>
          <tag k="name" v="Venezia"/>
          <tag k="name:en" v="Venice"/>
        </example>
        """

        for k, v in sorted(self.tags.items()):
            etree.SubElement(xml_element, 'tag', attrib={'k': k, 'v': v})

class Node(OSMElement):

    """Represents an OSM node

    You can create a complete node as follows:

    >>> cambridge = Node("12345", latitude="52.205", longitude="0.119")
    >>> cambridge
    Node(id="12345", lat="52.205", lon="0.119")

    Each node has a tags attribute as well:
    >>> cambridge.tags['name:en'] = "Cambridge"

    The tags can be seen with the .pretty() representation:

    >>> print cambridge.pretty(4)
        node (12345) lat: 52.205, lon: 0.119
          name:en => Cambridge

    If you only know the ID of the node, but not its latitude or
    longitude yet, you can create it as a 'missing' node with a
    static method from OSMElement:

    >>> missing = OSMElement.make_missing_element("node", "321")
    >>> missing
    Node(id="321", missing)

    """

    def __init__(self, node_id, latitude=None, longitude=None, element_content_missing=False):
        super(Node, self).__init__(node_id, element_content_missing, 'node')
        self.lat = latitude
        self.lon = longitude
        self.tags = {}

    def pretty(self, indent=0):
        i = u" "*indent
        result = i + u"node (%s) lat: %s, lon: %s" % (self.element_id, self.lat, self.lon)
        for k, v in sorted(self.tags.items()):
            result += u"\n%s  %s => %s" % (i, k, v)
        return result

    def lon_lat_tuple(self):
        """Return the latitude and longitude as a tuple of two strings

        >>> n = Node("1234", latitude="52", longitude="0.5")
        >>> n.lon_lat_tuple()
        ('0.5', '52')
        """
        return (self.lon, self.lat)

    def __repr__(self):
        if self.element_content_missing:
            return 'Node(id="%s", missing)' % (self.element_id)
        else:
            return 'Node(id="%s", lat="%s", lon="%s")' % (self.element_id,
                                                          self.lat,
                                                          self.lon)

    def to_xml(self, parent_element=None, include_node_dependencies=False):
        """Generate an XML element representing this node

        If parent_element is supplied, it is added to that element and
        returned.  If no parent_element is supplied, an OSM XML root
        element is created, and the generated <node> element is added
        to that.

        >>> n = Node("1234", latitude="51.2", longitude="-0.2")
        >>> parent = etree.Element('example')
        >>> result = n.to_xml(parent_element=parent)
        >>> parent is result
        True
        >>> print etree.tostring(parent, pretty_print=True),
        <example>
          <node lat="51.2" lon="-0.2" id="1234"/>
        </example>
        >>> full_result = n.to_xml()
        >>> print etree.tostring(full_result, pretty_print=True),
        <osm version="0.6" generator="mySociety Boundary Extractor">
          <note>The data included in this document is from www.openstreetmap.org. It has there been collected by a large group of contributors. For individual attribution of each item please refer to http://www.openstreetmap.org/api/0.6/[node|way|relation]/#id/history</note>
          <node lat="51.2" lon="-0.2" id="1234"/>
        </osm>
        """

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

    """Represents an OSM way as returned via the Overpass API

    You can create a Way object as follows:

    >>> Way("314159265")
    Way(id="314159265", nodes=0)

    Or supply a list of nodes:

    >>> top_left = Node("12", latitude="52", longitude="1")
    >>> top_right = Node("13", latitude="52", longitude="2")
    >>> bottom_right = Node("14", latitude="51", longitude="2")
    >>> bottom_left = Node("15", latitude="51", longitude="1")

    >>> ns = [top_left,
    ...       top_right,
    ...       bottom_right,
    ...       bottom_left]
    >>> unclosed = Way("314159265", ns)
    >>> unclosed
    Way(id="314159265", nodes=4)

    You can iterate over the nodes:

    >>> for n in unclosed:
    ...     print n
    Node(id="12", lat="52", lon="1")
    Node(id="13", lat="52", lon="2")
    Node(id="14", lat="51", lon="2")
    Node(id="15", lat="51", lon="1")

    Or test if a node is closed or not:

    >>> unclosed.closed()
    False
    >>> nsc = ns + [top_left]
    >>> closed = Way("98765", nodes=nsc)
    >>> closed.closed()
    True

    """

    def __init__(self, way_id, nodes=None, element_content_missing=False):
        super(Way, self).__init__(way_id, element_content_missing, 'way')
        self.nodes = nodes or []
        self.tags = {}

    def __iter__(self):
        for n in self.nodes:
            yield n

    def __len__(self):
        """Allow len(way) to return the number of nodes

        For example:

        >>> w = Way("1", nodes=[Node("12", latitude="52", longitude="1"),
        ...                     Node("13", latitude="52", longitude="2"),
        ...                     Node("14", latitude="51", longitude="2")])
        >>> len(w)
        3
        """
        return len(self.nodes)

    def __getitem__(self, val):
        """Allow access to nodes with array notation

        For example:
        >>> w = Way('76543', nodes=[Node("12", latitude="52", longitude="1"),
        ...                         Node("13", latitude="52", longitude="2"),
        ...                         Node("14", latitude="51", longitude="2")])
        >>> w[2]
        Node(id="14", lat="51", lon="2")
        """
        return self.nodes.__getitem__(val)

    def pretty(self, indent=0):
        """Generate a fuller string representation of this way

        For example:

        >>> w = Way('76543', nodes=[Node("12", latitude="52", longitude="1"),
        ...                         Node("13", latitude="52", longitude="2"),
        ...                         Node("14", latitude="51", longitude="1"),
        ...                         Node("15", latitude="51", longitude="2")])
        >>> w.tags['random_key'] = 'some value or other'
        >>> w.tags['boundary'] = 'administrative'
        >>> print w.pretty(2)
          way (76543)
            boundary => administrative
            random_key => some value or other
            node (12) lat: 52, lon: 1
            node (13) lat: 52, lon: 2
            node (14) lat: 51, lon: 1
            node (15) lat: 51, lon: 2
        """

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
        """Try to join another way to this one.

        This will succeed if they can be joined at either end, and
        otherwise returns None.

        As examples, consider joining two edges of a square in various
        ways:

             top_left -- top_right

                 |           |

          bottom_left -- bottom_right

        In the examples below, we try to join the top edge to the
        right in four distinct ways:

        >>> top_left = Node("12", latitude="52", longitude="1")
        >>> top_right = Node("13", latitude="52", longitude="2")
        >>> bottom_right = Node("14", latitude="51", longitude="2")
        >>> bottom_left = Node("15", latitude="51", longitude="1")

        >>> top_cw = Way("3456", nodes=[top_left, top_right])
        >>> right_cw = Way("1234", nodes=[top_right, bottom_right])
        >>> bottom_cw = Way("6789", nodes=[bottom_right, bottom_left])

        >>> joined = top_cw.join(right_cw)
        >>> print joined.pretty(2)
          way (None)
            node (12) lat: 52, lon: 1
            node (13) lat: 52, lon: 2
            node (14) lat: 51, lon: 2

        >>> top_ccw = Way("4567", nodes=[top_right, top_left])
        >>> joined = top_ccw.join(right_cw)
        >>> print joined.pretty(2)
          way (None)
            node (14) lat: 51, lon: 2
            node (13) lat: 52, lon: 2
            node (12) lat: 52, lon: 1

        >>> right_ccw = Way("2345", nodes=[bottom_right, top_right])
        >>> joined = top_ccw.join(right_ccw)
        >>> print joined.pretty(2)
          way (None)
            node (14) lat: 51, lon: 2
            node (13) lat: 52, lon: 2
            node (12) lat: 52, lon: 1

        >>> joined = top_cw.join(right_ccw)
        >>> print joined.pretty(2)
          way (None)
            node (12) lat: 52, lon: 1
            node (13) lat: 52, lon: 2
            node (14) lat: 51, lon: 2

        Closed ways cannot be joined, and throw exceptions as in these
        examples:

        >>> closed = Way("5678", nodes=[top_left,
        ...                             top_right,
        ...                             bottom_right,
        ...                             bottom_left,
        ...                             top_left])
        >>> joined = closed.join(top_cw)
        Traceback (most recent call last):
           ...
        Exception: Trying to join a closed way to another

        >>> closed = Way("5678", nodes=[top_left,
        ...                             top_right,
        ...                             bottom_right,
        ...                             bottom_left,
        ...                             top_left])
        >>> joined = top_cw.join(closed)
        Traceback (most recent call last):
           ...
        Exception: Trying to join a way to a closed way

        Finally, an exception is also thrown if there are no end
        points in common between the two ways:

        >>> top_cw.join(bottom_cw)
        Traceback (most recent call last):
           ...
        Exception: Trying to join two ways with no end point in common
        """

        if self.closed():
            raise Exception, "Trying to join a closed way to another"
        if other.closed():
            raise Exception, "Trying to join a way to a closed way"
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
        meridian.

        >>> w = Way('76543', nodes=[Node("12", latitude="52", longitude="1"),
        ...                         Node("13", latitude="52", longitude="2"),
        ...                         Node("14", latitude="51", longitude="1"),
        ...                         Node("15", latitude="51", longitude="2")])
        >>> w.bounding_box_tuple()
        (51.0, 1.0, 52.0, 2.0)

        As another example close to the -180 degree meridian, create a
        closed way somewhere in Alaska:


        >>> w = Way('76543', nodes=[Node("12", latitude="62", longitude="-149"),
        ...                         Node("13", latitude="62", longitude="-150"),
        ...                         Node("14", latitude="61", longitude="-149"),
        ...                         Node("15", latitude="61", longitude="-150")])
        >>> w.bounding_box_tuple()
        (61.0, 210.0, 62.0, 211.0)



        """

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
        """A returns simple repr-style representation of the Way

        >>> Way('81')
        Way(id="81", nodes=0)
        >>> OSMElement.make_missing_element('way', '49')
        Way(id="49", missing)
        """

        if self.element_content_missing:
            return 'Way(id="%s", missing)' % (self.element_id,)
        else:
            return 'Way(id="%s", nodes=%d)' % (self.element_id, len(self.nodes))

    def get_missing_elements(self, to_append_to=None):
        """Return a list of element type, id tuples of missing elements

        In the case of an element without children, this should either
        return an empty list or a list with this element in it,
        depending on whether it's marked as missing or not:

        >>> nodes = [OSMElement.make_missing_element('node', '43'),
        ...          Node('44'),
        ...          Node('45'),
        ...          OSMElement.make_missing_element('node', '46')]
        >>> w = Way("42", nodes=nodes)
        >>> w.get_missing_elements()
        [('node', '43'), ('node', '46')]

        >>> l = [('relation', '47')]
        >>> result = w.get_missing_elements(l)
        >>> l is result
        True
        >>> l
        [('relation', '47'), ('node', '43'), ('node', '46')]
        """

        to_append_to = OSMElement.get_missing_elements(self, to_append_to)
        for node in self:
            node.get_missing_elements(to_append_to)
        return to_append_to

    def to_xml(self, parent_element=None, include_node_dependencies=False):
        """Generate an XML element representing this way

        If parent_element is supplied, it is added to that element and
        returned.  If no parent_element is supplied, an OSM XML root
        element is created, and the generated <node> element is added
        to that.

        >>> w = Way('76543', nodes=[Node("12", latitude="52", longitude="1"),
        ...                         Node("13", latitude="52", longitude="2"),
        ...                         Node("14", latitude="51", longitude="1"),
        ...                         Node("15", latitude="51", longitude="2")])
        >>> w.tags.update({'boundary': 'administrative',
        ...                'admin_level': '2'})
        >>> xe = etree.Element('example')
        >>> result = w.to_xml(xe)
        >>> result is xe
        True
        >>> print etree.tostring(xe, pretty_print=True),
        <example>
          <way id="76543">
            <nd ref="12"/>
            <nd ref="13"/>
            <nd ref="14"/>
            <nd ref="15"/>
            <tag k="admin_level" v="2"/>
            <tag k="boundary" v="administrative"/>
          </way>
        </example>

        Sometimes we'd like to output the nodes that are in a way at the same time:

        >>> xe = etree.Element('example-with-nodes')
        >>> w.to_xml(xe, include_node_dependencies=True) #doctest: +ELLIPSIS
        <Element example-with-nodes at ...>
        >>> print etree.tostring(xe, pretty_print=True),
        <example-with-nodes>
          <node lat="52" lon="1" id="12"/>
          <node lat="52" lon="2" id="13"/>
          <node lat="51" lon="1" id="14"/>
          <node lat="51" lon="2" id="15"/>
          <way id="76543">
            <nd ref="12"/>
            <nd ref="13"/>
            <nd ref="14"/>
            <nd ref="15"/>
            <tag k="admin_level" v="2"/>
            <tag k="boundary" v="administrative"/>
          </way>
        </example-with-nodes>

        And the final option is to include the OSM XML boilerplate as well:

        >>> result = w.to_xml()
        >>> print etree.tostring(result, pretty_print=True),
        <osm version="0.6" generator="mySociety Boundary Extractor">
          <note>The data included in this document is from www.openstreetmap.org. It has there been collected by a large group of contributors. For individual attribution of each item please refer to http://www.openstreetmap.org/api/0.6/[node|way|relation]/#id/history</note>
          <way id="76543">
            <nd ref="12"/>
            <nd ref="13"/>
            <nd ref="14"/>
            <nd ref="15"/>
            <tag k="admin_level" v="2"/>
            <tag k="boundary" v="administrative"/>
          </way>
        </osm>
        """

        if parent_element is None:
            parent_element = OSMElement.xml_wrapping()
        if include_node_dependencies:
            for node in self:
                node.to_xml(parent_element, include_node_dependencies)
        way = etree.SubElement(parent_element,
                               'way',
                               attrib={'id': self.element_id})
        for node in self:
            etree.SubElement(way, 'nd', attrib={'ref': node.element_id})
        self.xml_add_tags(way)
        return parent_element

    def reconstruct_missing(self, parser, id_to_node):
        """Replace any missing nodes from the parser's cache or id_to_node

        id_to_node should be a dictionary that maps IDs of nodes (as
        strings) the complete Node object or None.  parser should have
        a method called get_known_or_fetch('node', element_id) which
        will return None or the complete Node object, if the parser
        can find it.

        If any nodes could not be found from parser or id_to_node,
        they are returned as a list.  Therefore, if the way could be
        completely reconstructed, [] will be returned.

        >>> w = Way('76543', nodes=[Node("12", latitude="52", longitude="1"),
        ...                         OSMElement.make_missing_element('node', '13'),
        ...                         OSMElement.make_missing_element('node', '14'),
        ...                         Node("15", latitude="51", longitude="2")])
        >>> class FakeParser:
        ...     def get_known_or_fetch(self, element_type, element_id):
        ...         if element_type != 'node':
        ...             return None
        ...         if element_id == "14":
        ...             return Node("14", latitude="52.4", longitude="2.1")
        ...         return None
        >>> node_cache = {"13": Node("13", latitude="51.2", longitude="1.3"),
        ...               "22": None}
        >>> w.reconstruct_missing(FakeParser(), node_cache)
        []

        >>> w = Way('76543', nodes=[Node("21", latitude="52", longitude="1"),
        ...                         OSMElement.make_missing_element('node', '22'),
        ...                         OSMElement.make_missing_element('node', '23'),
        ...                         Node("24", latitude="51", longitude="2")])
        >>> w.reconstruct_missing(FakeParser(), node_cache)
        [Node(id="22", missing), Node(id="23", missing)]
        """

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
            if (found_node is not None) and (not found_node.element_content_missing):
                self.nodes[i] = found_node
            else:
                still_missing.append(node)
        return still_missing

class Relation(OSMElement):

    """Represents an OSM relation as returned via the Overpass API"""

    def __init__(self, relation_id, element_content_missing=False):
        super(Relation, self).__init__(relation_id, element_content_missing, 'relation')
        # A relation has an ordered list of children, which we store
        # as a list of tuples.  The first element of each tuple is a
        # Node, Way or Relation, and the second is a "role" string.
        self.children = []
        self.tags = {}

    def __iter__(self):
        for c in self.children:
            yield c

    def __len__(self):
        return len(self.children)

    def __getitem__(self, val):
        return self.children.__getitem__(val)

    def add_member(self, new_member, role=''):
        self.children.append((new_member, role))

    def pretty(self, indent=0):
        """Generate a fuller string representation of this way

        For example:

        >>> r = Relation('98765')
        >>> r.add_member(Node('76542', latitude="51.0", longitude="0.3"))
        >>> r.add_member(Way('76543'))
        >>> r.add_member(Way('76544'), role='inner')
        >>> r.add_member(Way('76545'), role='inner')
        >>> r.add_member(Way('76546'))
        >>> r.tags['random_key'] = 'some value or other'
        >>> r.tags['boundary'] = 'administrative'
        >>> print r.pretty(2)
          relation (98765)
            boundary => administrative
            random_key => some value or other
            child node with role ''
              node (76542) lat: 51.0, lon: 0.3
            child way with role ''
              way (76543)
            child way with role 'inner'
              way (76544)
            child way with role 'inner'
              way (76545)
            child way with role ''
              way (76546)
        """

        i = u" "*indent
        result = i + u"relation (%s)" % (self.element_id)
        for k, v in sorted(self.tags.items()):
            result += u"\n%s  %s => %s" % (i, k, v)
        for child, role in self.children:
            result += u"\n%s  child %s" % (i, child.element_type)
            result += u" with role '%s'" % (role)
            result += u"\n" + child.pretty(indent + 4)
        return result

    def way_iterator(self, inner=False):
        """Iterate over the ways in this relation

        If inner is set, iterate only over ways with the roles 'inner'
        or 'enclave' - otherwise miss them out.

        For example:

        >>> subr1 = Relation('98764')
        >>> subr1.add_member(Way('54319'), role='inner')
        >>> subr1.add_member(Way('54320'))

        >>> subr2 = Relation('87654')
        >>> subr2.add_member(Way('54321'))
        >>> subr2.add_member(Way('54322'), role='inner')

        >>> r = Relation('98765')
        >>> r.add_member(Node('76542', latitude="51.0", longitude="0.3"))
        >>> r.add_member(Way('76543'))
        >>> r.add_member(subr1)
        >>> r.add_member(Way('76544'), role='inner')
        >>> r.add_member(Way('76545'), role='inner')
        >>> r.add_member(subr2, role='inner')
        >>> r.add_member(Way('76546'))

        >>> for w in r.way_iterator():
        ...     print w
        Way(id="76543", nodes=0)
        Way(id="54320", nodes=0)
        Way(id="76546", nodes=0)

        >>> for w in r.way_iterator(inner=True):
        ...     print w
        Way(id="76544", nodes=0)
        Way(id="76545", nodes=0)
        Way(id="54322", nodes=0)
        """

        for child, role in self.children:
            if inner:
                if role not in ('enclave', 'inner'):
                    continue
            else:
                if role and role != 'outer':
                    continue
            if child.element_type == 'way':
                yield child
            elif child.element_type == 'relation':
                for sub_way in child.way_iterator(inner):
                    yield sub_way

    def __repr__(self):
        """A returns simple repr-style representation of the OSMElement

        For example:

        >>> Relation('6')
        Relation(id="6", members=0)

        >>> OSMElement.make_missing_element('relation', '7')
        Relation(id="7", missing)
        """

        if self.element_content_missing:
            return 'Relation(id="%s", missing)' % (self.element_id,)
        else:
            return 'Relation(id="%s", members=%d)' % (self.element_id, len(self.children))

    def get_missing_elements(self, to_append_to=None):
        """Return a list of element type, id tuples of missing elements

        In the case of an element without children, this should either
        return an empty list or a list with this element in it,
        depending on whether it's marked as missing or not:

        >>> r1 = Relation('77')
        >>> r1.get_missing_elements()
        []
        >>> r2 = OSMElement.make_missing_element('relation', '78')
        >>> r2.get_missing_elements()
        [('relation', '78')]

        >>> subr1 = Relation('98764')
        >>> subr1.add_member(Way('54319'), role='inner')
        >>> subr1.add_member(OSMElement.make_missing_element('relation', '54320'))
        >>> subr1.add_member(OSMElement.make_missing_element('way', '54321'))

        >>> subr2 = Relation('87654')
        >>> subr2.add_member(Way('54322'))
        >>> subr2.add_member(Way('54323'), role='inner')

        >>> r = Relation('98765')
        >>> r.add_member(OSMElement.make_missing_element('node', '76542'))
        >>> r.add_member(Way('76543'))
        >>> r.add_member(subr1)
        >>> r.add_member(OSMElement.make_missing_element('way', '98764'))
        >>> r.add_member(Way('76545'), role='inner')
        >>> r.add_member(subr2, role='inner')
        >>> r.add_member(Way('76546'))

        >>> r.get_missing_elements()
        [('node', '76542'), ('relation', '54320'), ('way', '54321'), ('way', '98764')]
        """

        to_append_to = OSMElement.get_missing_elements(self, to_append_to)
        for member, role in self:
            if role not in OSMXMLParser.IGNORED_ROLES:
                member.get_missing_elements(to_append_to)
        return to_append_to

    def to_xml(self, parent_element=None, include_node_dependencies=False):
        """Generate an XML element representing this relation

        If parent_element is supplied, it is added to that element and
        returned.  If no parent_element is supplied, an OSM XML root
        element is created, and the generated <node> element is added
        to that.

        >>> subr1 = Relation('98764')
        >>> subr1.add_member(Way('54319'), role='inner')
        >>> subr1.add_member(OSMElement.make_missing_element('relation', '54320'))
        >>> subr1.add_member(OSMElement.make_missing_element('way', '54321'))

        >>> subr2 = Relation('87654')
        >>> subr2.add_member(Way('54322'))
        >>> subr2.add_member(Way('54323'), role='inner')

        >>> r = Relation('98765')
        >>> r.add_member(Node('76542', latitude='52', longitude='0.3'))
        >>> r.add_member(Way('76543'))
        >>> r.add_member(subr1)
        >>> r.add_member(OSMElement.make_missing_element('way', '98764'))
        >>> r.add_member(Way('76545'), role='inner')
        >>> r.add_member(subr2, role='inner')
        >>> r.add_member(Way('76546'))

        >>> r.tags.update({'boundary': 'administrative',
        ...                'admin_level': '2'})
        >>> xe = etree.Element('example')
        >>> result = r.to_xml(xe)
        >>> result is xe
        True
        >>> print etree.tostring(xe, pretty_print=True),
        <example>
          <relation id="98765">
            <member ref="76542" role="" type="node"/>
            <member ref="76543" role="" type="way"/>
            <member ref="98764" role="" type="relation"/>
            <member ref="98764" role="" type="way"/>
            <member ref="76545" role="inner" type="way"/>
            <member ref="87654" role="inner" type="relation"/>
            <member ref="76546" role="" type="way"/>
            <tag k="admin_level" v="2"/>
            <tag k="boundary" v="administrative"/>
          </relation>
        </example>

        Sometimes we'd like to output the nodes that are included at the same time:

        >>> xe = etree.Element('example-with-nodes')
        >>> r.to_xml(xe, include_node_dependencies=True) #doctest: +ELLIPSIS
        <Element example-with-nodes at ...>
        >>> print etree.tostring(xe, pretty_print=True),
        <example-with-nodes>
          <node lat="52" lon="0.3" id="76542"/>
          <relation id="98765">
            <member ref="76542" role="" type="node"/>
            <member ref="76543" role="" type="way"/>
            <member ref="98764" role="" type="relation"/>
            <member ref="98764" role="" type="way"/>
            <member ref="76545" role="inner" type="way"/>
            <member ref="87654" role="inner" type="relation"/>
            <member ref="76546" role="" type="way"/>
            <tag k="admin_level" v="2"/>
            <tag k="boundary" v="administrative"/>
          </relation>
        </example-with-nodes>


        And the final option is to include the OSM XML boilerplate as well:

        >>> result = r.to_xml()
        >>> print etree.tostring(result, pretty_print=True),
        <osm version="0.6" generator="mySociety Boundary Extractor">
          <note>The data included in this document is from www.openstreetmap.org. It has there been collected by a large group of contributors. For individual attribution of each item please refer to http://www.openstreetmap.org/api/0.6/[node|way|relation]/#id/history</note>
          <relation id="98765">
            <member ref="76542" role="" type="node"/>
            <member ref="76543" role="" type="way"/>
            <member ref="98764" role="" type="relation"/>
            <member ref="98764" role="" type="way"/>
            <member ref="76545" role="inner" type="way"/>
            <member ref="87654" role="inner" type="relation"/>
            <member ref="76546" role="" type="way"/>
            <tag k="admin_level" v="2"/>
            <tag k="boundary" v="administrative"/>
          </relation>
        </osm>

        An exception should be thrown if a missing node is included,
        and include_node_dependencies is true:

        >>> r = Relation('1234')
        >>> r.add_member(OSMElement.make_missing_element('node', '17'))
        >>> example = etree.Element('exception-example')
        >>> r.to_xml(example, include_node_dependencies=True)
        Traceback (most recent call last):
          ...
        Exception: Trying out output a missing node %s as XML
        """

        if parent_element is None:
            parent_element = OSMElement.xml_wrapping()
        relation = etree.Element('relation',
                                 attrib={'id': self.element_id})
        members_xml = []
        for member, role in self:
            if include_node_dependencies and member.element_type == "node":
                if member.element_content_missing:
                    raise Exception, "Trying out output a missing node %s as XML"
                member.to_xml(parent_element, include_node_dependencies)
            etree.SubElement(relation,
                             'member',
                             attrib={'type': member.element_type,
                                     'ref': member.element_id,
                                     'role': role})
        parent_element.append(relation)
        self.xml_add_tags(relation)
        return parent_element

    def reconstruct_missing(self, parser, id_to_node):
        """Replace any missing nodes from the parser's cache or id_to_node

        id_to_node should be a dictionary that maps IDs of nodes (as
        strings) the complete Node object or None.  parser should have
        a method called get_known_or_fetch('node', element_id) which
        will return None or the complete Node object, if the parser
        can find it.

        If any nodes could not be found from parser or id_to_node,
        they are returned as a list.  Therefore, if the way could be
        completely reconstructed, [] will be returned.

        >>> def make_incomplete_relation():
        ...     w = Way('76543', nodes=[Node("12", latitude="52", longitude="1"),
        ...                             OSMElement.make_missing_element('node', '13'),
        ...                             OSMElement.make_missing_element('node', '14'),
        ...                             Node("15", latitude="51", longitude="2")])
        ...     r = Relation('76544')
        ...     r.add_member(Node("16", latitude="50", longitude="0"))
        ...     r.add_member(w)
        ...     r.add_member(OSMElement.make_missing_element('relation', '76545'), role='defaults')
        ...     r.add_member(Way('17'))
        ...     r.add_member(OSMElement.make_missing_element('way', '18'))
        ...     r.add_member(OSMElement.make_missing_element('node', '19'))
        ...     r.add_member(OSMElement.make_missing_element('node', '20'))
        ...     return r
        >>> r = make_incomplete_relation()
        >>> class FakeParser:
        ...     def get_known_or_fetch(self, element_type, element_id):
        ...         if element_type != 'node':
        ...             return OSMElement.make_missing_element(element_type, element_id)
        ...         if element_id == "14":
        ...             return Node("14", latitude="52.4", longitude="2.1")
        ...         return OSMElement.make_missing_element(element_type, element_id)
        >>> node_cache = {"13": Node("13", latitude="51.2", longitude="1.3"),
        ...               "19": None,
        ...               "20": Node("20", latitude="51.3", longitude="1.1"),
        ...               "22": None}
        >>> r.reconstruct_missing(FakeParser(), node_cache)
        [Way(id="18", missing), Node(id="19", missing)]

        Supposing that both those caches are empty, all of the missing
        elements should be returned:

        >>> r = make_incomplete_relation()
        >>> class FakeEmptyParser:
        ...     def get_known_or_fetch(self, element_type, element_id):
        ...         return OSMElement.make_missing_element(element_type, element_id)
        >>> node_cache = {}
        >>> r.reconstruct_missing(FakeEmptyParser(), node_cache)
        [Node(id="13", missing), Node(id="14", missing), Way(id="18", missing), Node(id="19", missing), Node(id="20", missing)]
        """

        still_missing = []
        for i, t in enumerate(self.children):
            member, role = t
            if role in OSMXMLParser.IGNORED_ROLES:
                continue
            element_type = member.element_type
            element_id = member.element_id
            if member.element_content_missing:
                found_element = None
                if element_type == 'node':
                    if element_id in id_to_node:
                        found_element = id_to_node[element_id]
                if not found_element:
                    # Ask the parser to try to fetch it from its filesystem cache:
                    found_element = parser.get_known_or_fetch(element_type, element_id)
                if (found_element is not None) and (not found_element.element_content_missing):
                    self.children[i] = (found_element, role)
                else:
                    still_missing.append(member)
            else:
                # Even if the element isn't marked as missing, it may
                # contain nodes, ways or relations that *are* missing,
                # so we have to recurse:
                if element_type != 'node':
                    still_missing.extend(member.reconstruct_missing(parser, id_to_node))

        return still_missing

class UnexpectedElementException(Exception):
    def __init__(self, element_name, message):
        self.element_name = element_name
        self.message = message
    def __str__(self):
        return self.message

class OSMXMLParser(ContentHandler):

    """A SAX-based parser for data from OSM's Overpass API

    This has two main modes of operation.  The first builds a
    structure of Node, Way and Relation objects that represent the
    returned data, fetching missing elements as necessary, keeping
    these all in memory.  Typically one would then call
    get_known_or_fetch on this object to get back data for a
    particular element.

    The second allows you to supply a callback that will be called for
    each top-level element as it's parsed, which takes a minimal
    amount of memory.

    >>> valid_xml = '''<?xml version="1.0" encoding="UTF-8"?>
    ... <osm version="0.6" generator="Overpass API">
    ...   <node id="291974462" lat="55.0548850" lon="-2.9544991"/>
    ...   <node id="312203528" lat="54.4600000" lon="-5.0596341"/>
    ...   <way id="28421671">
    ...     <nd ref="291974462"/>
    ...     <nd ref="312203528"/>
    ...   </way>
    ...   <relation id="3123205528">
    ...     <member type="way" ref="28421671" role="inner"/>
    ...      <tag k="name:en" v="Whatever"/>
    ...   </relation>
    ... </osm>'''
    >>> parser = parse_xml_string(valid_xml, fetch_missing=False)
    >>> len(parser)
    4
    >>> parser.empty()
    False

    If any unexpected elements occur, an exception is thrown:

    >>> parse_xml_string('''<?xml version="1.0" encoding="UTF-8"?>
    ... <osm version="0.6" generator="Overpass API">
    ...   <blah/>
    ... </osm>''', fetch_missing=False)
    Traceback (most recent call last):
      ...
    UnexpectedElementException: Should never get a <blah> at the top level

    Similarly for unexpected elements at lower level:

    >>> parse_xml_string('''<?xml version="1.0" encoding="UTF-8"?>
    ... <osm version="0.6" generator="Overpass API">
    ...   <node id="123" lat="52" lon="0">
    ...     <foo>
    ...   </node>
    ... </osm>''', fetch_missing=False)
    Traceback (most recent call last):
      ...
    UnexpectedElementException: Unhandled element <foo>

    Some elements can only be nested in others:

    >>> parse_xml_string('''<?xml version="1.0" encoding="UTF-8"?>
    ... <osm version="0.6" generator="Overpass API">
    ...   <node id="123" lat="52" lon="0">
    ...     <member type="way" ref="345" role=""/>
    ...   </node>
    ... </osm>''', fetch_missing=False)
    Traceback (most recent call last):
      ...
    UnexpectedElementException: Didn't expect to find <member> in a <node>, can only be in <relation>

    And some elements can't be at the top level:

    >>> parse_xml_string('''<?xml version="1.0" encoding="UTF-8"?>
    ... <osm version="0.6" generator="Overpass API">
    ...   <member type="way" ref="345" role=""/>
    ... </osm>''', fetch_missing=False)
    Traceback (most recent call last):
      ...
    UnexpectedElementException: Should never get a <member> at the top level

    Top-level elements should never be found at a sub-level:

    >>> parse_xml_string('''<?xml version="1.0" encoding="UTF-8"?>
    ... <osm version="0.6" generator="Overpass API">
    ...   <node id="123" lat="52" lon="0">
    ...     <node>
    ...   </node>
    ... </osm>''', fetch_missing=False)
    Traceback (most recent call last):
      ...
    UnexpectedElementException: Should never get a new <node> when still in a top-level element

    The types of members of relations must be known:

    >>> parse_xml_string('''<?xml version="1.0" encoding="UTF-8"?>
    ... <osm version="0.6" generator="Overpass API">
    ...   <relation id="3123205528">
    ...     <member type="foo" ref="28421671" role="inner"/>
    ...   </relation>
    ... </osm>''', fetch_missing=False)
    Traceback (most recent call last):
      ...
    Exception: Unknown member type 'foo' in <relation>

    Parsed elements are normally cached:

    >>> parser = parse_xml_string(valid_xml, fetch_missing=False)
    >>> len(parser.known_nodes)
    2
    >>> len(parser.known_ways)
    1
    >>> len(parser.known_relations)
    1

    But the cache can be cleared:

    >>> parser.clear_caches()
    >>> len(parser.known_nodes) + len(parser.known_ways) + len(parser.known_relations)
    0

    Or you can request no caching in the first place:

    parser = parse_xml_string(valid_xml, cache_in_memory=False, fetch_missing=False)
    >>> len(parser.known_nodes) + len(parser.known_ways) + len(parser.known_relations)
    0

    Now some examples of using a callback instead:

    >>> def test(element, parser):
    ...    print "got element:", element
    >>> parser = parse_xml_string(valid_xml, fetch_missing=False, callback=test)
    got element: Node(id="291974462", lat="55.0548850", lon="-2.9544991")
    got element: Node(id="312203528", lat="54.4600000", lon="-5.0596341")
    got element: Way(id="28421671", nodes=2)
    got element: Relation(id="3123205528", members=1)

    And then trying to access the top-level elements in any way should
    throw an exception:

    >>> len(parser)
    Traceback (most recent call last):
      ...
    Exception: When parsed with a callback, no top level elements are kept in memory
    >>> parser.empty()
    Traceback (most recent call last):
      ...
    Exception: When parsed with a callback, no top level elements are kept in memory
    >>> for e in parser:
    ...    print e
    Traceback (most recent call last):
      ...
    Exception: When parsed with a callback, no top level elements are kept in memory

    If the elements are in an unhelpful order, then parsing still
    succeeds:

    >>> reordered_xml = '''<?xml version="1.0" encoding="UTF-8"?>
    ... <osm version="0.6" generator="Overpass API">
    ...   <relation id="3123205528">
    ...     <member type="way" ref="28421671" role="inner"/>
    ...      <tag k="name:en" v="Whatever"/>
    ...   </relation>
    ...   <way id="28421671">
    ...     <nd ref="291974462"/>
    ...     <nd ref="312203528"/>
    ...   </way>
    ...   <node id="291974462" lat="55.0548850" lon="-2.9544991"/>
    ...   <node id="312203528" lat="54.4600000" lon="-5.0596341"/>
    ... </osm>'''
    >>> tmp_cache = mkdtemp()
    >>> parser = parse_xml_string(reordered_xml,
    ...                           fetch_missing=False,
    ...                           cache_directory=tmp_cache)
    >>> for e in parser:
    ...     print e
    Relation(id="3123205528", members=1)
    Way(id="28421671", nodes=2)
    Node(id="291974462", lat="55.0548850", lon="-2.9544991")
    Node(id="312203528", lat="54.4600000", lon="-5.0596341")

    But some elements may be marked as missing:

    >>> r = parser[0]
    >>> r
    Relation(id="3123205528", members=1)
    >>> r[0]
    (Way(id="28421671", missing), u'inner')

    ... which can be fixed up with reconstruct_missing, which uses its
    in-memory cache:

    >>> still_missing = r.reconstruct_missing(parser, {})
    >>> still_missing
    []
    >>> parser[0][0]
    (Way(id="28421671", nodes=2), u'inner')

    If there are some missing elements which aren't in the XML at all,
    they can be fetched from the Overpass API if you have the
    fetch_missing option on (as it is by default):

    >>> tmp_cache = mkdtemp()
    >>> xml_requiring_fetch = '''<?xml version="1.0" encoding="UTF-8"?>
    ... <osm version="0.6" generator="Overpass API">
    ...   <relation id="1">
    ...     <member type="relation" ref="295353" role="example-subrelation"/>
    ...   </relation>
    ... </osm>'''
    >>> parser = parse_xml_string(xml_requiring_fetch,
    ...                           cache_directory=tmp_cache)
    >>> south_cambridgeshire_relation, fake_role = parser[0][0]
    >>> south_cambridgeshire_relation # doctest: +ELLIPSIS
    Relation(id="295353", members=...)
    >>> len(south_cambridgeshire_relation) > 0
    True

    Doing that again will be faster, since the results of the API will
    have been cached to disk, but still produce the same result:

    >>> parser = parse_xml_string(xml_requiring_fetch,
    ...                           cache_directory=tmp_cache)
    >>> south_cambridgeshire_relation, fake_role = parser[0][0]
    >>> south_cambridgeshire_relation # doctest: +ELLIPSIS
    Relation(id="295353", members=...)
    >>> len(south_cambridgeshire_relation) > 0
    True

    If some elements are totally non-existent, and we're not fetching:

    >>> xml_with_fictitious_refs = '''<?xml version="1.0" encoding="UTF-8"?>
    ... <osm version="0.6" generator="Overpass API">
    ...   <way id="28421671">
    ...     <nd ref="1000000000000"/>
    ...     <nd ref="1000000000001"/>
    ...   </way>
    ... </osm>'''
    >>> parser = parse_xml_string(xml_with_fictitious_refs,
    ...                           fetch_missing=False,
    ...                           cache_directory=tmp_cache)
    >>> for e in parser[0]:
    ...     print e
    Node(id="1000000000000", missing)
    Node(id="1000000000001", missing)

    If fetching isn't allowed, we get the same result the first time:

    >>> parser = parse_xml_string(xml_with_fictitious_refs,
    ...                           cache_directory=tmp_cache)
    >>> for e in parser[0]:
    ...     print e
    Node(id="1000000000000", missing)
    Node(id="1000000000001", missing)

    A second time, we find an empty file in the cache, which should
    give the same result.

    >>> parser = parse_xml_string(xml_with_fictitious_refs,
    ...                           cache_directory=tmp_cache) # doctest: +ELLIPSIS
    >>> for e in parser[0]:
    ...     print e
    Node(id="1000000000000", missing)
    Node(id="1000000000001", missing)

    Remove the temporary directory created for these doctests:
    >>> shutil.rmtree(tmp_cache)
    """

    VALID_TOP_LEVEL_ELEMENTS = set(('node', 'relation', 'way'))
    VALID_RELATION_MEMBERS = set(('node', 'relation', 'way'))
    IGNORED_TAGS = set(('osm', 'note', 'meta', 'bound'))
    IGNORED_ROLES = set(('subarea', 'defaults', 'apply_to'))

    def __init__(self, fetch_missing=True, callback=None, cache_in_memory=True, cache_directory=None):
        self.top_level_elements = []
        self.current_top_level_element = None
        # These dictionaries map ids to already discovered elements:
        self.known_nodes = {}
        self.known_ways = {}
        self.known_relations = {}
        self.fetch_missing = fetch_missing
        self.callback = callback
        self.cache_in_memory = cache_in_memory
        self.cache_directory = cache_directory

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

    def __getitem__(self, val):
        return self.top_level_elements.__getitem__(val)

    def raise_if_sub_level(self, name):
        if self.current_top_level_element is not None:
            raise UnexpectedElementException(name, "Should never get a new <%s> when still in a top-level element" % (name,))

    def raise_if_top_level(self, name):
        if self.current_top_level_element is None:
            raise UnexpectedElementException(name, "Should never get a <%s> at the top level" % (name,))

    def raise_unless_expected_parent(self, name, expected_parent):
        if self.current_top_level_element.element_type != expected_parent:
            wrong_parent = self.current_top_level_element.element_type
            raise UnexpectedElementException(name, "Didn't expect to find <%s> in a <%s>, can only be in <%s>" % (name, wrong_parent, expected_parent))

    def get_known_or_fetch(self, element_type, element_id, verbose=False):
        """Return an OSM Node, Way or Relation, fetching it if necessary

        If the element couldn't be found any means, an element marked
        with element_content_missing is returned."""
        element_id = str(element_id)
        if self.cache_in_memory:
            d = {'node': self.known_nodes,
                 'way': self.known_ways,
                 'relation': self.known_relations}[element_type]
            if element_id in d:
                return d[element_id]
        result = None
        # See if it is in the on-disk cache:
        cache_filename = get_cache_filename(element_type, element_id, self.cache_directory)
        if os.path.exists(cache_filename):
            parser = parse_xml(cache_filename, fetch_missing=self.fetch_missing)
            for e in parser.top_level_elements:
                if e.name_id_tuple() == (element_type, element_id):
                    result = e
                    break
            if result is None:
                if len(parser) == 0:
                    # If it's an empty file, just return a missing element:
                    return OSMElement.make_missing_element(element_type, element_id)
                else:
                    # However, if there's the wrong data in the file,
                    # that's worth looking into:
                    raise Exception, "Failed to find expected element in: " + cache_filename
        if result is None:
            if self.fetch_missing:
                result = fetch_osm_element(element_type,
                                           element_id,
                                           self.fetch_missing,
                                           verbose,
                                           self.cache_directory)
                if not result:
                    return OSMElement.make_missing_element(element_type, element_id)
            else:
                return OSMElement.make_missing_element(element_type, element_id)
        if self.cache_in_memory:
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
                if self.cache_in_memory:
                    self.known_nodes[element_id] = self.current_top_level_element
            elif name == "way":
                self.current_top_level_element = Way(element_id)
                if self.cache_in_memory:
                    self.known_ways[element_id] = self.current_top_level_element
            elif name == "relation":
                self.current_top_level_element = Relation(element_id)
                if self.cache_in_memory:
                    self.known_relations[element_id] = self.current_top_level_element
            else:
                # A programming error: something's been added to
                # VALID_TOP_LEVEL_ELEMENTS which isn't dealt with.
                assert "Unhandled top level element %s" % (name,) # pragma: no cover
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
                    raise Exception, "Unknown member type '%s' in <relation>" % (member_type,)
                if attr['role'] not in OSMXMLParser.IGNORED_ROLES:
                    member = self.get_known_or_fetch(member_type, attr['ref'])
                    self.current_top_level_element.children.append((member, attr['role']))
            elif name == "nd":
                self.raise_unless_expected_parent(name, 'way')
                node = self.get_known_or_fetch('node', attr['ref'])
                if node.element_content_missing:
                    if self.fetch_missing:
                         # print >> sys.stderr, "A node (%s) was referenced that couldn't be found" % (attr['ref'],)
                         pass
                    node = OSMElement.make_missing_element('node', attr['ref'])
                self.current_top_level_element.nodes.append(node)
            else:
                raise UnexpectedElementException(name, "Unhandled element <%s>" % (name,))

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

def fetch_cached(element_type, element_id, verbose=False, cache_directory=None):
    """Get an OSM element from the Overpass API, with caching on disk

    >>> tmp_cache = mkdtemp()
    >>> filename = fetch_cached('relation',
    ...                         '375982',
    ...                         cache_directory=tmp_cache)
    >>> filename # doctest: +ELLIPSIS
    '.../relation/982/relation-375982.xml'

    If you request an unknown element type, an exception is thrown:
    >>> filename = fetch_cached('nonsense',
    ...                         '1',
    ...                         cache_directory=tmp_cache)
    Traceback (most recent call last):
      ...
    Exception: Unknown element type 'nonsense'
    """

    global last_overpass_fetch
    arguments = (element_type, element_id)
    if element_type not in ('relation', 'way', 'node'):
        raise Exception, "Unknown element type '%s'" % (element_type,)
    filename = get_cache_filename(element_type, element_id, cache_directory)
    if not os.path.exists(filename):
        all_dependents_query = get_query_relation_and_dependents(element_type, element_id)
        get_from_overpass(all_dependents_query, filename)
    return filename

def parse_xml_minimal(filename, element_handler):
    """Parse some OSM XML just to get type, id and tags

    >>> def output(type, id, tags):
    ...     print "type:", type, "id:", id, "tags:", tags
    >>> example_xml = '''<?xml version="1.0" encoding="UTF-8"?>
    ... <osm version="0.6" generator="Overpass API">
    ...   <node id="291974462" lat="55.0548850" lon="-2.9544991"/>
    ...   <node id="312203528" lat="54.4600000" lon="-5.0596341"/>
    ...   <way id="28421671">
    ...     <nd ref="291974462"/>
    ...     <nd ref="312203528"/>
    ...   </way>
    ...   <relation id="3123205528">
    ...     <member type="way" ref="28421671" role="inner"/>
    ...      <tag k="name:en" v="Whatever"/>
    ...   </relation>
    ... </osm>
    ... '''
    >>> with NamedTemporaryFile(delete=False) as ntf:
    ...     ntf.write(example_xml)
    >>> parse_xml_minimal(ntf.name, output)
    type: node id: 291974462 tags: {}
    type: node id: 312203528 tags: {}
    type: way id: 28421671 tags: {}
    type: relation id: 3123205528 tags: {u'name:en': u'Whatever'}
    """
    parser = MinimalOSMXMLParser(element_handler)
    with open(filename) as fp:
        xml.sax.parse(fp, parser)

def parse_xml(filename, fetch_missing=True):
    """Completely parse an OSM XML file

    >>> example_xml = '''<?xml version="1.0" encoding="UTF-8"?>
    ... <osm version="0.6" generator="Overpass API">
    ...   <node id="291974462" lat="55.0548850" lon="-2.9544991"/>
    ...   <node id="312203528" lat="54.4600000" lon="-5.0596341"/>
    ...   <way id="28421671">
    ...     <nd ref="291974462"/>
    ...     <nd ref="312203528"/>
    ...   </way>
    ...   <relation id="3123205528">
    ...     <member type="way" ref="28421671" role="inner"/>
    ...      <tag k="name:en" v="Whatever"/>
    ...   </relation>
    ... </osm>
    ... '''
    >>> with NamedTemporaryFile(delete=False) as ntf:
    ...     ntf.write(example_xml)
    >>> parser = parse_xml(ntf.name, fetch_missing=False)
    >>> os.remove(ntf.name)
    >>> for top_level_element in parser:
    ...     print top_level_element
    Node(id="291974462", lat="55.0548850", lon="-2.9544991")
    Node(id="312203528", lat="54.4600000", lon="-5.0596341")
    Way(id="28421671", nodes=2)
    Relation(id="3123205528", members=1)
    """
    parser = OSMXMLParser(fetch_missing)
    with open(filename) as fp:
        xml.sax.parse(fp, parser)
    return parser

def parse_xml_string(s, *parser_args, **parser_kwargs):
    fp = StringIO(s)
    parser = OSMXMLParser(*parser_args, **parser_kwargs)
    xml.sax.parse(fp, parser)
    return parser

def fetch_osm_element(element_type, element_id, fetch_missing=True, verbose=False, cache_directory=None):
    """Fetch and parse a particular OSM element recursively

    More data is fetched from the API if required.  'element_type'
    should be one of 'relation', 'way' or 'node'.

    For example, you could request the relation representing Scotland
    with:

    >>> tmp_cache = mkdtemp()
    >>> fetch_osm_element("relation", "58446", cache_directory=tmp_cache)
    Relation(id="58446", members=71)

    Or do the same, more verbosely, with:

    >>> tmp_cache2 = mkdtemp()
    >>> fetch_osm_element("relation", "58446", verbose=True, cache_directory=tmp_cache2)
    fetch_osm_element(relation, 58446)
    Relation(id="58446", members=71)

    FIXME: fetching a non-existing element really should produce an
    exception, but at the moment just returns None

    >>> tmp_cache3 = mkdtemp()
    >>> fetch_osm_element('relation', '10000000000', cache_directory=tmp_cache3)

    Remove the temporary directories created for these doctests:
    >>> for d in (tmp_cache, tmp_cache2, tmp_cache3):
    ...     shutil.rmtree(d)
    """

    element_id = str(element_id)
    if verbose:
        print "fetch_osm_element(%s, %s)" % (element_type, element_id)
    # Make sure we have the XML file for that relation, node or way:
    filename = fetch_cached(element_type, element_id, verbose, cache_directory)
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
    you can join another Way to.  However, each endpoint can only map
    to one way.

    For example, create some nodes that are at the corners of a square

    >>> top_left = Node("12", latitude="52", longitude="1")
    >>> top_right = Node("13", latitude="52", longitude="2")
    >>> bottom_right = Node("14", latitude="51", longitude="2")
    >>> bottom_left = Node("15", latitude="51", longitude="1")

    ... and extra ones at the bottom left:

    >>> below_bottom_left = Node("16", latitude="50", longitude="1")
    >>> left_of_bottom_left = Node("17", latitude="51", longitude="0")

    And create a way which represents the left side (w), top and right
    sides (ne), bottom side (s) and edges coming down and left from
    the bottom left:

    >>> w = Way("1", nodes=[bottom_left, top_left])
    >>> ne = Way("2", nodes=[top_left, top_right, bottom_right])
    >>> s = Way("3", nodes=[bottom_right, bottom_left])
    >>> stalk_down = Way("4", nodes=[below_bottom_left, bottom_left])
    >>> stalk_left = Way("5", nodes=[left_of_bottom_left, bottom_left])

    Now add two to an EndpointToWayMap:

    >>> etwm = EndpointToWayMap()
    >>> etwm.add_way(ne)
    >>> etwm.add_way(stalk_down)

    Ways can them be retrieved by endpoints that overlap:

    >>> etwm.get_from_either_end(stalk_left)
    [Way(id="4", nodes=2)]
    >>> result = etwm.get_from_either_end(s)
    >>> set(result) == set([stalk_down, ne])
    True
    >>> etwm.number_of_endpoints()
    4

    You can output a readable version of the EndpointToWayMap:

    >>> print etwm.pretty(2)
      EndpointToWayMap:
        endpoint: node (12) lat: 52, lon: 1
          way.first: Node(id="12", lat="52", lon="1")
          way.last: Node(id="14", lat="51", lon="2")
        endpoint: node (14) lat: 51, lon: 2
          way.first: Node(id="12", lat="52", lon="1")
          way.last: Node(id="14", lat="51", lon="2")
        endpoint: node (15) lat: 51, lon: 1
          way.first: Node(id="16", lat="50", lon="1")
          way.last: Node(id="15", lat="51", lon="1")
        endpoint: node (16) lat: 50, lon: 1
          way.first: Node(id="16", lat="50", lon="1")
          way.last: Node(id="15", lat="51", lon="1")

    Ways can be removed from the map as well:

    >>> etwm.remove_way(ne)
    >>> etwm.remove_way(stalk_down)
    >>> etwm.get_from_either_end(w)
    []

    Adding a way that has endpoints that are already in the map is an
    error:

    >>> etwm.add_way(ne)
    >>> etwm.add_way(s)
    Traceback (most recent call last):
      ...
    Exception: Call to add_way would overwrite existing way(s)
    """

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
        for k, v in sorted(self.endpoints.items()):
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

    For example, if we create some points in a square:

    >>> top_left = Node("12", latitude="52", longitude="1")
    >>> top_right = Node("13", latitude="52", longitude="2")
    >>> bottom_right = Node("14", latitude="51", longitude="2")
    >>> bottom_left = Node("15", latitude="51", longitude="1")

    ... and extra ones at the bottom left:

    >>> below_bottom_left = Node("16", latitude="50", longitude="1")
    >>> left_of_bottom_left = Node("17", latitude="51", longitude="0")

    And create a way which represents the left side (w), top and right
    sides (ne), bottom side (s) and edges coming down and left from
    the bottom left:

    >>> w = Way("1", nodes=[bottom_left, top_left])
    >>> ne = Way("2", nodes=[top_left, top_right, bottom_right])
    >>> s = Way("3", nodes=[bottom_right, bottom_left])
    >>> stalk_down = Way("4", nodes=[below_bottom_left, bottom_left])
    >>> stalk_left = Way("5", nodes=[left_of_bottom_left, bottom_left])

    It shouldn't be possible to join stalk_left to ne:

    >>> join_way_soup([stalk_left, ne])
    Traceback (most recent call last):
    ...
    UnclosedBoundariesException

    And w and ne can be joined, but won't form a closed boundary (the
    bottom side of the square (s) is missing):

    >>> join_way_soup([w, ne])
    Traceback (most recent call last):
    ...
    UnclosedBoundariesException

    However, all of the sides of the square can be joined:

    >>> result = join_way_soup([w, ne, s])
    >>> result
    [Way(id="None", nodes=5)]

    If the way soup includes any missing ways, then just ignore them:
    >>> missing = OSMElement.make_missing_element('way', '7')
    >>> join_way_soup([w, ne, s, missing])
    [Way(id="None", nodes=5)]

    The nodes in the joined way should be the same as all the corners
    of the square (with one repeated once to join up again):

    >>> set(result[0].nodes) == set([top_left, top_right, bottom_left, bottom_right])
    True

    The ways supplied can from more than one closed polygon.  e.g.

    >>> other_top_left = Node("18", latitude="52", longitude="5")
    >>> other_top_right = Node("19", latitude="52", longitude="6")
    >>> other_bottom_right = Node("20", latitude="51", longitude="5")
    >>> other_bottom_left = Node("21", latitude="51", longitude="6")

    >>> other_nw = Way("6", nodes=[other_bottom_left, other_top_left, other_top_right])
    >>> other_se = Way("7", nodes=[other_top_right, other_bottom_right, other_bottom_left])

    >>> join_way_soup([s, w, ne, other_nw, other_se])
    [Way(id="None", nodes=5), Way(id="None", nodes=5)]

    But one closed polygon and an open one still fails:

    >>> join_way_soup([s, ne, other_nw, other_se])
    Traceback (most recent call last):
    ...
    UnclosedBoundariesException

    Another option is that one of the ways might already be closed,
    which is fine:

    >>> whole_square = Way("8", nodes=[top_left, top_right, bottom_right, bottom_left, top_left])
    >>> join_way_soup([whole_square, other_nw, other_se])
    [Way(id="8", nodes=5), Way(id="None", nodes=5)]
    """

    closed_ways = []
    endpoints_to_ways = EndpointToWayMap()
    for way in ways:
        if way.element_content_missing:
            continue
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

if __name__ == "__main__":

    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("--test", dest="doctest",
                      default=False, action='store_true',
                      help="Run all doctests in this file")
    parser.add_option("--relation", dest="relation",
                      metavar="<RELATION_ID>",
                      help="Output KML for the OSM relation <RELATION_ID>")
    parser.add_option("--way", dest="way",
                      metavar="<WAY_ID>",
                      help="Output KML for the OSM way <WAY_ID>")

    (options, args) = parser.parse_args()

    if args:
        parser.print_help(file=sys.stderr)
        sys.exit(1)

    # These options are all mutually exclusive:
    exclusive_options = (options.doctest,
                         options.relation,
                         options.way)

    if sum(bool(x) for x in exclusive_options) != 1:
        print >> sys.stderr, "You must specify exactly one of --test, --relation or --way"
        sys.exit(1)

    if options.doctest:
        import doctest
        failure_count, test_count = doctest.testmod()
        sys.exit(0 if failure_count == 0 else 1)

    if options.relation:
        element_type = 'relation'
        element_id = options.relation
    elif options.way:
        element_type = 'way'
        element_id = options.way

    from generate_kml import *

    kml, bbox = get_kml_for_osm_element(element_type, element_id)

    if kml:
        print kml
        sys.exit(0)
    else:
        sys.exit(1)
