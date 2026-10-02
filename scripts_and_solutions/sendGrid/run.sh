#!/bin/bash
# Convenience wrapper for running SendGrid scripts
# Automatically activates virtual environment and runs the requested script

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

print_error() {
    echo -e "${RED}✗ ERROR: $1${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ $1${NC}"
}

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    print_error "Virtual environment not found"
    echo ""
    echo "Please run setup first:"
    echo "  ./setup.sh"
    echo ""
    exit 1
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    print_error ".env file not found"
    echo ""
    echo "Please run setup first:"
    echo "  ./setup.sh"
    echo ""
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# If no arguments provided, show usage
if [ $# -eq 0 ]; then
    echo "Usage: ./run.sh <script> [arguments]"
    echo ""
    echo "Available scripts:"
    echo "  test                   - Test connections to all accounts"
    echo "  check <email>          - Check if email is suppressed"
    echo "  remove <options>       - Remove suppressions"
    echo ""
    echo "Examples:"
    echo "  ./run.sh test"
    echo "  ./run.sh check user@example.com"
    echo "  ./run.sh remove --email user@example.com --dry-run"
    echo "  ./run.sh remove --csv emails.csv"
    echo ""
    exit 0
fi

# Parse command
COMMAND=$1
shift  # Remove first argument, leaving the rest for the script

case "$COMMAND" in
    test)
        print_info "Testing connections to all 7 SendGrid accounts..."
        python3 test_connection.py "$@"
        ;;

    check)
        if [ $# -eq 0 ]; then
            print_error "Email address required"
            echo "Usage: ./run.sh check <email>"
            exit 1
        fi
        print_info "Checking suppressions for: $1"
        python3 check_suppressions.py "$@"
        ;;

    remove)
        if [ $# -eq 0 ]; then
            print_error "Options required"
            echo ""
            echo "Usage:"
            echo "  ./run.sh remove --email <email> [--dry-run]"
            echo "  ./run.sh remove --csv <file> [--dry-run]"
            echo "  ./run.sh remove --domain <domain> [--dry-run]"
            exit 1
        fi
        python3 remove_suppressions.py "$@"
        ;;

    *)
        print_error "Unknown command: $COMMAND"
        echo ""
        echo "Available commands: test, check, remove"
        echo "Run './run.sh' with no arguments for usage information"
        exit 1
        ;;
esac
