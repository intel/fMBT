# pull official base image
FROM debian:latest

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DEBIAN_FRONTEND=noninteractive

# tzdata hack
RUN ln -fs /usr/share/zoneinfo/Europe/Rome /etc/localtime

# update system
RUN apt-get update && apt-get dist-upgrade -y
RUN apt-get install git build-essential libglib2.0-dev libboost-regex-dev libedit-dev libmagickcore-dev \
 	python-dev python-pexpect python-dbus python-gobject gawk libtool autoconf automake debhelper \
 	libboost-dev flex libpng16-16 libxml2-dev graphviz imagemagick gnuplot python-pyside* tesseract-ocr --yes

# build project
WORKDIR /opt
RUN git clone --branch v0.42 --single-branch --depth 1 https://github.com/intel/fMBT
WORKDIR /opt/fMBT
RUN ./autogen.sh; ./configure; make; make install 

