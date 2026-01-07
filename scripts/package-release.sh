#!/bin/bash
# Package release script for Medical Bill Analyzer
#
# Creates a release package containing the executable and documentation.
#
# Usage:
#   ./scripts/package-release.sh [VERSION]
#
# Arguments:
#   VERSION  Version string (e.g., 1.0.0). If not provided, reads from pyproject.toml.
#
# Output:
#   releases/medical-bill-analyzer-vVERSION-PLATFORM.tar.gz (Linux/macOS)
#   releases/medical-bill-analyzer-vVERSION-PLATFORM.zip (Windows)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Get version
if [ -n "$1" ]; then
    VERSION="$1"
else
    # Extract version from pyproject.toml
    VERSION=$(grep '^version = ' pyproject.toml | head -1 | cut -d'"' -f2)
fi

if [ -z "$VERSION" ]; then
    echo -e "${RED}Error: Could not determine version.${NC}"
    echo "Please provide version as argument: $0 1.0.0"
    exit 1
fi

# Detect platform
case "$(uname -s)" in
    Linux*)     PLATFORM="linux";;
    Darwin*)    PLATFORM="macos";;
    MINGW*|MSYS*|CYGWIN*)  PLATFORM="windows";;
    *)          PLATFORM="unknown";;
esac

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  Medical Bill Analyzer - Release Packager${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""
echo -e "Version:  ${GREEN}v$VERSION${NC}"
echo -e "Platform: ${GREEN}$PLATFORM${NC}"
echo ""

# Check if executable exists
if [ "$PLATFORM" = "windows" ]; then
    EXECUTABLE="dist/medical-bill-analyzer.exe"
else
    EXECUTABLE="dist/medical-bill-analyzer"
fi

if [ ! -f "$EXECUTABLE" ]; then
    echo -e "${RED}Error: Executable not found at $EXECUTABLE${NC}"
    echo "Please run ./scripts/build.sh first."
    exit 1
fi

# Create releases directory
mkdir -p releases

# Create package directory
PACKAGE_NAME="medical-bill-analyzer-v$VERSION-$PLATFORM"
PACKAGE_DIR="releases/$PACKAGE_NAME"

echo -e "${YELLOW}Creating release package...${NC}"

# Clean existing package directory
rm -rf "$PACKAGE_DIR"
mkdir -p "$PACKAGE_DIR"

# Copy files
echo "Copying executable..."
cp "$EXECUTABLE" "$PACKAGE_DIR/"

echo "Copying documentation..."
cp packaging/GETTING_STARTED.txt "$PACKAGE_DIR/" 2>/dev/null || echo "  (GETTING_STARTED.txt not found, skipping)"
cp packaging/README.txt "$PACKAGE_DIR/" 2>/dev/null || echo "  (README.txt not found, skipping)"
cp LICENSE "$PACKAGE_DIR/LICENSE.txt" 2>/dev/null || echo "  (LICENSE not found, skipping)"

# Create archive
echo ""
echo -e "${YELLOW}Creating archive...${NC}"

if [ "$PLATFORM" = "windows" ]; then
    # Create zip for Windows
    ARCHIVE="releases/$PACKAGE_NAME.zip"
    cd releases
    zip -r "$PACKAGE_NAME.zip" "$PACKAGE_NAME"
    cd ..
else
    # Create tar.gz for Linux/macOS
    ARCHIVE="releases/$PACKAGE_NAME.tar.gz"
    tar -czvf "$ARCHIVE" -C releases "$PACKAGE_NAME"
fi

# Get archive size
SIZE=$(du -h "$ARCHIVE" | cut -f1)

# Cleanup package directory
rm -rf "$PACKAGE_DIR"

echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}  Release Package Created!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo -e "Package: ${BLUE}$ARCHIVE${NC}"
echo -e "Size:    ${BLUE}$SIZE${NC}"
echo ""
echo "Contents:"
if [ "$PLATFORM" = "windows" ]; then
    unzip -l "$ARCHIVE" 2>/dev/null || true
else
    tar -tzvf "$ARCHIVE" 2>/dev/null || true
fi
echo ""
