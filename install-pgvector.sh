"""
Install script for pgvector extension in PostgreSQL Docker container
"""

#!/bin/bash

set -e

# Get the Docker container ID
CONTAINER_ID=${1:-$(docker ps -qf "name=postgres")}

if [ -z "$CONTAINER_ID" ]; then
    echo "Error: No container ID provided and no container with 'postgres' in name found."
    echo "Usage: $0 [container_id]"
    exit 1
fi

echo "Installing pgvector in container $CONTAINER_ID"

# Check if Docker container is running
if ! docker ps -q --filter "id=$CONTAINER_ID" | grep -q .; then
    echo "Error: Container $CONTAINER_ID is not running"
    exit 1
fi

# Install build dependencies
docker exec -it $CONTAINER_ID apt-get update
docker exec -it $CONTAINER_ID apt-get install -y build-essential git postgresql-server-dev-all

# Clone and install pgvector
docker exec -it $CONTAINER_ID bash -c "cd /tmp && git clone --branch v0.4.4 https://github.com/pgvector/pgvector.git"
docker exec -it $CONTAINER_ID bash -c "cd /tmp/pgvector && make && make install"

# Create extension in database
echo "Creating pgvector extension in database"
docker exec -it $CONTAINER_ID psql -U postgres -c "CREATE EXTENSION IF NOT EXISTS vector;"

echo "Testing pgvector installation"
docker exec -it $CONTAINER_ID psql -U postgres -c "CREATE TABLE IF NOT EXISTS vector_test (id serial primary key, embedding vector(3));"
docker exec -it $CONTAINER_ID psql -U postgres -c "INSERT INTO vector_test (embedding) VALUES ('[1,2,3]');"
docker exec -it $CONTAINER_ID psql -U postgres -c "SELECT * FROM vector_test;"
docker exec -it $CONTAINER_ID psql -U postgres -c "DROP TABLE vector_test;"

echo "pgvector installation complete"
