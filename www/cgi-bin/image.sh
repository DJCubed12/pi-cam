#!/bin/bash

echo "Content-type: text/html"
echo ""

libcamera-still -o "/var/www/html/snapshot.jpg"

echo "Image saved as snapshot.jpg"
