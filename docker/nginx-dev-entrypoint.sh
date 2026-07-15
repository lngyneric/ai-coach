#!/bin/sh
envsubst '${OPENCODE_API_KEY}' < /etc/nginx/nginx.conf > /tmp/nginx.conf
cp /tmp/nginx.conf /etc/nginx/nginx.conf
exec nginx -g 'daemon off;'
