# coding=utf8

import os
import re
import urllib

from django.core.management.base import BaseCommand
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.db.models import Union
from django.db.models import Q
from mapit.models import Area, Generation, Type, Country, NameType, CodeType


def legis_row(id):
    fn = id.replace('/', '-')
    try:
        r = open('cache/' + fn).read()
    except IOError:
        r = urllib.urlopen('https://www.legislation.gov.uk/uksi/' + id).read()
        try:
            fp = open('cache/' + fn, 'w')
            fp.write(r)
            fp.close()
        except IOError:
            pass
    for row in re.findall('<td[^>]*>(.*?)</td><td[^>]*>(.*?)</td><td[^>]*>.*?</td>', r):
        new, curr = row
        if '<p' in curr:
            curr = re.findall('<p[^>]*>(.*?)&#xD;', curr)
        else:
            curr = [curr]
        out = []
        for name in curr:
            name = name.replace('Bishops', "Bishop's")  # SW&T
            name = re.sub(' the (?!parish)', ' The ', name)  # WS, ignore Dorset
            name = name.replace('Marys', "Mary's")  # WS
            name = name.replace('Margarets', "Margaret's")  # ES
            name = name.replace(' (Bournemouth)', '').replace('Queens', "Queen's")  # BCP
            name = name.replace('Kingston', 'Kington')  # Dorset typo
            name = name.replace(' &amp; ', ' & ')
            out.append(name)
        new = new.replace(' &amp; ', ' & ')
        yield new, out


