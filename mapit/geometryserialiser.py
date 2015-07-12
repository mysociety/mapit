import json

from django.conf import settings
from django.contrib.gis.gdal import OGRException, SRSException
from django.utils.html import escape


class TransformError(Exception):
    pass


# serialise a list of Area objects into .kml .geojson format
# .wkt is supported only for a list of length 1
class GeometrySerialiser(object):
    kml_header =\
        """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
    <Document>
        <Style id="ourPolygonStyle">
            <LineStyle>
                <color>%s</color>
                <width>2</width>
            </LineStyle>
            <PolyStyle>
                <color>%s</color>
            </PolyStyle>
        </Style>"""
    kml_placemark =\
        """
        <Placemark>
            <styleUrl>#ourPolygonStyle</styleUrl>
            <name>%s</name>
            %s
        </Placemark>"""
    kml_footer =\
        """
    </Document>
</kml>"""

    def __init__(self, areas, srid, simplify_tolerance):
        # the geojson serialization format needs to know if we're
        # serializer one item, or a list with one item
        if not isinstance(areas, list):
            self.single = True
            areas = [areas]
        else:
            self.single = False

        self.areas = areas
        self.srid = srid
        self.simplify_tolerance = simplify_tolerance

    # collect all polygons that make up an area
    def __collect_polygons(self, area):
        all_polygons = area.polygons.all()
        if len(all_polygons) > 1:
            all_polygons = all_polygons.collect()
        elif len(all_polygons) == 1:
            all_polygons = all_polygons[0].polygon
        else:
            return None
        return all_polygons

    # transform to a different co-ordinate system
    def __transform(self, polygons):
        if self.srid != settings.MAPIT_AREA_SRID:
            try:
                polygons.transform(self.srid)
            except (SRSException, OGRException) as e:
                raise TransformError("Error with transform: %s" % e)
        return polygons

    # apply boundary simplification
    def __simplify(self, polygons, name):
        num_points_before_simplification = polygons.num_points
        if self.simplify_tolerance:
            polygons = polygons.simplify(self.simplify_tolerance)
            if polygons.num_points == 0 and num_points_before_simplification > 0:
                raise TransformError("Simplifying %s with tolerance %f left no boundary at all" % (
                    name, self.simplify_tolerance))
        return polygons

    # apply pre-processing to self.areas before serialisation
    def __process_polygons(self):
        processed_areas = []
        for area in self.areas:
            polygons = self.__collect_polygons(area)
            if polygons:
                polygons = self.__transform(polygons)
                polygons = self.__simplify(polygons, area.name)
                processed_areas.append((polygons, area))
        if len(processed_areas) == 0:
            raise TransformError("No polygons found")
        else:
            return processed_areas

    # output self.areas as kml
    def kml(self, kml_type, line_colour="70ff0000", fill_colour="3dff5500"):
        content_type = 'application/vnd.google-earth.kml+xml'
        processed_areas = self.__process_polygons()

        if kml_type == "full":
            output = self.kml_header % (line_colour, fill_colour)
            for area in processed_areas:
                output += self.kml_placemark % (escape(area[1].name), area[0].kml)
            output += self.kml_footer
            return (output, content_type)
        elif kml_type == "polygon":
            if len(processed_areas) == 1:
                return (processed_areas[0][0].kml, content_type)
            else:
                raise Exception("kml_type: '%s' not supported for multiple areas"
                                % (kml_type,))
        else:
            raise Exception("Unknown kml_type: '%s'" % (kml_type,))

    # output self.areas as geojson
    def geojson(self):
        content_type = 'application/json'
        processed_areas = self.__process_polygons()
        if len(processed_areas) == 1 and self.single:
            return (processed_areas[0][0].json, content_type)
        else:
            output = {
                'type': 'FeatureCollection',
                'features': [
                    self.area_as_geojson_feature(area[1], area[0])
                    for area in processed_areas
                ]
            }
            return (json.dumps(output), content_type)

    def area_as_geojson_feature(self, area, polygons):
        return {
            'type': 'Feature',
            'properties': {'name': area.name},
            'geometry': json.loads(polygons.json),
        }

    # output self.areas as wkt
    def wkt(self):
        content_type = 'text/plain'
        processed_areas = self.__process_polygons()
        if len(processed_areas) == 1:
            return (processed_areas[0][0].wkt, content_type)
        else:
            raise Exception("wkt not supported for multiple areas")
