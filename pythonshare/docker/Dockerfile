FROM scratch
COPY usr/ /usr/
ENV PYTHONPATH=/usr/lib/python27.zip
ENV PYTHONHOME=/usr
EXPOSE 8089
ENTRYPOINT ["/usr/bin/pythonshare-server", "-d", "--interface=all", "--password=xyz"]
