# This Dockerfile builds fMBT development image.
# fMBT is built and installed on the system with all dependencies.
#
# In order build a production image, consider building fmbt-gui or fmbt-cli:
# see Dockerfile.fmbt-gui and Dockerfile.fmbt-cli.
#
# Usage:
#   1. Build this image:
#      $ docker build . -t fmbt:latest
#   2. Run:
#      $ docker run -it fmbt:latest
#      # fmbt --version

FROM debian:buster AS builder

RUN apt-get update
RUN apt-get install -y \
        git build-essential libglib2.0-dev libboost-regex-dev libedit-dev libmagickcore-dev \
        python-dev python-pexpect python-dbus python-gobject gawk libtool autoconf automake debhelper \
        libboost-dev flex libpng16-16 libxml2-dev graphviz imagemagick
COPY . /usr/src/fmbt
RUN cd /usr/src/fmbt && \
    ./autogen.sh && \
    ./configure && \
    make -j 4 && \
    make install
RUN cd /usr/src/fmbt/utils3 && \
    python3 setup.py install

FROM builder
RUN apt-get update
RUN apt-get install -y \
        python python-pexpect python-dbus python-gobject gawk \
        libpng16-16 libxml2 imagemagick graphviz \
        gnuplot tesseract-ocr \
        python3-distutils \
        python3-pyside2.qtcore \
        python3-pyside2.qtgui \
        python3-pyside2.qtwidgets
CMD ["/bin/bash"]
