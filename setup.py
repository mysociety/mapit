from distutils.core import setup
import os

file_dir = os.path.dirname(__file__)
if file_dir: os.chdir(file_dir)

packages = []
for dirpath, dirnames, filenames in os.walk('mapit'):
    if '__init__.py' in filenames:
        packages.append(dirpath.replace('/', '.'))

setup(
    name='django-mapit',
    version='1.0.0pr2',
    description='A web service for mapping postcodes and points to current or past administrative area information and polygons.',
    long_description=open('README').read(), # TODO: Put this into ReST format
    author='mySociety',
    author_email='mapit@mysociety.org',
    url='https://github.com/mysociety/mapit',
    license='LICENSE.txt',

    # TODO: Use find_packages from setuptools
    packages=packages,

    # TODO: Use include_package_data=True from setuptools
    package_data={
        'mapit': [
            'templates/mapit/*.html',
            'templates/*/mapit/*.html',
            'static/mapit/*',
            'fixtures/*.json',
            'sql/*.sql',
    ] },

    # TODO: This does nothing, apparently - needs to be install_requires and using setuptools
    requires=[ 'memcache', 'gdal', 'django', 'yaml', 'psycopg2', 'south' ],

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Framework :: Django',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Topic :: Database :: Front-Ends',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Scientific/Engineering :: GIS',
    ],

    zip_safe=False, # So that easy_install doesn't make an egg
)
