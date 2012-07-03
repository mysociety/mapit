import re

def sorted_areas(areas):
    return sorted(list(areas), key=lambda a: (a.type.code, a.name))
