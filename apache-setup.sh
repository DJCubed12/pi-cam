#!/bin/bash

# Remove old html files, copy in new ones
if [ -d /var/www/html ]; then
  rm -r /var/www/html
fi
cp -r www/html /var/www
chmod -R u=rwX,go=rX /var/www

# Remove old cgi-bin files, copy in new ones
if [ -d /usr/lib/cgi-bin ]; then
  rm -r /usr/lib/cgi-bin
fi
cp -r www/cgi-bin /usr/lib
chmod -R u=rwx,go=rx /usr/lib/cgi-bin

# Allow CGI scripts to generate files and store them here:
mkdir /usr/lib/cgi-bin/generated
chown www-data /usr/lib/cgi-bin/generated

systemctl start apache2
