#!/bin/bash

echo "Content-type: text/html"
echo ""

echo "<p>Folder: $(pwd)</p>"

libcamera-still -o "generated/temp.jpg"

echo "<p>Contents:</p>"
echo "<p>$(ls)</p>"

echo ""

# rm generated/temp.jpg

exit 0
