#!/bin/sh
set -eu

CONFIG_PATH=${CONFIG_PATH:-/usr/share/nginx/html/config.json}
API_URL=${FRONTEND_API_URL:-/api}

# Handle compose implementations that pass the literal default expression
case "$API_URL" in
  *'${'* )
  API_URL="/api"
    ;;
esac

# Escape backslashes and double quotes for JSON output
escaped_api_url=$(printf '%s' "$API_URL" | sed 's/\\/\\\\/g; s/"/\\"/g')

cat <<EOF >"$CONFIG_PATH"
{
  "API_URL": "$escaped_api_url"
}
EOF

echo "Wrote runtime config to $CONFIG_PATH (API_URL=$API_URL)"

# Extract FQDN/hostname from FE_LISTEN_URL (assumes format scheme://host:port)
FE_LISTEN_URL=${FE_LISTEN_URL:-}
if [ -n "$FE_LISTEN_URL" ]; then
  FE_HOSTNAME=${FE_LISTEN_URL#*://}    # strip scheme
  FE_HOSTNAME=${FE_HOSTNAME%%:*}      # strip port
else
  FE_HOSTNAME=""
fi
 
# Build list of allowed server names (front-end host plus optional extras)
FE_EXTRA_SERVER_NAMES="localhost 127.0.0.1"
SERVER_NAMES=""
if [ -n "$FE_HOSTNAME" ]; then
  SERVER_NAMES="$FE_HOSTNAME $FE_EXTRA_SERVER_NAMES"
else
  SERVER_NAMES=$FE_EXTRA_SERVER_NAMES
fi

SERVER_CONF=${SERVER_CONF:-/etc/nginx/conf.d/default.conf}
if grep -q "__SERVER_NAME_PLACEHOLDER__" "$SERVER_CONF"; then
  escaped_server_names=$(printf '%s' "$SERVER_NAMES" | sed 's/[&/]/\\&/g')
  sed -i "0,/__SERVER_NAME_PLACEHOLDER__/s//${escaped_server_names}/" "$SERVER_CONF"
  echo "Configured nginx server_name to: $SERVER_NAMES"
else
  echo "Warning: server name placeholder not found in $SERVER_CONF" >&2
fi