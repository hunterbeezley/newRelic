#!/bin/bash
# SendGrid Suppression Management Tool - Setup Script
# =====================================================
# This script sets up the SendGrid tool for managing email suppressions
# across 7 New Relic SendGrid accounts (1 parent + 6 sub-accounts).
#
# What this script does:
# 1. Checks that Python 3 is installed
# 2. Creates a virtual environment for Python dependencies
# 3. Installs required Python packages
# 4. Sets up your .env configuration file with API keys
# 5. Tests connections to all SendGrid accounts
# 6. Creates necessary directories
#
# No Python or development experience needed - just follow the prompts!

set -e  # Exit on error

# Color codes for better readability (works in most terminals)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Detect if we're in an interactive terminal
if [ -t 1 ]; then
    USE_COLOR=true
else
    USE_COLOR=false
fi

# Helper functions for colored output
print_header() {
    if [ "$USE_COLOR" = true ]; then
        echo -e "\n${BOLD}${CYAN}========================================${NC}"
        echo -e "${BOLD}${CYAN}$1${NC}"
        echo -e "${BOLD}${CYAN}========================================${NC}\n"
    else
        echo ""
        echo "========================================"
        echo "$1"
        echo "========================================"
        echo ""
    fi
}

print_success() {
    if [ "$USE_COLOR" = true ]; then
        echo -e "${GREEN}✓ $1${NC}"
    else
        echo "✓ $1"
    fi
}

print_info() {
    if [ "$USE_COLOR" = true ]; then
        echo -e "${BLUE}ℹ $1${NC}"
    else
        echo "ℹ $1"
    fi
}

print_warning() {
    if [ "$USE_COLOR" = true ]; then
        echo -e "${YELLOW}⚠ $1${NC}"
    else
        echo "⚠ $1"
    fi
}

print_error() {
    if [ "$USE_COLOR" = true ]; then
        echo -e "${RED}✗ ERROR: $1${NC}"
    else
        echo "✗ ERROR: $1"
    fi
}

print_step() {
    if [ "$USE_COLOR" = true ]; then
        echo -e "\n${BOLD}${BLUE}▶ $1${NC}"
    else
        echo ""
        echo "▶ $1"
    fi
}

# Function to compare version numbers
version_gte() {
    # Returns 0 (success) if $1 >= $2
    printf '%s\n%s' "$2" "$1" | sort -V -C
}

# Main setup starts here
print_header "SendGrid Suppression Management Tool - Setup"

# Step 1: Check Python installation
print_step "Step 1/7: Checking Python installation"

if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed or not in your PATH"
    echo ""
    echo "To fix this:"
    echo "  • macOS: Install from https://www.python.org/downloads/ or use 'brew install python3'"
    echo "  • Linux: Use your package manager (e.g., 'sudo apt install python3')"
    echo "  • Windows: Download from https://www.python.org/downloads/"
    echo ""
    exit 1
fi

# Get Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
python_major=$(echo "$python_version" | cut -d. -f1)
python_minor=$(echo "$python_version" | cut -d. -f2)

print_info "Found Python $python_version"

# Check if Python version is >= 3.7
if ! version_gte "$python_version" "3.7.0"; then
    print_error "Python 3.7 or higher is required (found $python_version)"
    echo ""
    echo "To fix this:"
    echo "  • Update Python to version 3.7 or higher"
    echo "  • Visit: https://www.python.org/downloads/"
    echo ""
    exit 1
fi

print_success "Python version is compatible ($python_version >= 3.7)"

# Step 2: Create virtual environment
print_step "Step 2/7: Setting up Python virtual environment"

echo ""
print_info "A virtual environment keeps this tool's dependencies isolated from your system"

if [ -d "venv" ]; then
    print_warning "Virtual environment already exists - skipping creation"
else
    echo "Creating virtual environment..."
    if python3 -m venv venv; then
        print_success "Virtual environment created"
    else
        print_error "Failed to create virtual environment"
        echo ""
        echo "To fix this:"
        echo "  • Make sure 'python3-venv' is installed"
        echo "  • Linux: sudo apt install python3-venv"
        echo "  • macOS: Should work by default"
        echo ""
        exit 1
    fi
fi

# Step 3: Install dependencies
print_step "Step 3/7: Installing Python dependencies"

echo ""
print_info "Installing required packages (requests, urllib3)..."

# Activate virtual environment
source venv/bin/activate

# Upgrade pip silently
if pip install --upgrade pip > /dev/null 2>&1; then
    print_success "pip updated to latest version"
else
    print_warning "Could not update pip (continuing anyway)"
