# OutputFormatter
# class for merging kml/geojson output

from django.utils.html import escape


class OutputFormatter:

    def __init__(self):
        self.kml_header =\
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
        self.kml_placemark =\
"""
        <Placemark>
            <styleUrl>#ourPolygonStyle</styleUrl>
            <name>%s</name>
            %s
        </Placemark>"""
        self.kml_footer =\
"""
    </Document>
</kml>"""


    # [(kml, name)] -> kml
    def merge_kml(self, kml_arr, line_colour="70ff0000", fill_colour="3dff5500"):
        output = self.kml_header % (line_colour, fill_colour)
        for kml in kml_arr:
            output += self.kml_placemark % (escape(kml[1]), kml[0])
        output += self.kml_footer
        return output

    # [(geojson, name)] -> geojson
    def merge_geojson(self, geojson_arr):
        output = '{ "type": "FeatureCollection", "features": ['
        for geojson in geojson_arr:
            output += '{ "properties": { "name": "%s" }, "type": "Feature", "geometry": %s },'\
                % (escape(geojson[1]), geojson[0])
        output = output[:-1]
        output += "] }"
        return output
