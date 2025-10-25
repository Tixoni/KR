#!/bin/bash

# logs-swarm.sh - Log viewer for Tourism Platform
set -e  # Exit on any error

# Configuration
STACK_NAME="tourism-platform"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "📋 Tourism Platform Logs at $TIMESTAMP..."

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

# Function to show logs for a specific service
show_service_logs() {
    local service_name=$1
    local lines=${2:-50}
    local follow=${3:-false}
    
    print_info "Logs for $service_name (last $lines lines):"
    echo "----------------------------------------"
    
    if [ "$follow" = "true" ]; then
        docker service logs --tail "$lines" -f "$STACK_NAME"_"$service_name" 2>/dev/null || print_warning "No logs available"
    else
        docker service logs --tail "$lines" "$STACK_NAME"_"$service_name" 2>/dev/null || print_warning "No logs available"
    fi
}

# Function to show all logs
show_all_logs() {
    local lines=${1:-20}
    
    print_info "All services logs (last $lines lines each):"
    echo "=========================================="
    
    for service in postgres auth-service tours-service booking-service frontend; do
        echo ""
        print_info "--- $service ---"
        docker service logs --tail "$lines" "$STACK_NAME"_"$service" 2>/dev/null || print_warning "No logs available for $service"
    done
}

# Function to show error logs only
show_error_logs() {
    local lines=${1:-50}
    
    print_info "Error logs (last $lines lines):"
    echo "=================================="
    
    for service in postgres auth-service tours-service booking-service frontend; do
        echo ""
        print_info "--- $service errors ---"
        docker service logs --tail "$lines" "$STACK_NAME"_"$service" 2>/dev/null | grep -i error || print_warning "No errors found for $service"
    done
}

# Main logs function
main() {
    # Check if stack exists
    if ! docker stack ls --format "{{.Name}}" | grep -q "^$STACK_NAME$"; then
        print_error "Stack '$STACK_NAME' does not exist!"
        exit 1
    fi
    
    print_status "Stack '$STACK_NAME' found ✅"
    
    # Parse command line arguments
    case "${1:-all}" in
        "auth"|"auth-service")
            show_service_logs "auth-service" "${2:-50}" "${3:-false}"
            ;;
        "tours"|"tours-service")
            show_service_logs "tours-service" "${2:-50}" "${3:-false}"
            ;;
        "booking"|"booking-service")
            show_service_logs "booking-service" "${2:-50}" "${3:-false}"
            ;;
        "frontend")
            show_service_logs "frontend" "${2:-50}" "${3:-false}"
            ;;
        "postgres")
            show_service_logs "postgres" "${2:-50}" "${3:-false}"
            ;;
        "all")
            show_all_logs "${2:-20}"
            ;;
        "errors")
            show_error_logs "${2:-50}"
            ;;
        "follow")
            show_service_logs "${2:-auth-service}" "${3:-50}" "true"
            ;;
        "-h"|"--help")
            echo "Usage: $0 [SERVICE] [LINES] [follow]"
            echo ""
            echo "Services:"
            echo "  auth, auth-service     Auth service logs"
            echo "  tours, tours-service   Tours service logs"
            echo "  booking, booking-service Booking service logs"
            echo "  frontend              Frontend logs"
            echo "  postgres              Database logs"
            echo "  all                   All services logs (default)"
            echo "  errors                Error logs only"
            echo "  follow SERVICE        Follow logs for service"
            echo ""
            echo "Examples:"
            echo "  $0                    # Show all logs (20 lines each)"
            echo "  $0 auth 100           # Show auth logs (100 lines)"
            echo "  $0 follow auth        # Follow auth logs"
            echo "  $0 errors 200         # Show error logs (200 lines)"
            exit 0
            ;;
        *)
            print_error "Unknown service: $1"
            echo "Use '$0 --help' for usage information"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
