#!/bin/bash

# stop-swarm.sh - Quick stop script for Tourism Platform
set -e  # Exit on any error

# Configuration
STACK_NAME="tourism-platform"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "🛑 Stopping Tourism Platform at $TIMESTAMP..."

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

# Main stop function
main() {
    # Check if stack exists
    if ! stack_exists; then
        print_warning "Stack '$STACK_NAME' does not exist!"
        exit 0
    fi
    
    print_status "Found stack '$STACK_NAME', stopping..."
    
    # Remove stack
    print_status "Removing stack '$STACK_NAME'..."
    docker stack rm "$STACK_NAME"
    
    # Wait for services to stop
    print_status "Waiting for services to stop..."
    local max_wait=60
    local wait_time=0
    
    while [ $wait_time -lt $max_wait ]; do
        if ! stack_exists; then
            print_status "Stack stopped successfully ✅"
            break
        fi
        
        print_info "Waiting for stack to stop... ($wait_time/$max_wait seconds)"
        sleep 5
        wait_time=$((wait_time + 5))
    done
    
    if stack_exists; then
        print_warning "Stack still exists after $max_wait seconds"
        print_info "Use './cleanup-swarm.sh --force' for force cleanup"
    fi
    
    echo ""
    print_status "🛑 Tourism Platform stopped!"
    echo ""
    print_info "📋 Next steps:"
    echo "  Start again:   ./start-swarm.sh"
    echo "  Full cleanup: ./cleanup-swarm.sh"
    echo "  Check status: ./check-status.sh"
}

# Run main function
main "$@"
