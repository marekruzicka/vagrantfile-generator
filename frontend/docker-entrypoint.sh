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
