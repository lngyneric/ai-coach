#!/bin/sh
# entrypoint for nginx: substitute env vars in nginx configs before starting
export ARK_API_KEY="${ARK_API_KEY:-}"
export OPENCODE_API_KEY="${OPENCODE_API_KEY:-${OPENAI_API_KEY:-}}"
envsubst '${ARK_API_KEY} ${OPENCODE_API_KEY}' < /etc/nginx/nginx.conf > /tmp/nginx.conf && \
  cp /tmp/nginx.conf /etc/nginx/nginx.conf && \
  envsubst '${OPENCODE_API_KEY}' < /etc/nginx/conf.d/default.conf > /tmp/default.conf && \
  cp /tmp/default.conf /etc/nginx/conf.d/default.conf && \
  exec nginx -g 'daemon off;'
