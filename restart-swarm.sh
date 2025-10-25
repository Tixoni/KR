#!/bin/bash

# restart-swarm.sh - Quick restart script for Tourism Platform
set -e  # Exit on any error

# Configuration
STACK_NAME="tourism-platform"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "🔄 Restarting Tourism Platform at $TIMESTAMP..."

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

# Main restart function
main() {
    # Check if stack exists
    if ! stack_exists; then
        print_warning "Stack '$STACK_NAME' does not exist!"
        print_info "Use './start-swarm.sh' to start the platform"
        exit 1
    fi
    
    print_status "Found stack '$STACK_NAME', restarting..."
    
    # Stop stack
    print_status "Stopping stack '$STACK_NAME'..."
    docker stack rm "$STACK_NAME"
    
    # Wait for services to stop
    print_status "Waiting for services to stop..."
    sleep 15
    
    # Start stack
    print_status "Starting stack '$STACK_NAME'..."
    docker stack deploy -c docker-stack.yml "$STACK_NAME"
    
    # Wait for services to start
    print_status "Waiting for services to start..."
    sleep 30
    
    # Show status
    print_status "Stack restarted! Checking status..."
    docker service ls --filter name="$STACK_NAME"
    
    echo ""
    print_status "🔄 Tourism Platform restarted!"
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
}

# Run main function
main "$@"
