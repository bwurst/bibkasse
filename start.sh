#!/bin/bash

touchscreen="$(xrandr |grep 'connected primary.* 1920x1080'|cut -d ' ' -f 1)"
secondscreen="$(xrandr |grep 'HDMI-. connected 1920x1080'|cut -d ' ' -f 1)"

echo "Primary: ${touchscreen}"
echo "Secondary: ${secondscreen}"

if [[ -n "${secondscreen}" && -n "${touchscreen}" ]] ; then
  xrandr --output "${touchscreen}" --primary
  xrandr --output "${secondscreen}" --right-of "${touchscreen}"
  xrandr --output "${secondscreen}" --rotate inverted
fi

touchdev="$(xinput --list|grep Touch|sed -e 's:^.*id=\([0-9]*\).*$:\1:')"
xinput --map-to-output "${touchdev}" "${touchscreen}"

xset -dpms
xset s off

cd "$(dirname ${0})"
exec ./bib
