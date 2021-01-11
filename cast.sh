#!/bin/bash
# Small cast script to Ask a Google Hub to show HA
if ! catt -d "Keuken Display" status | grep 'PLAYING'; then
  # mute first to avoid the annoying beeps
  catt -d "Keuken Display" volume 0
  catt -d "Keuken Display" cast_site http://192.168.0.40:8123/lovelace/0
  # and set volume back, although this gives a small beep too
  catt -d "Keuken Display" volume 45
fi