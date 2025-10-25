#!/bin/bash

# manage-swarm.sh - Main management script for Tourism Platform
set -e  # Exit on any error

# Configuration
STACK_NAME="tourism-platform"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "🎛️  Tourism Platform Management at $TIMESTAMP..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
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

print_header() {
    echo -e "${PURPLE}[HEADER]${NC} $1"
}

# Function to show help
show_help() {
    echo "🎛️  Tourism Platform Management Script"
    echo "======================================"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  start       Start the platform (quick start)"
    echo "  stop        Stop the platform (quick stop)"
    echo "  restart     Restart the platform"
    echo "  deploy      Full deployment with build"
    echo "  status      Check platform status"
    echo "  logs        View logs"
    echo "  cleanup     Clean up platform"
    echo "  scale       Scale services"
    echo "  health      Health check"
    echo "  help        Show this help"
    echo ""
    echo "Examples:"
    echo "  $0 start                    # Quick start"
    echo "  $0 deploy                  # Full deployment"
    echo "  $0 status                  # Check status"
    echo "  $0 logs auth 100           # View auth logs"
    echo "  $0 scale auth-service 5    # Scale auth service to 5 replicas"
    echo "  $0 health                  # Health check"
    echo ""
    echo "For detailed help on specific commands:"
    echo "  $0 logs --help"
    echo "  $0 scale --help"
}

# Function to check if stack exists
stack_exists() {
    docker stack ls --format "{{.Name}}" | grep -q "^$STACK_NAME$"
}

# Function to show platform status
show_status() {
    print_header "Platform Status"
    
    if stack_exists; then
        print_status "Stack '$STACK_NAME' is running ✅"
        echo ""
        docker service ls --filter name="$STACK_NAME"
        echo ""
        print_info "🌐 Access URLs:"
        echo "  Frontend:     http://localhost:8080"
        echo "  Auth API:     http://localhost:8000"
        echo "  Tours API:    http://localhost:8001"
        echo "  Booking API:  http://localhost:8002"
    else
        print_warning "Stack '$STACK_NAME' is not running"
        print_info "Use '$0 start' or '$0 deploy' to start the platform"
    fi
}

# Function to scale services
scale_service() {
    local service_name=$1
    local replicas=$2
    
    if [ -z "$service_name" ] || [ -z "$replicas" ]; then
        print_error "Usage: $0 scale SERVICE_NAME REPLICAS"
        echo ""
        echo "Available services:"
        echo "  postgres, auth-service, tours-service, booking-service, frontend"
        echo ""
        echo "Examples:"
        echo "  $0 scale auth-service 5"
        echo "  $0 scale frontend 3"
        exit 1
    fi
    
    if ! stack_exists; then
        print_error "Stack '$STACK_NAME' does not exist!"
        exit 1
    fi
    
    print_status "Scaling $service_name to $replicas replicas..."
    docker service scale "${STACK_NAME}_${service_name}=${replicas}"
    
    print_status "Scaling completed! New status:"
    docker service ls --filter name="$STACK_NAME"_"$service_name"
}

# Function to perform health check
health_check() {
    print_header "Health Check"
    
    if ! stack_exists; then
        print_error "Stack '$STACK_NAME' does not exist!"
        exit 1
    fi
    
    print_info "Checking service health..."
    
    # Check each service
    for service in auth-service tours-service booking-service frontend; do
        local url=""
        case $service in
            "auth-service") url="http://localhost:8000/health" ;;
            "tours-service") url="http://localhost:8001/health" ;;
            "booking-service") url="http://localhost:8002/health" ;;
            "frontend") url="http://localhost:8080" ;;
        esac
        
        if [ -n "$url" ]; then
            if curl -f -s "$url" > /dev/null 2>&1; then
                print_status "$service: ✅ Healthy"
            else
                print_error "$service: ❌ Unhealthy"
            fi
        fi
    done
}

# Main management function
main() {
    case "${1:-help}" in
        "start")
            print_header "Starting Tourism Platform"
            ./start-swarm.sh
            ;;
        "stop")
            print_header "Stopping Tourism Platform"
            ./stop-swarm.sh
            ;;
        "restart")
            print_header "Restarting Tourism Platform"
            ./restart-swarm.sh
            ;;
        "deploy")
            print_header "Full Deployment"
            ./deploy-swarm.sh
            ;;
        "status")
            show_status
            ;;
        "logs")
            shift
            ./logs-swarm.sh "$@"
            ;;
        "cleanup")
            print_header "Cleanup"
            ./cleanup-swarm.sh "$@"
            ;;
        "scale")
            shift
            scale_service "$@"
            ;;
        "health")
            health_check
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            print_error "Unknown command: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
