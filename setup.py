from setuptools import setup, find_packages
import os

file_dir = os.path.abspath(os.path.dirname(__file__))


def read_file(filename):
    filepath = os.path.join(file_dir, filename)
    return open(filepath).read()


setup(
    name='django-mapit',
    version='1.3',
    description=(
        'A web service for mapping postcodes and points to current or past '
        'administrative area information and polygons.'),
    long_description=read_file('README.rst'),
    author='mySociety',
    author_email='mapit@mysociety.org',
    url='https://github.com/mysociety/mapit',
    license='LICENSE.txt',
    packages=find_packages(exclude=['project']),
    scripts=['bin/mapit_make_css'],
    include_package_data=True,
    install_requires=[
        'Django >= 1.4.18',
        'South == 1.0.2',
        'psycopg2',
        'PyYAML',
        'Shapely',
    ],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Database :: Front-Ends',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Scientific/Engineering :: GIS',
    ],

    zip_safe=False,  # So that easy_install doesn't make an egg
)
