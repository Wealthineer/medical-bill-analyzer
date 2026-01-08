@echo off
REM Build script for Medical Bill Analyzer (Windows)
REM
REM Usage:
REM   scripts\build.bat [--skip-tests] [--clean]
REM
REM Options:
REM   --skip-tests  Skip running tests before build
REM   --clean       Clean build artifacts before building

setlocal enabledelayedexpansion

set SKIP_TESTS=false
set CLEAN=false

REM Parse arguments
:parse_args
if "%~1"=="" goto :main
if /i "%~1"=="--skip-tests" (
    set SKIP_TESTS=true
    shift
    goto :parse_args
)
if /i "%~1"=="--clean" (
    set CLEAN=true
    shift
    goto :parse_args
)
echo Unknown argument: %~1
echo Usage: %0 [--skip-tests] [--clean]
exit /b 1

:main
echo ================================================
echo   Medical Bill Analyzer - Build Script
echo ================================================
echo.

REM Get script directory and project root
set SCRIPT_DIR=%~dp0
cd /d %SCRIPT_DIR%\..

REM Step 1: Clean if requested
if "%CLEAN%"=="true" (
    echo Cleaning build artifacts...
    if exist build rmdir /s /q build
    if exist dist rmdir /s /q dist
    echo Clean complete.
    echo.
)

REM Step 2: Check dependencies
echo Checking dependencies...
where uv >nul 2>&1
if errorlevel 1 (
    echo Error: uv is not installed.
    echo Please install uv: https://docs.astral.sh/uv/getting-started/installation/
    exit /b 1
)

REM Install dependencies
echo Installing dependencies...
uv sync --quiet
if errorlevel 1 (
    echo Error: Failed to install dependencies.
    exit /b 1
)
echo Dependencies installed.
echo.

REM Step 3: Run tests (unless skipped)
if "%SKIP_TESTS%"=="false" (
    echo Running tests...
    uv run pytest -q --tb=short
    if errorlevel 1 (
        echo Tests failed. Aborting build.
        echo Use --skip-tests to build anyway ^(not recommended^).
        exit /b 1
    )
    echo All tests passed!
    echo.
) else (
    echo Skipping tests ^(--skip-tests flag set^)
    echo.
)

REM Step 4: Build executable
echo Building executable with PyInstaller...
uv run pyinstaller packaging\medical-bill-analyzer.spec --noconfirm
if errorlevel 1 (
    echo Build failed.
    exit /b 1
)

REM Check if build succeeded
if exist "dist\medical-bill-analyzer.exe" (
    echo Build successful!
    echo.
    echo Executable: dist\medical-bill-analyzer.exe
    echo.

    REM Step 5: Test executable
    echo Testing executable...
    dist\medical-bill-analyzer.exe --help >nul 2>&1
    if errorlevel 1 (
        echo Warning: Could not verify executable. Please test manually.
    ) else (
        echo Executable works correctly!
    )
    echo.

    echo ================================================
    echo   Build Complete!
    echo ================================================
    echo.
    echo To run the application:
    echo   dist\medical-bill-analyzer.exe
    echo.
) else (
    echo Build failed. Executable not found.
    exit /b 1
)

endlocal
