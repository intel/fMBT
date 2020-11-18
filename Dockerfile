# This Dockerfile builds an fMBT image from which you can run
# the fMBT test generator and python3 versions of utilities.
#
# Usage:
#   1. Build image:
#      $ docker build . -t fmbt:latest
#   2. Launch fmbt3-editor with X forward:
#      $ docker run -it --network=host -e DISPLAY=$DISPLAY -v ~/.Xauthority:/root/.Xauthority fmbt:latest
#      # fmbt3-editor
#
# Tips:
#   Use and modify test models on the host by adding another volume mount
#   before the image (fmbt:latest) to the docker run command above:
#       -v /path/to/your/models:/models
#   Now you can run tests and edit models in /models inside the container:
#   # fmbt3-editor /models/mymodel.aal

FROM debian:buster

RUN apt-get update
RUN apt-get install -y \
        git build-essential libglib2.0-dev libboost-regex-dev libedit-dev libmagickcore-dev \
 	python-dev python-pexpect python-dbus python-gobject gawk libtool autoconf automake debhelper \
 	libboost-dev flex libpng16-16 libxml2-dev graphviz imagemagick gnuplot tesseract-ocr \
        python3-pyside2.qtcore \
        python3-pyside2.qtgui \
        python3-pyside2.qtwidgets

COPY . /usr/src/fmbt

RUN cd /usr/src/fmbt && \
    ./autogen.sh && \
    ./configure && \
    make -j 4 && \
    make install

RUN cd /usr/src/fmbt/utils3 && \
    python3 setup.py install

CMD ["/bin/bash"]