class Command(BaseCommand):
    help = "Sort out boundaries for 2019 council changes"

    def add_arguments(self, parser):
        parser.add_argument('--commit', action='store_true')

    def handle(self, *args, **options):
        self.commit = options['commit']
        self.g = Generation.objects.current()
        self.gn = Generation.objects.new()
        self.name_type = NameType.objects.get(code='S')
        self.code_type = CodeType.objects.get(code='gss')
        self.country = Country.objects.get(code='E')

        self.raise_generation_on_everything_else()

        self.areas = Area.objects.filter(generation_low_id__lte=self.g, generation_high_id__gte=self.g)

        self.get_existing()
        self.somerset_west_and_taunton()
        self.west_suffolk()
        self.east_suffolk()
        self.bcp()
        self.dorset_council()

    def _exclude_councils_and_wards(self, qs, names, type_p, type_c):
        areas = Area.objects.filter(type__code=type_p, name__in=names, generation_high=self.g)
        wards = Area.objects.filter(type__code=type_c, parent_area__in=areas, generation_high=self.g)
        qs = qs.exclude(id__in=areas).exclude(id__in=wards)
        return qs

    def raise_generation_on_everything_else(self):
        qs = Area.objects.filter(generation_high=self.g)
        print('%d areas in database' % qs.count())
        qs = self._exclude_councils_and_wards(
            qs, ('West Somerset District Council', 'Taunton Deane Borough Council'), 'DIS', 'DIW')
        qs = self._exclude_councils_and_wards(
            qs, ('Forest Heath District Council', "St Edmundsbury Borough Council"), 'DIS', 'DIW')
        qs = self._exclude_councils_and_wards(
            qs, ('Suffolk Coastal District Council', "Waveney District Council"), 'DIS', 'DIW')
        qs = self._exclude_councils_and_wards(qs, ('Dorset County Council',), 'CTY', 'CED')
        qs = self._exclude_councils_and_wards(
            qs, ('Bournemouth Borough Council', "Poole Borough Council"), 'UTA', 'UTW')
        qs = self._exclude_councils_and_wards(
            qs, ('Christchurch Borough Council', 'East Dorset District Council', 'North Dorset District Council',
                 'Purbeck District Council', 'West Dorset District Council', 'Weymouth and Portland Borough Council'),
            'DIS', 'DIW')

        if self.commit:
            print('Raising gen high on %d areas' % qs.count())
            updated = qs.update(generation_high=self.gn)
            print('Raised gen high on %d areas' % updated)
        else:
            print('Would raise gen high on %d areas' % qs.count())

    def get_existing(self):
        self.somerset = Area.objects.get(type__code='CTY', name='Somerset County Council')
        self.suffolk = Area.objects.get(type__code='CTY', name='Suffolk County Council')
        self.dorset = Area.objects.get(type__code='CTY', name='Dorset County Council')

    def _create(self, name, typ, geom, gss=None):
        m = Area(
            name=name, type=Type.objects.get(code=typ), country=self.country,
            generation_low=self.gn, generation_high=self.gn,
        )
        if self.commit:
            m.save()
            m.names.update_or_create(type=self.name_type, defaults={'name': name})
            if gss:
                m.codes.update_or_create(type=self.code_type, defaults={'code': gss})
            m.polygons.create(polygon=geom)
        else:
            print('Would create', name, typ)

    def somerset_west_and_taunton(self):
        """New Somerset West and Taunton areas are existing county electoral divisions"""
        districts = Area.objects.filter(
            type__code='DIS', name__in=('West Somerset District Council', 'Taunton Deane Borough Council'))
        self._create('Somerset West and Taunton Council', 'UTA', self._union(districts), 'E07000246')
        for new, curr in legis_row('2018/649/schedule/made'):
            out = self.areas.filter(name__in=curr, type__code='CED', parent_area=self.somerset)
            self._create(new, 'UTW', self._union(out))

    def west_suffolk(self):
        """New West Suffolk areas are groups of existing district wards"""
        districts = Area.objects.filter(
            type__code='DIS', name__in=('Forest Heath District Council', "St Edmundsbury Borough Council"))
        self._create('West Suffolk Council', 'UTA', self._union(districts), 'E07000245')
        for new, curr in legis_row('2018/639/schedule/made'):
            out = self.areas.filter(name__in=curr, type__code='DIW', parent_area__in=districts)
            self._create(new, 'UTW', self._union(out))

    def east_suffolk(self):
        """New East Suffolk areas might be existing wards or electoral
        divisions, given per row in brackets. Note there is a gap in this SI in
        Felixstowe, the part of Felixstowe Coastal ED that is not in S, E, W."""
        districts = Area.objects.filter(
            type__code='DIS', name__in=('Suffolk Coastal District Council', "Waveney District Council"))
        self._create('East Suffolk Council', 'UTA', self._union(districts), 'E07000244')
        for new, curr in legis_row('2018/640/schedule/made'):
            qs = Q()
            for name in curr:
                # Ward or ED is in the name
                name, typ = re.match(r'^(.*?) \((ED|W)\)$', name).groups()
                gen = self.g
                if name == "Rushmere St Andrew":  # Must be old boundary to make sense
                    gen = Generation.objects.get(id=23)
                    qsn = Q(name=name, generation_low_id__lte=gen, generation_high_id__gte=gen,
                            type__code='DIW', parent_area__in=districts)
                elif typ == 'ED':
                    qsn = Q(name=name, type__code='CED', parent_area=self.suffolk,
                            generation_low_id__lte=gen, generation_high_id__gte=gen)
                elif typ == 'W':
                    qsn = Q(name=name, type__code='DIW', parent_area__in=districts,
                            generation_low_id__lte=gen, generation_high_id__gte=gen)
                qs |= qsn
            out = self._union(Area.objects.filter(qs))
            self._create(new, 'UTW', out)

    def bcp(self):
        """New BCP areas might be existing ward(s) or an electoral
        division, given per row as text."""
        districts = Area.objects.filter(
            Q(type__code='UTA', name='Bournemouth Borough Council')
            | Q(type__code='DIS', name="Christchurch Borough Council")
            | Q(type__code='UTA', name="Poole Borough Council"))
        self._create('Bournemouth, Christchurch and Poole Council', 'UTA', self._union(districts), 'E06000058')
        for new, curr in legis_row('2018/648/schedule/1/made'):
            line = curr[0]  # Only ever one row here
            typ, multi, line = re.match('^The existing (borough ward(s?)|county division) of (.*?)$', line).groups()
            curr = line.split(' and ') if multi else [line]  # Never more than two
            qs = Q()
            for name in curr:
                names = [name, name.replace(' & ', ' and ')] if ' & ' in name else [name]
                if typ == 'county division':
                    qs |= Q(name__in=names, type__code='CED', parent_area=self.dorset)
                else:
                    qs |= Q(name__in=names, type__code='UTW', parent_area__in=districts)
            out = self._union(self.areas.filter(qs))
            self._create(new, 'UTW', out)

    def dorset_council(self):
        """This is the complex one"""
        self.districts = Area.objects.filter(type__code='DIS', name__in=(
            'East Dorset District Council',
            'North Dorset District Council',
            'Purbeck District Council',
            'West Dorset District Council',
            'Weymouth and Portland Borough Council',
        ))
        new_dorset = self._union(self.districts)
        self._create('Dorset Council', 'UTA', new_dorset, 'E06000059')
        for new, curr in legis_row('2018/648/schedule/2/made'):
            qs = Q()
            constructed = []
            for line in curr:
                m = re.match('''(?x)
                    ^The [ ] (?:whole[ ]of[ ]the[ ])?
                    ( parish(?:es)? | parish[ ]wards? | existing[ ]county[ ]division )
                    [ ] of [ ] (.*?)$''', line)
                typ = m.group(1)
                names = m.group(2)
                if typ == 'existing county division':
                    qs |= Q(name=names, type__code='CED', parent_area=self.dorset)
                elif typ == 'parish' or typ == 'parishes':
                    names = names.split(', ')
                    names[-1:] = names[-1].split(' and ')
                    qs |= Q(name__in=names, type__code='CPC', parent_area__in=self.districts)
                # Parish wards have to be constructed out of other things
                elif typ == 'parish ward':
                    if names == '‘Three Cross’ of the parish of Verwood':
                        constructed.append(self.three_cross())
                    elif names == '‘St Leonards and St Ives South’ of the parish of St Leonards and St Ives':
                        constructed.append(self.read_manual('st-leonards-south'))
                    elif names == '‘Stephens Castle’ of the parish of Verwood':
                        qs |= Q(name='Verwood East', type__code='DIW', parent_area__in=self.districts)
                elif typ == 'parish wards':
                    if names == ('‘St Leonards and St Ives East’ and ‘St Leonards and St Ives West’'
                                 ' of the parish of St Leonards and St Ives'):
                        constructed.append(self.read_manual('st-leonards-east-west'))
                    elif names == ('‘Ameysford’, ‘Ferndown Central North’ and ‘Ferndown Links’'
                                   ' of the parish of Ferndown'):
                        constructed.append(self.read_manual('ferndown-north'))
                    elif names == '‘Ferndown Central’ and ‘Ferndown Links South’ of the parish of Ferndown':
                        constructed.append(self.read_manual('ferndown-south'))
                    elif names == '‘Dorchester East’ and ‘Dorchester South’ of the parish of Dorchester':
                        qs |= Q(name__in=('Dorchester East', 'Dorchester South'),
                                type__code='DIW', parent_area__in=self.districts)
                    elif names == '‘Dorchester West’ and ‘Dorchester North’ of the parish of Dorchester':
                        qs |= Q(name__in=('Dorchester West', 'Dorchester North'),
                                type__code='DIW', parent_area__in=self.districts)
                    elif names == '‘Symondsbury Pine View’ and ‘Symondsbury West Cliff’ of the parish of Symondsbury':
                        constructed.extend(self.symondsbury())
                    elif names == '‘Milton-on-Stour’, ‘Gillingham Rural’ and ‘Wyke’ of the parish of Gillingham':
                        constructed.append(self.gillingham_ham_or_milton('N'))
                        constructed.append(self.gillingham_rural())
                    elif names == '‘Ham’ and ‘Gillingham Town’ of the parish of Gillingham':
                        qs |= Q(name='Gillingham Town', type__code='DIW', parent_area__in=self.districts)
                        constructed.append(self.gillingham_ham_or_milton('S'))
                    elif names == '‘Dewlands North’ and Dewlands South’ of the parish of Verwood':
                        constructed.append(self.dewlands())
            if len(qs) and constructed:
                out = self._union(self.areas.filter(qs))
                for g in constructed:
                    out = out.union(g)
            elif constructed:
                out = constructed[0]
                for g in constructed[1:]:
                    out = out.union(g)
            elif len(qs):
                out = self._union(self.areas.filter(qs))
            else:
                raise Exception
            self._create(new, 'UTW', out)

    def gillingham_ham_or_milton(self, north_or_south):
        polygons = self._intersect(
            {'name': 'Gillingham', 'type__code': 'CPC', 'parent_area__in': self.districts},
            {'name': 'Motcombe & Bourton', 'type__code': 'DIW', 'parent_area__in': self.districts})
        polygons.sort(key=lambda x: x.extent[1])  # min_y
        if north_or_south == 'N':
            return polygons[1]
        else:
            return polygons[0]

    def gillingham_rural(self):
        return self._intersect(
            {'name': 'Gillingham Rural', 'type__code': 'DIW', 'parent_area__in': self.districts},
            {'name': 'Gillingham', 'type__code': 'CPC', 'parent_area__in': self.districts})

    def symondsbury(self):
        return self._intersect(
            {'name': 'Bridport South', 'type__code': 'DIW', 'parent_area__in': self.districts},
            {'name': 'Symondsbury', 'type__code': 'CPC', 'parent_area__in': self.districts})

    def three_cross(self):
        verwood_cpc = self.areas.get(name='Verwood', type__code='CPC', parent_area__in=self.districts)
        verwood_ced = self.areas.get(name='Verwood', type__code='CED', parent_area=self.dorset)
        verwood_ced_area = verwood_ced.polygons.all()[0].polygon
        verwood_cpc_area = verwood_cpc.polygons.all()[0].polygon
        return verwood_cpc_area.difference(verwood_ced_area)

    def dewlands(self):
        intersect = self._intersect(
            {'name': 'Verwood', 'type__code': 'CPC', 'parent_area__in': self.districts},
            {'name': 'Verwood', 'type__code': 'CED', 'parent_area': self.dorset})
        verwood_east = self.areas.get(name='Verwood East', type__code='DIW', parent_area__in=self.districts)
        verwood_area = verwood_east.polygons.all()[0].polygon
        return intersect.difference(verwood_area)

    # Only works for areas with one polygon
    def _intersect(self, a1, a2):
        a1 = self.areas.get(**a1).polygons.all()[0].polygon
        a2 = self.areas.get(**a2).polygons.all()[0].polygon
        intersect = a1.intersection(a2)
        if intersect.geom_type == 'GeometryCollection':
            intersect = [a for a in intersect if a.geom_type != 'LineString']
            if len(intersect) == 1:
                intersect = intersect[0]
        return intersect

    def _union(self, qs):
        qs = qs.aggregate(Union('polygons__polygon'))
        area = qs['polygons__polygon__union']
        return area

    def read_manual(self, fn):
        dir = os.path.dirname(__file__) + '/../..'
        fp = open('%s/data/2019-%s.geojson' % (dir, fn))
        p = GEOSGeometry(fp.read(), srid=4326)
        p.transform(27700)
        return p
