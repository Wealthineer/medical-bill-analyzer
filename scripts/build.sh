#!/bin/bash
# Build script for Medical Bill Analyzer (Linux/macOS)
#
# Usage:
#   ./scripts/build.sh [--skip-tests] [--clean]
#
# Options:
#   --skip-tests  Skip running tests before build
#   --clean       Clean build artifacts before building

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Parse arguments
SKIP_TESTS=false
CLEAN=false

for arg in "$@"; do
    case $arg in
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        --clean)
            CLEAN=true
            shift
            ;;
        *)
            echo -e "${RED}Unknown argument: $arg${NC}"
            echo "Usage: $0 [--skip-tests] [--clean]"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  Medical Bill Analyzer - Build Script${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Change to project root
cd "$PROJECT_ROOT"

# Step 1: Clean if requested
if [ "$CLEAN" = true ]; then
    echo -e "${YELLOW}Cleaning build artifacts...${NC}"
    rm -rf build/ dist/ *.spec 2>/dev/null || true
    echo -e "${GREEN}Clean complete.${NC}"
    echo ""
fi

# Step 2: Check dependencies
echo -e "${YELLOW}Checking dependencies...${NC}"
if ! command -v poetry &> /dev/null; then
    echo -e "${RED}Error: Poetry is not installed.${NC}"
    echo "Please install Poetry: https://python-poetry.org/docs/#installation"
    exit 1
fi

# Install dependencies
echo "Installing dependencies..."
poetry install --quiet
echo -e "${GREEN}Dependencies installed.${NC}"
echo ""

# Step 3: Run tests (unless skipped)
if [ "$SKIP_TESTS" = false ]; then
    echo -e "${YELLOW}Running tests...${NC}"
    if poetry run pytest -q --tb=short; then
        echo -e "${GREEN}All tests passed!${NC}"
    else
        echo -e "${RED}Tests failed. Aborting build.${NC}"
        echo "Use --skip-tests to build anyway (not recommended)."
        exit 1
    fi
    echo ""
else
    echo -e "${YELLOW}Skipping tests (--skip-tests flag set)${NC}"
    echo ""
fi

# Step 4: Build executable
echo -e "${YELLOW}Building executable with PyInstaller...${NC}"
poetry run pyinstaller packaging/medical-bill-analyzer.spec --noconfirm

# Check if build succeeded
if [ -f "dist/medical-bill-analyzer" ]; then
    echo -e "${GREEN}Build successful!${NC}"
    echo ""

    # Get file size
    SIZE=$(du -h dist/medical-bill-analyzer | cut -f1)
    echo -e "Executable: ${BLUE}dist/medical-bill-analyzer${NC}"
    echo -e "Size: ${BLUE}$SIZE${NC}"
    echo ""

    # Step 5: Test executable
    echo -e "${YELLOW}Testing executable...${NC}"
    if ./dist/medical-bill-analyzer --version 2>/dev/null; then
        echo -e "${GREEN}Executable works correctly!${NC}"
    else
        # --version might not be implemented, try --help
        if ./dist/medical-bill-analyzer --help >/dev/null 2>&1; then
            echo -e "${GREEN}Executable works correctly!${NC}"
        else
            echo -e "${YELLOW}Warning: Could not verify executable. Please test manually.${NC}"
        fi
    fi
    echo ""

    echo -e "${GREEN}================================================${NC}"
    echo -e "${GREEN}  Build Complete!${NC}"
    echo -e "${GREEN}================================================${NC}"
    echo ""
    echo "To run the application:"
    echo "  ./dist/medical-bill-analyzer"
    echo ""
    echo "To create a release package:"
    echo "  ./scripts/package-release.sh"
    echo ""
else
    echo -e "${RED}Build failed. Executable not found.${NC}"
    exit 1
fi
