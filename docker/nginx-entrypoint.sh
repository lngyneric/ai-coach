#!/bin/sh
# entrypoint for nginx: substitute ${ARK_API_KEY} in nginx.conf before starting
export ARK_API_KEY="${ARK_API_KEY:-}"
envsubst '${ARK_API_KEY}' < /etc/nginx/nginx.conf > /tmp/nginx.conf && \
  mv /tmp/nginx.conf /etc/nginx/nginx.conf && \
  exec nginx -g 'daemon off;'