fi

# Install requirements
if pip install -r requirements.txt > /dev/null 2>&1; then
    print_success "Dependencies installed successfully"
else
    print_error "Failed to install dependencies"
    echo ""
    echo "To fix this:"
    echo "  • Check your internet connection"
    echo "  • Try running manually: source venv/bin/activate && pip install -r requirements.txt"
    echo ""
    exit 1
fi

# Step 4: Create logs directory
print_step "Step 4/7: Creating logs directory"

if [ ! -d "logs" ]; then
    mkdir -p logs
    print_success "Logs directory created"
else
    print_success "Logs directory already exists"
fi

# Step 5: Configure SSL certificates (macOS only)
print_step "Step 5/7: Configuring SSL certificates for corporate network"

echo ""
print_info "Setting up SSL certificates from macOS Keychain for secure connections"

if [[ "$OSTYPE" != "darwin"* ]]; then
    print_warning "Not running on macOS - skipping certificate extraction"
    print_info "If you encounter SSL errors, use --no-verify-ssl flag (see documentation)"
else
    CA_BUNDLE_PATH="$HOME/.sendgrid-ca-bundle.pem"

    if [ -f "$CA_BUNDLE_PATH" ]; then
        print_warning "CA bundle already exists at $CA_BUNDLE_PATH"
        echo ""
        read -p "Recreate CA bundle? (y/n, default=n): " recreate_bundle

        if [ "$recreate_bundle" = "y" ] || [ "$recreate_bundle" = "Y" ]; then
            rm "$CA_BUNDLE_PATH"
            print_info "Removed existing CA bundle"
        else
            print_success "Using existing CA bundle"
            SKIP_CA_BUNDLE=true
        fi
    fi

    if [ "$SKIP_CA_BUNDLE" != true ]; then
        echo ""
        print_info "Extracting certificates from macOS System Keychain..."

        # Export system certificates
        if security find-certificate -a -p /Library/Keychains/System.keychain > /tmp/system-certs.pem 2>/dev/null; then
            system_cert_count=$(grep -c 'BEGIN CERTIFICATE' /tmp/system-certs.pem)
            print_success "Exported $system_cert_count certificates from System Keychain"
        else
            print_warning "Could not export system certificates (continuing anyway)"
            touch /tmp/system-certs.pem
        fi

        # Get Python's certifi bundle location
        print_info "Finding Python's certificate bundle..."
        certifi_path=$(python3 -c "import certifi; print(certifi.where())" 2>/dev/null)

        if [ -n "$certifi_path" ] && [ -f "$certifi_path" ]; then
            certifi_cert_count=$(grep -c 'BEGIN CERTIFICATE' "$certifi_path")
            print_success "Found certifi bundle with $certifi_cert_count certificates"

            # Combine certificates
            cat /tmp/system-certs.pem "$certifi_path" > "$CA_BUNDLE_PATH"
            total_certs=$(grep -c 'BEGIN CERTIFICATE' "$CA_BUNDLE_PATH")
            print_success "Created combined CA bundle with $total_certs certificates"

            # Clean up temp file
            rm /tmp/system-certs.pem

            # Test the bundle
            echo ""
            print_info "Testing SSL verification with new CA bundle..."

            if REQUESTS_CA_BUNDLE="$CA_BUNDLE_PATH" python3 -c "import requests; requests.get('https://api.sendgrid.com', timeout=5)" 2>/dev/null; then
                print_success "SSL verification test passed!"

                # Offer to add to shell profile
                echo ""
                print_info "To use this CA bundle automatically, add it to your shell profile"
                read -p "Add REQUESTS_CA_BUNDLE to your shell profile? (y/n, default=y): " add_to_profile

                if [ "$add_to_profile" != "n" ] && [ "$add_to_profile" != "N" ]; then
                    # Detect shell
                    if [ -n "$ZSH_VERSION" ] || [ "$SHELL" = "/bin/zsh" ]; then
                        profile_file="$HOME/.zshrc"
                    else
                        profile_file="$HOME/.bash_profile"
                    fi

                    # Check if already in profile
                    if grep -q "REQUESTS_CA_BUNDLE.*sendgrid-ca-bundle" "$profile_file" 2>/dev/null; then
                        print_warning "REQUESTS_CA_BUNDLE already in $profile_file"
                    else
                        echo "" >> "$profile_file"
                        echo "# SendGrid Python Scripts - Use macOS Keychain certificates for SSL" >> "$profile_file"
                        echo "export REQUESTS_CA_BUNDLE=\"\$HOME/.sendgrid-ca-bundle.pem\"" >> "$profile_file"
                        print_success "Added REQUESTS_CA_BUNDLE to $profile_file"
                        echo ""
                        print_info "Run 'source $profile_file' or restart your terminal to apply changes"
                    fi

                    # Set for current session
                    export REQUESTS_CA_BUNDLE="$CA_BUNDLE_PATH"
                else
                    print_info "Skipped shell profile update"
                    echo ""
                    print_warning "You'll need to set REQUESTS_CA_BUNDLE manually for each session:"
                    echo "  export REQUESTS_CA_BUNDLE=\"$CA_BUNDLE_PATH\""
                fi
            else
                print_warning "SSL test did not complete (but bundle was created)"
                print_info "You may need to use --no-verify-ssl flag if SSL issues persist"
            fi
        else
            print_warning "Could not find certifi bundle - skipping CA bundle creation"
            print_info "If you encounter SSL errors, use --no-verify-ssl flag"
        fi
    fi
