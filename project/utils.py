import sys

if sys.version_info[:2] >= (3, 4):
    import importlib

    def find_module(c):
        return importlib.machinery.PathFinder.find_spec(c)  # noqa
elif sys.version_info[:2] >= (3, 1):
    import importlib

    def find_module(c):
        return importlib.machinery.PathFinder.find_module(c)  # noqa
else:
    import imp

    def find_module(c):
        return imp.find_module(c)
