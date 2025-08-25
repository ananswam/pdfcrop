#!/bin/bash

# Universal Setup Script
# Installs uv, configures shell profiles, and runs uv sync
# Runs without user interaction and includes comprehensive error handling

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to detect shell profile files
get_shell_profiles() {
    local profiles=()
    
    # Check for common shell profile files
    if [[ -f "$HOME/.bashrc" ]]; then
        profiles+=("$HOME/.bashrc")
    fi
    
    if [[ -f "$HOME/.zshrc" ]]; then
        profiles+=("$HOME/.zshrc")
    fi
    
    # Create .bashrc if it doesn't exist and bash is available
    if command_exists bash && [[ ! -f "$HOME/.bashrc" ]]; then
        touch "$HOME/.bashrc"
        profiles+=("$HOME/.bashrc")
        log_info "Created ~/.bashrc"
    fi
    
    # Create .zshrc if it doesn't exist and zsh is available
    if command_exists zsh && [[ ! -f "$HOME/.zshrc" ]]; then
        touch "$HOME/.zshrc"
        profiles+=("$HOME/.zshrc")
        log_info "Created ~/.zshrc"
    fi
    
    printf '%s\n' "${profiles[@]}"
}

# Function to add uv to PATH in shell profiles
configure_shell_profiles() {
    local uv_path="$HOME/.local/bin"
    local shell_config='export PATH="$HOME/.local/bin:$PATH"'
    
    log_info "Configuring shell profiles..."
    
    # Get available shell profiles
    local profiles
    readarray -t profiles < <(get_shell_profiles)
    
    if [[ ${#profiles[@]} -eq 0 ]]; then
        log_warning "No shell profile files found. You may need to manually add $uv_path to your PATH."
        return 0
    fi
    
    for profile in "${profiles[@]}"; do
        if [[ -f "$profile" ]]; then
            # Check if PATH configuration already exists
            if grep -q "HOME/.local/bin" "$profile" 2>/dev/null; then
                log_info "PATH already configured in $profile"
            else
                echo "" >> "$profile"
                echo "# Added by uv setup script" >> "$profile"
                echo "$shell_config" >> "$profile"
                log_success "Added uv to PATH in $profile"
            fi
        fi
    done
}

# Function to install uv
install_uv() {
    log_info "Installing uv..."
    
    # Check if curl is available
    if ! command_exists curl; then
        log_error "curl is required but not installed. Please install curl first."
        exit 1
    fi
    
    # Download and install uv
    if curl -LsSf https://astral.sh/uv/install.sh | sh; then
        log_success "uv installed successfully"
    else
        log_error "Failed to install uv"
        exit 1
    fi
    
    # Add uv to current session PATH
    export PATH="$HOME/.local/bin:$PATH"
    
    # Configure shell profiles
    configure_shell_profiles
}

# Function to verify uv installation
verify_uv() {
    # Add uv to PATH for current session if not already there
    if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
        export PATH="$HOME/.local/bin:$PATH"
    fi
    
    if command_exists uv; then
        local uv_version
        uv_version=$(uv --version 2>/dev/null || echo "unknown")
        log_success "uv is available (version: $uv_version)"
        return 0
    else
        log_error "uv is not available in PATH"
        return 1
    fi
}

# Function to check for Python project files
check_project_files() {
    local project_files=("pyproject.toml" "uv.lock" "requirements.txt" "setup.py" "setup.cfg")
    local found_files=()
    
    for file in "${project_files[@]}"; do
        if [[ -f "$file" ]]; then
            found_files+=("$file")
        fi
    done
    
    if [[ ${#found_files[@]} -eq 0 ]]; then
        log_warning "No Python project files found in current directory"
        log_warning "Expected files: ${project_files[*]}"
        return 1
    else
        log_info "Found project files: ${found_files[*]}"
        return 0
    fi
}

# Function to run uv sync
run_uv_sync() {
    log_info "Running uv sync..."
    
    # Check if we're in a Python project directory
    if ! check_project_files; then
        log_error "Not in a Python project directory. Cannot run uv sync."
        log_info "Make sure you're in a directory with pyproject.toml or other Python project files."
        exit 1
    fi
    
    # Run uv sync with error handling
    if uv sync; then
        log_success "uv sync completed successfully"
    else
        log_error "uv sync failed"
        log_info "This might be due to:"
        log_info "  - Missing or invalid pyproject.toml"
        log_info "  - Network connectivity issues"
        log_info "  - Python version compatibility issues"
        exit 1
    fi
}

# Main execution
main() {
    log_info "Starting universal setup script..."
    
    # Check if uv is already installed and available
    if verify_uv; then
        log_info "uv is already installed and configured"
    else
        log_info "uv not found, installing..."
        install_uv
        
        # Verify installation
        if ! verify_uv; then
            log_error "uv installation verification failed"
            exit 1
        fi
    fi
    
    # Run uv sync
    run_uv_sync
    
    log_success "Setup completed successfully!"
    log_info "Note: You may need to restart your shell or run 'source ~/.bashrc' (or ~/.zshrc) for PATH changes to take effect in new sessions."
}

# Run main function
main "$@"