fi

# Step 6: Set up .env configuration file
print_step "Step 6/7: Configuring SendGrid API keys"

echo ""
print_info "The .env file stores your SendGrid API keys securely"
print_info "This file is excluded from git and should never be committed"

if [ -f ".env" ]; then
    print_warning ".env file already exists"
    echo ""
    echo "Do you want to:"
    echo "  1. Keep existing .env file (default)"
    echo "  2. Reconfigure API keys (will backup existing .env)"
    echo ""
    read -p "Enter choice (1 or 2): " env_choice

    if [ "$env_choice" = "2" ]; then
        # Backup existing .env
        backup_file=".env.backup.$(date +%Y%m%d_%H%M%S)"
        mv .env "$backup_file"
        print_info "Backed up existing .env to $backup_file"
    else
        print_success "Keeping existing .env file"
        SKIP_ENV_SETUP=true
    fi
fi

if [ "$SKIP_ENV_SETUP" != true ]; then
    if [ ! -f ".env.template" ]; then
        print_error ".env.template file not found"
        echo ""
        echo "The .env.template file is required but missing from this directory."
        echo "Please ensure you have all files from the repository."
        echo ""
        exit 1
    fi

    echo ""
    echo "Creating .env file from template..."
    cp .env.template .env
    print_success ".env file created"
fi

# Check if .env has placeholder values
echo ""
print_info "Checking .env file configuration..."

if grep -q "SG.your_key_here" .env; then
    placeholder_count=$(grep -c "SG.your_key_here" .env)
    print_warning "Found $placeholder_count placeholder API key(s) in .env"
    echo ""
    echo "You still need to add actual API keys to .env before the tool will work."
    echo "Edit the .env file and replace 'SG.your_key_here' with real keys from 1Password."
    echo ""
    SKIP_CONNECTION_TEST=true
else
    print_success ".env file appears to be configured (no placeholders found)"
fi

# Step 7: Test connections
print_step "Step 7/7: Testing SendGrid API connections"

if [ "$SKIP_CONNECTION_TEST" = true ]; then
    print_warning "Skipping connection test (API keys not configured)"
    echo ""
    echo "Once you've added API keys to .env, run the connection test:"
    echo "  source venv/bin/activate"
    echo "  python3 test_connection.py"
else
    echo ""
    print_info "Testing connections to all 7 SendGrid accounts..."
    echo ""

    if python3 test_connection.py; then
        echo ""
        print_success "All connection tests passed!"
    else
        echo ""
        print_error "Some connection tests failed"
        echo ""
        echo "Common issues:"
        echo "  • Invalid API key - verify keys in 1Password GTS vault"
        echo "  • Expired API key - get new keys from SendGrid admin"
        echo "  • Network/firewall issues - check internet connection"
        echo "  • SSL certificate errors - see README for --no-verify-ssl flag"
        echo ""
        echo "To retry:"
        echo "  1. Fix the API keys in .env"
        echo "  2. Run: source venv/bin/activate && python3 test_connection.py"
        echo ""
    fi
fi

# Final success message
print_header "Setup Complete!"

if [ "$SKIP_CONNECTION_TEST" = true ]; then
    print_warning "Remember to configure API keys in .env before using the tool!"
    echo ""
    echo "To configure keys:"
    echo "  1. Get keys from 1Password GTS vault"
    echo "  2. Edit .env: ${CYAN}nano .env${NC}"
    echo "  3. Replace 'SG.your_key_here' with real keys"
    echo "  4. Test: ${CYAN}source venv/bin/activate && python3 test_connection.py${NC}"
    echo ""
fi

print_success "Setup script completed successfully!"
echo ""
