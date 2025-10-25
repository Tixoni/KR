#!/bin/bash

# start-swarm.sh - Quick start script for Tourism Platform
set -e  # Exit on any error

# Configuration
STACK_NAME="tourism-platform"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "🚀 Quick Start Tourism Platform at $TIMESTAMP..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Function to check if stack exists
stack_exists() {
    docker stack ls --format "{{.Name}}" | grep -q "^$STACK_NAME$"
}

# Main start function
main() {
    # Check if stack already exists
    if stack_exists; then
        print_warning "Stack '$STACK_NAME' already exists!"
        print_info "Use './check-status.sh' to check status or './cleanup-swarm.sh' to remove first"
        exit 1
    fi
    
    # Check if Docker Swarm is initialized
    if ! docker node ls &> /dev/null; then
        print_status "Initializing Docker Swarm..."
        docker swarm init
    else
        print_status "Docker Swarm already initialized"
    fi
    
    # Create network if it doesn't exist
    if ! docker network ls | grep -q tourism_network; then
        print_status "Creating overlay network..."
        docker network create --driver overlay tourism_network
    else
        print_status "Network 'tourism_network' already exists"
    fi
    
    # Deploy stack
    print_status "Deploying stack '$STACK_NAME'..."
    docker stack deploy -c docker-stack.yml "$STACK_NAME"
    
    # Wait for services to start
    print_status "Waiting for services to start..."
    sleep 30
    
    # Show status
    print_status "Stack deployed! Checking status..."
    docker service ls --filter name="$STACK_NAME"
    
    echo ""
    print_status "🎉 Tourism Platform started!"
    echo ""
    print_info "🌐 Access URLs:"
    echo "  Frontend:     http://localhost:8080"
    echo "  Auth API:     http://localhost:8000"
    echo "  Tours API:    http://localhost:8001"
    echo "  Booking API:  http://localhost:8002"
    echo ""
    print_info "📋 Next steps:"
    echo "  Check status: ./check-status.sh"
    echo "  View logs:    docker service logs ${STACK_NAME}_auth-service"
    echo "  Stop platform: ./stop-swarm.sh"
}

# Run main function
main "$@"
