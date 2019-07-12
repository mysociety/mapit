import doctest
import mapit.management.command_utils


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(mapit.management.command_utils))
    return tests
