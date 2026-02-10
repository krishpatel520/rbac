#!/bin/bash
# Build script for Django RBAC Core package (Linux/Mac)

echo "========================================"
echo "Building Django RBAC Core Package"
echo "========================================"

# Clean previous builds
echo ""
echo "Cleaning previous builds..."
rm -rf build dist *.egg-info

# Install/upgrade build tools
echo ""
echo "Installing/upgrading build tools..."
python -m pip install --upgrade pip setuptools wheel build

# Build the package
echo ""
echo "Building source distribution and wheel..."
python -m build

# Check if build was successful
if [ -d "dist" ]; then
    echo ""
    echo "========================================"
    echo "Build completed successfully!"
    echo "========================================"
    echo ""
    echo "Built packages:"
    ls -lh dist/
    echo ""
    echo "To install locally, run:"
    echo "  pip install dist/django_rbac_core-0.1.0-py3-none-any.whl"
    echo ""
    echo "To upload to PyPI, run:"
    echo "  python -m pip install --upgrade twine"
    echo "  python -m twine upload dist/*"
else
    echo ""
    echo "========================================"
    echo "Build failed! Check errors above."
    echo "========================================"
    exit 1
fi
