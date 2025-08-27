#!/bin/bash

# setup-env.sh - Environment setup script for em_audit_tool

set -e

echo "=== Environment Setup Script ==="

# Function to show usage
show_usage() {
    echo "Usage: ./setup-env.sh [dev|prod]"
    echo ""
    echo "Arguments:"
    echo "  dev   - Setup development environment"
    echo "  prod  - Setup production environment"
    echo ""
    echo "If no argument is provided, you will be prompted to choose."
}

# Function to setup environment
setup_environment() {
    local env=$1
    
    if [ "$env" = "dev" ]; then
        echo "Setting up development environment..."
        if [ -f ".env.development" ]; then
            cp .env.development .env
            echo "✓ Development environment configured (.env.development → .env)"
        else
            echo "✗ Error: .env.development file not found!"
            exit 1
        fi
    elif [ "$env" = "prod" ]; then
        echo "Setting up production environment..."
        if [ -f ".env.production" ]; then
            cp .env.production .env
            echo "✓ Production environment configured (.env.production → .env)"
        else
            echo "✗ Error: .env.production file not found!"
            exit 1
        fi
    else
        echo "✗ Error: Invalid environment '$env'. Use 'dev' or 'prod'."
        exit 1
    fi
}

# Main logic
if [ $# -eq 0 ]; then
    echo "Which environment do you want to setup?"
    echo "1) Development"
    echo "2) Production"
    read -p "Choose (1-2): " choice
    
    case $choice in
        1) setup_environment "dev" ;;
        2) setup_environment "prod" ;;
        *) echo "Invalid choice. Exiting."; exit 1 ;;
    esac
elif [ $# -eq 1 ]; then
    if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
        show_usage
        exit 0
    fi
    setup_environment "$1"
else
    echo "✗ Error: Too many arguments."
    show_usage
    exit 1
fi

echo "Environment setup completed successfully!"
