@echo off
REM Build script for Django RBAC Core package (Windows)

echo ========================================
echo Building Django RBAC Core Package
echo ========================================

REM Clean previous builds
echo.
echo Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist django_rbac_core.egg-info rmdir /s /q django_rbac_core.egg-info

REM Install/upgrade build tools
echo.
echo Installing/upgrading build tools...
python -m pip install --upgrade pip setuptools wheel build

REM Build the package
echo.
echo Building source distribution and wheel...
python -m build

REM Check if build was successful
if exist dist (
    echo.
    echo ========================================
    echo Build completed successfully!
    echo ========================================
    echo.
    echo Built packages:
    dir /b dist
    echo.
    echo To install locally, run:
    echo   pip install dist\django_rbac_core-0.1.0-py3-none-any.whl
    echo.
    echo To upload to PyPI, run:
    echo   python -m pip install --upgrade twine
    echo   python -m twine upload dist/*
) else (
    echo.
    echo ========================================
    echo Build failed! Check errors above.
    echo ========================================
    exit /b 1
)
