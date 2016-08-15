# As per the comment in the 2011-10 control file, this script is to be run
# one-off after that import in order to get the two old boundaries back in that
# were removed due to a mistake in the 2011-05 Boundary-Line.

from django.core.management.base import LabelCommand
from django.contrib.gis.gdal import DataSource
from django.utils import six

from mapit.models import Area, CodeType
from utils import save_polygons


class Command(LabelCommand):
    help = 'Import OS Boundary-Line'
    args = '<October 2010 Boundary-Line parish and district ward SHP files>'

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument('--commit', action='store_true', dest='commit', help='Actually update the database')

    def handle_label(self, filename, **options):
        code_version = CodeType.objects.get(code='gss')
        for feat in DataSource(filename)[0]:
            name = feat['NAME'].value
            if not isinstance(name, six.text_type):
                name = name.decode('iso-8859-1')
            ons_code = feat['CODE'].value
            if ons_code in ('E04008782', 'E05004419'):
                m = Area.objects.get(codes__type=code_version, codes__code=ons_code)
                if options['commit']:
                    print('Updating %s' % name)
                    save_polygons({ons_code: (m, [feat.geom])})
