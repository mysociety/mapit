def sorted_areas(areas):
    return areas.order_by('type__code', 'name')
