@echo off
setlocal

:: Title and Description
title MetaGPT Automated Setup
echo ===========================================
echo        MetaGPT Automated Setup
echo ===========================================

:: Check Python installation
echo Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed. Please install Python 3.9+ and try again.
    pause
    exit /b 1
)

:: Create a Conda environment (if Conda is available)
echo Checking for Conda...
conda --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Conda not found. Skipping Conda environment creation.
) else (
    echo Creating Conda environment...
    conda create -n metagpt python=3.9 -y
    conda activate metagpt
)

:: Install MetaGPT via pip
echo Installing MetaGPT...
pip install --upgrade metagpt

:: Clone the MetaGPT repository if necessary
if not exist MetaGPT (
    echo Cloning the MetaGPT repository...
    git clone https://github.com/geekan/MetaGPT.git
    cd MetaGPT
    pip install --upgrade -e .
) else (
    echo MetaGPT repository already exists.
    cd MetaGPT
)

:: Initialize MetaGPT config
echo Initializing MetaGPT configuration...
metagpt --init-config

:: Install additional dependencies
echo Installing additional dependencies from requirements.txt...
pip install -r requirements.txt

:: Summary
echo ===========================================
echo          Setup Completed Successfully
echo ===========================================
pause

endlocal
