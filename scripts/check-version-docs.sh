#!/bin/bash

# Check that all version directories have required files
REQUIRED_FILES=("favicon.ico" "openapi.json" "README.md")
MISSING_FILES=()
EXIT_CODE=0

# Only check if docs/version exists
if [ ! -d "docs/version" ]; then
    echo "⚠️  docs/version directory does not exist yet"
    exit 0
fi

# Find all version directories
for version_dir in docs/version/v*/; do
    if [ -d "$version_dir" ]; then
        version=$(basename "$version_dir")

        for file in "${REQUIRED_FILES[@]}"; do
            if [ ! -f "$version_dir$file" ]; then
                MISSING_FILES+=("$version_dir$file")
                EXIT_CODE=1
            fi
        done
    fi
done

# If any files are missing, fail the check
if [ $EXIT_CODE -ne 0 ]; then
    echo "❌ Version documentation check failed!"
    echo ""
    echo "The following required files are missing:"
    for file in "${MISSING_FILES[@]}"; do
        echo "  - $file"
    done
    echo ""
    echo "Each docs/version/vX/ directory must contain:"
    echo "  - favicon.ico"
    echo "  - openapi.json"
    echo "  - README.md"
    echo ""
    echo "Please add the missing files before committing."
    exit 1
fi

echo "✅ All version directories have required documentation files"
exit 0
