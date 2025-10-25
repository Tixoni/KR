#!/bin/bash

# check-status.sh - Comprehensive status checker for Tourism Platform
set -e  # Exit on any error

# Configuration
STACK_NAME="tourism-platform"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "🔍 Checking Tourism Platform Stack Status at $TIMESTAMP..."

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

# Function to check service health
check_service_health() {
    local service_name=$1
    local health_url=$2
    
    if [ -n "$health_url" ]; then
        if curl -f -s "$health_url" > /dev/null 2>&1; then
            print_status "$service_name: ✅ Healthy"
            return 0
        else
            print_error "$service_name: ❌ Unhealthy"
            return 1
        fi
    fi
}

# Function to get service status
get_service_status() {
    local service_name=$1
    local replicas=$(docker service ls --format "{{.Replicas}}" --filter name="$STACK_NAME"_"$service_name")
    local image=$(docker service ls --format "{{.Image}}" --filter name="$STACK_NAME"_"$service_name")
    
    if [ -n "$replicas" ]; then
        echo "  📊 Replicas: $replicas"
        echo "  🐳 Image: $image"
        
        # Check if all replicas are running
        if echo "$replicas" | grep -q "/"; then
            local running=$(echo "$replicas" | cut -d'/' -f1)
            local total=$(echo "$replicas" | cut -d'/' -f2)
            
            if [ "$running" -eq "$total" ]; then
                print_status "$service_name: ✅ All replicas running"
            else
                print_warning "$service_name: ⚠️  $running/$total replicas running"
            fi
        fi
    else
        print_error "$service_name: ❌ Service not found"
    fi
}

# Function to show resource usage
show_resource_usage() {
    print_info "Resource Usage:"
    echo "  💾 Memory:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" 2>/dev/null | grep "$STACK_NAME" || echo "    No running containers"
    
    echo ""
    print_info "Disk Usage:"
    docker system df
}

# Function to show logs
show_logs() {
    local service_name=$1
    local lines=${2:-10}
    
    print_info "Recent logs for $service_name (last $lines lines):"
    docker service logs --tail "$lines" "$STACK_NAME"_"$service_name" 2>/dev/null || print_warning "No logs available"
}

# Main status check function
main() {
    # Check if stack exists
    if ! docker stack ls --format "{{.Name}}" | grep -q "^$STACK_NAME$"; then
        print_error "Stack '$STACK_NAME' does not exist!"
        exit 1
    fi
    
    print_status "Stack '$STACK_NAME' found ✅"
    
    echo ""
    print_info "📋 Services Overview:"
    docker service ls --filter name="$STACK_NAME"
    
    echo ""
    print_info "🔧 Detailed Service Status:"
    
    # Check each service
    get_service_status "postgres"
    get_service_status "auth-service"
    get_service_status "tours-service"
    get_service_status "booking-service"
    get_service_status "frontend"
    
    echo ""
    print_info "🌐 Network Status:"
    docker network ls | grep tourism_network || print_warning "Network not found"
    
    echo ""
    print_info "💾 Volume Status:"
    docker volume ls | grep "$STACK_NAME" || print_warning "No volumes found"
    
    echo ""
    print_info "🏥 Health Checks:"
    check_service_health "auth-service" "http://localhost:8000/health"
    check_service_health "tours-service" "http://localhost:8001/health"
    check_service_health "booking-service" "http://localhost:8002/health"
    check_service_health "frontend" "http://localhost:8080"
    
    echo ""
    show_resource_usage
    
    echo ""
    print_info "🌐 Access URLs:"
    echo "  Frontend:     http://localhost:8080"
    echo "  Auth API:     http://localhost:8000"
    echo "  Tours API:    http://localhost:8001"
    echo "  Booking API:  http://localhost:8002"
    
    echo ""
    print_info "📋 Useful Commands:"
    echo "  View logs:    docker service logs ${STACK_NAME}_auth-service"
    echo "  Scale service: docker service scale ${STACK_NAME}_auth-service=2"
    echo "  Restart:       docker service update --force ${STACK_NAME}_auth-service"
    echo "  Full status:    docker service ps ${STACK_NAME}_auth-service"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --logs)
            show_logs "$2" "$3"
            exit 0
            ;;
        --health)
            check_service_health "$2" "$3"
            exit 0
            ;;
        --resources)
            show_resource_usage
            exit 0
            ;;
        -h|--help)
            echo "Usage: $0 [--logs SERVICE [LINES]] [--health SERVICE URL] [--resources]"
            echo "  --logs SERVICE [LINES]    Show logs for service (default: 10 lines)"
            echo "  --health SERVICE URL      Check health of service"
            echo "  --resources               Show resource usage"
            echo "  -h, --help                Show this help"
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