FROM python:2.7-stretch
ENV DEBIAN_FRONTEND noninteractive

# Upgrade OS Dependencies
RUN apt-get update && apt-get upgrade -y
# Install Postgresql Client
RUN apt-get install postgresql-client -y

# Upgrade pip + setuptools
RUN pip install -q -U pip setuptools

# Install gunicorn with gevent
RUN pip install -q -U gunicorn[gevent]

# GDAL Installs
RUN apt-get install gdal-bin python-gdal libgdal-dev -y
RUN pip install -q GDAL==2.1.3 --global-option=build_ext --global-option="-I/usr/include/gdal"

# Set env variables used in this Dockerfile
#Django settings
ENV DJANGO_SETTINGS_MODULE=project.settings

# Local directory with project source
ENV APP_SRC=.
# Directory in container for all project files
ENV APP_SRVHOME=/src
# Directory in container for project source files
ENV APP_SRVPROJ=/src/mapit

# Add application source code to SRCDIR
ADD $APP_SRC $APP_SRVPROJ
WORKDIR $APP_SRVPROJ

# Install dependencies
RUN pip install -q -e .

# Server
EXPOSE 8000

COPY ./docker-entrypoint.sh /
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD [ "--name", "mapit", "--reload", "mapit.wsgi:application" ]
