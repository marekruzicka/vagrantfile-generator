#!/bin/sh
set -e

# Seed shared data from the bundled seed-data directory
# This runs on every container start but only copies if destination is empty

SEED_DIR="/app/seed-data/shared"
DATA_DIR="/app/data/shared"

# List of resource types to seed
RESOURCE_TYPES="boxes plugins provisioners triggers"

for resource_type in $RESOURCE_TYPES; do
    src_dir="$SEED_DIR/$resource_type"
    dst_dir="$DATA_DIR/$resource_type"
    
    # Create destination directory if it doesn't exist
    mkdir -p "$dst_dir"
    
    # Only seed if source exists and destination is empty
    if [ -d "$src_dir" ] && [ -n "$(ls -A "$src_dir" 2>/dev/null)" ]; then
        if [ -z "$(ls -A "$dst_dir" 2>/dev/null)" ]; then
            echo "Seeding shared $resource_type from $src_dir to $dst_dir"
            cp -r "$src_dir"/* "$dst_dir"/
        else
            echo "Shared $resource_type already exists, skipping seed"
        fi
    fi
done

# Ensure other required directories exist
mkdir -p /app/data/users
mkdir -p /app/data/auth

echo "Data initialization complete"

# Execute the main command
exec "$@"
