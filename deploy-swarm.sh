#!/bin/bash

# deploy-swarm.sh - Automated deployment script for Tourism Platform
set -e  # Exit on any error

# Configuration
STACK_NAME="tourism-platform"
LOG_FILE="deployment.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "🚀 Starting Tourism Platform deployment at $TIMESTAMP..."

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

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    if ! command_exists docker; then
        print_error "Docker is not installed!"
        exit 1
    fi
    
    if ! command_exists docker-compose; then
        print_error "Docker Compose is not installed!"
        exit 1
    fi
    
    print_status "All prerequisites are met ✅"
}

# Function to wait for service health
wait_for_service_health() {
    local service_name=$1
    local max_attempts=30
    local attempt=1
    
    print_info "Waiting for $service_name to be healthy..."
    
    while [ $attempt -le $max_attempts ]; do
        if docker service ps --format "{{.CurrentState}}" "$STACK_NAME"_"$service_name" | grep -q "Running"; then
            print_status "$service_name is running ✅"
            return 0
        fi
        
        print_info "Attempt $attempt/$max_attempts: $service_name not ready yet..."
        sleep 10
        ((attempt++))
    done
    
    print_error "$service_name failed to start after $max_attempts attempts"
    return 1
}

# Function to check service health
check_service_health() {
    local service_name=$1
    local health_url=$2
    
    if [ -n "$health_url" ]; then
        print_info "Checking health endpoint for $service_name..."
        if curl -f -s "$health_url" > /dev/null 2>&1; then
            print_status "$service_name health check passed ✅"
            return 0
        else
            print_warning "$service_name health check failed"
            return 1
        fi
    fi
}

# Main deployment function
main() {
    # Initialize log file
    echo "=== Tourism Platform Deployment Log ===" > "$LOG_FILE"
    echo "Started at: $TIMESTAMP" >> "$LOG_FILE"
    
    # Check prerequisites
    check_prerequisites
    
    # 1. Check if Docker Swarm is initialized
    if ! docker node ls &> /dev/null; then
        print_status "Initializing Docker Swarm..."
        docker swarm init
    else
        print_status "Docker Swarm already initialized"
    fi
    
    # 2. Create network if it doesn't exist
    if ! docker network ls | grep -q tourism_network; then
        print_status "Creating overlay network..."
        docker network create --driver overlay tourism_network
    else
        print_status "Network 'tourism_network' already exists"
    fi
    
    # 3. Clean up any old services (to avoid port conflicts)
    print_status "Cleaning up old services..."
    docker stack rm "$STACK_NAME" 2>/dev/null || true
    docker stack rm tourism 2>/dev/null || true
    
    # Wait for cleanup to complete
    print_status "Waiting for cleanup..."
    sleep 15
    
    # 4. Build images with error handling
    print_status "Building Docker images..."
    if ! docker-compose build; then
        print_error "Failed to build images!"
        exit 1
    fi
    
    # 5. Deploy stack
    print_status "Deploying stack '$STACK_NAME'..."
    if ! docker stack deploy -c docker-stack.yml "$STACK_NAME"; then
        print_error "Failed to deploy stack!"
        exit 1
    fi

    # 6. Wait for services to start
    print_status "Waiting for services to start..."
    sleep 30
    
    # 7. Wait for each service to be healthy
    print_status "Waiting for services to be healthy..."
    wait_for_service_health "postgres"
    wait_for_service_health "auth-service"
    wait_for_service_health "tours-service"
    wait_for_service_health "booking-service"
    wait_for_service_health "frontend"
    
    # 8. Check deployment status
    print_status "Checking service status..."
    docker service ls
    
    # 9. Health check endpoints
    print_status "Performing health checks..."
    check_service_health "auth-service" "http://localhost:8000/health"
    check_service_health "tours-service" "http://localhost:8001/health"
    check_service_health "booking-service" "http://localhost:8002/health"
    check_service_health "frontend" "http://localhost:8080"
    
    echo ""
    print_status "🎉 Deployment completed!"
    echo ""
    
    # 10. Show final status with retries
    print_status "Final service status (checking multiple times):"
    for i in {1..5}; do
        echo "Attempt $i/5:"
        docker service ls --format "table {{.Name}}\t{{.Replicas}}\t{{.Image}}"
        echo ""
        
        # Check if all services are running
        RUNNING_SERVICES=$(docker service ls --format "table {{.Replicas}}" | grep -E "[0-9]/[0-9]" | wc -l)
        TOTAL_SERVICES=$(docker service ls --format "table {{.Name}}" | wc -l)
        TOTAL_SERVICES=$((TOTAL_SERVICES - 1)) # subtract header
        
        if [ "$RUNNING_SERVICES" -eq "$TOTAL_SERVICES" ] && [ "$TOTAL_SERVICES" -gt 0 ]; then
            print_status "All services are running! ✅"
            break
        fi
        
        if [ $i -lt 5 ]; then
            echo "Waiting for all services to start..."
            sleep 15
        fi
    done
    
    echo ""
    echo "🌐 Access URLs:"
    echo "   Frontend:     http://localhost:8080"
    echo "   Auth API:     http://localhost:8000"
    echo "   Tours API:    http://localhost:8001" 
    echo "   Booking API:  http://localhost:8002"
    echo ""
    echo "📋 Useful commands:"
    echo "   Check logs:    docker service logs ${STACK_NAME}_auth-service"
    echo "   Check all:     docker service ls"
    echo "   Scale service: docker service scale ${STACK_NAME}_auth-service=2"
    echo "   View logs:     tail -f $LOG_FILE"
    echo ""
    print_status "Deployment script finished!"
    echo "Log file: $LOG_FILE"
}

# Run main function
main "$@"