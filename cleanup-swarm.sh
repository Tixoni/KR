#!/bin/bash

# cleanup-swarm.sh - Complete cleanup script for Tourism Platform
set -e  # Exit on any error

# Configuration
STACK_NAME="tourism-platform"
LOG_FILE="cleanup.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "🧹 Starting Tourism Platform cleanup at $TIMESTAMP..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
    echo "[$TIMESTAMP] [INFO] $1" >> "$LOG_FILE"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
    echo "[$TIMESTAMP] [WARN] $1" >> "$LOG_FILE"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    echo "[$TIMESTAMP] [ERROR] $1" >> "$LOG_FILE"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
    echo "[$TIMESTAMP] [INFO] $1" >> "$LOG_FILE"
}

# Function to check if stack exists
stack_exists() {
    docker stack ls --format "{{.Name}}" | grep -q "^$STACK_NAME$"
}

# Function to force cleanup
force_cleanup() {
    print_warning "Force cleanup mode enabled"
    
    # Force remove all containers
    print_status "Force removing containers..."
    docker container prune -f
    
    # Force remove all services
    print_status "Force removing services..."
    docker service ls --format "{{.Name}}" | grep "$STACK_NAME" | xargs -r docker service rm
    
    # Force remove all networks
    print_status "Force removing networks..."
    docker network ls --format "{{.Name}}" | grep "$STACK_NAME" | xargs -r docker network rm
    
    # Force remove all volumes
    print_status "Force removing volumes..."
    docker volume ls --format "{{.Name}}" | grep "$STACK_NAME" | xargs -r docker volume rm
}

# Main cleanup function
main() {
    # Initialize log file
    echo "=== Tourism Platform Cleanup Log ===" > "$LOG_FILE"
    echo "Started at: $TIMESTAMP" >> "$LOG_FILE"
    
    # Check if stack exists
    if ! stack_exists; then
        print_warning "Stack '$STACK_NAME' does not exist"
        exit 0
    fi
    
    print_status "Found stack '$STACK_NAME', proceeding with cleanup..."
    
    # 1. Remove stack
    print_status "Removing stack '$STACK_NAME'..."
    if docker stack rm "$STACK_NAME"; then
        print_status "Stack removal initiated ✅"
    else
        print_error "Failed to remove stack!"
        exit 1
    fi
    
    # 2. Wait for services to stop
    print_status "Waiting for services to stop..."
    local max_wait=60
    local wait_time=0
    
    while [ $wait_time -lt $max_wait ]; do
        if ! stack_exists; then
            print_status "Stack removed successfully ✅"
            break
        fi
        
        print_info "Waiting for stack removal... ($wait_time/$max_wait seconds)"
        sleep 5
        wait_time=$((wait_time + 5))
    done
    
    if stack_exists; then
        print_warning "Stack still exists after $max_wait seconds, forcing cleanup..."
        force_cleanup
    fi
    
    # 3. Remove volumes
    print_status "Removing volumes..."
    docker volume rm "${STACK_NAME}_postgres_data" 2>/dev/null || print_warning "Volume already removed"
    
    # 4. Remove networks (if no other services using them)
    print_status "Removing networks..."
    docker network rm "${STACK_NAME}_tourism_network" 2>/dev/null || print_warning "Network already removed"
    
    # 5. Remove unused images
    print_status "Removing unused images..."
    docker image prune -f
    
    # 6. Remove unused volumes
    print_status "Removing unused volumes..."
    docker volume prune -f
    
    # 7. Remove unused networks
    print_status "Removing unused networks..."
    docker network prune -f
    
    echo ""
    print_status "✅ Cleanup completed!"
    echo "Log file: $LOG_FILE"
    
    # Show final status
    echo ""
    print_info "Final status:"
    docker stack ls
    docker service ls
    docker volume ls
    docker network ls
}

# Parse command line arguments
FORCE_CLEANUP=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --force)
            FORCE_CLEANUP=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [--force]"
            echo "  --force    Force cleanup even if stack doesn't exist"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Run main function
main "$@"