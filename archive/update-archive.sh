#! /usr/bin/env bash

rm -R c
wget --no-verbose --directory-prefix=c --no-host-directories --convert-links --page-requisites --recursive http://fractal.linuxd.org:6543/
rm archive.zip
zip --recurse-paths archive.zip c
cat archive.zip | uuencode archive.zip | mail -s "Archive update" hailebop@gmail.com

echo "MAIL SENT!"
