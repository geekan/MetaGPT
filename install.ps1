#Requires -Version 5.1

<#
.SYNOPSIS
    Installs MetaGPT and its dependencies.
.DESCRIPTION
    This script automates the installation of MetaGPT, including Python version checking,
    repository cloning, virtual environment setup, dependency installation, and initial configuration.
.NOTES
    Author: Your Name
    Date: $(Get-Date -Format yyyy-MM-dd)
#>

# Strict mode for better error handling
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop" # Exit on first error for most cmdlets

# Function to display messages
function Write-Message {
    param (
        [string]$Message,
        [string]$Type = "INFO" # INFO, WARNING, ERROR, SUCCESS
    )

    $Color = @{
        INFO = "White"
        WARNING = "Yellow"
        ERROR = "Red"
        SUCCESS = "Green"
    }

    Write-Host "[$Type] $Message" -ForegroundColor $Color[$Type]
}

# --- 0. Initial Setup ---
$RepoName = "MetaGPT"
$RepoUrl = "https://github.com/geekan/MetaGPT.git"
$VenvName = ".venv"

# --- 1. Check Python Version ---
Write-Message "1. Checking Python version..."
try {
    $pythonVersionInfo = python --version 2>&1
    Write-Message "Raw Python version output: '$pythonVersionInfo'"
    $pythonVersion = $pythonVersionInfo.Trim()

    if ($pythonVersion -match "Python (\d+)\.(\d+)") {
        $major = [int]$Matches[1]
        $minor = [int]$Matches[2]

        if (($major -eq 3 -and $minor -ge 9 -and $minor -lt 12)) {
            Write-Message "Python version is compatible ($major.$minor)." -Type SUCCESS
        } else {
            Write-Message "Python version $major.$minor is not compatible. MetaGPT requires Python 3.9, 3.10, or 3.11." -Type ERROR
            Write-Message "Please install a compatible Python version and add it to your PATH, then try again." -Type ERROR
            exit 1
        }
    } else {
        Write-Message "Could not determine Python version from output: '$pythonVersion'." -Type ERROR
        Write-Message "Please ensure Python 3.9, 3.10, or 3.11 is installed and in your PATH." -Type ERROR
        exit 1
    }
}
catch {
    Write-Message "Error checking Python version: $($_.Exception.Message)" -Type ERROR
    Write-Message "Please ensure Python 3.9, 3.10, or 3.11 is installed and added to your PATH." -Type ERROR
    exit 1
}
Write-Message "Python version check completed."

# --- 2. Clone Repository ---
Write-Message "2. Handling MetaGPT repository..."
if (Test-Path $RepoName) {
    Write-Message "Directory '$RepoName' already exists." -Type WARNING
    $choice = Read-Host "Do you want to: [R]emove and re-clone | [U]se existing directory | [A]bort? (R/U/A)"
    switch ($choice.ToUpper()) {
        'R' {
            Write-Message "Removing existing '$RepoName' directory..."
            try {
                Remove-Item -Recurse -Force $RepoName
                Write-Message "'$RepoName' directory removed." -Type SUCCESS
            }
            catch {
                Write-Message "Error removing directory '$RepoName': $($_.Exception.Message)" -Type ERROR
                Write-Message "Please remove it manually and try again." -Type ERROR
                exit 1
            }
        }
        'U' {
            Write-Message "Using existing directory '$RepoName'. Skipping clone." -Type INFO
        }
        'A' {
            Write-Message "Aborting installation as requested." -Type INFO
            exit 0
        }
        Default {
            Write-Message "Invalid choice. Aborting installation." -Type ERROR
            exit 1
        }
    }
}

if (-not (Test-Path $RepoName)) {
    Write-Message "Cloning MetaGPT repository from $RepoUrl..."
    try {
        git clone $RepoUrl $RepoName
        Write-Message "Repository cloned successfully into '$RepoName'." -Type SUCCESS
    }
    catch {
        Write-Message "Error cloning repository: $($_.Exception.Message)" -Type ERROR
        Write-Message "Please ensure Git is installed and in your PATH." -Type ERROR
        exit 1
    }
}

try {
    Set-Location $RepoName
    Write-Message "Changed current directory to $(Get-Location)." -Type SUCCESS
}
catch {
    Write-Message "Error changing directory to '$RepoName': $($_.Exception.Message)" -Type ERROR
    exit 1
}

# --- 3. Create and Prepare Virtual Environment ---
Write-Message "3. Setting up Python virtual environment ('$VenvName')..."
$VenvPath = Join-Path -Path (Get-Location) -ChildPath $VenvName
$PipExecutable = Join-Path -Path $VenvPath -ChildPath "Scripts\pip.exe"
$PythonExecutable = Join-Path -Path $VenvPath -ChildPath "Scripts\python.exe"
$ActivateScript = Join-Path -Path $VenvPath -ChildPath "Scripts\Activate.ps1"

if (-not (Test-Path $VenvPath)) {
    Write-Message "Creating virtual environment in '$VenvPath'..."
    try {
        python -m venv $VenvName
        Write-Message "Virtual environment created." -Type SUCCESS
    }
    catch {
        Write-Message "Error creating virtual environment: $($_.Exception.Message)" -Type ERROR
        Write-Message "Ensure 'venv' module is available for your Python installation." -Type ERROR
        exit 1
    }
} else {
    Write-Message "Virtual environment directory '$VenvName' already exists. Using existing." -Type INFO
}

Write-Message "Virtual environment setup completed. Will use '$PipExecutable' for installations."

# --- 4. Install Dependencies ---
Write-Message "4. Installing MetaGPT and development dependencies..."
Write-Message "This may take a few minutes."
$InstallCommand = "& `"$PipExecutable`" install -e .[dev]"
Write-Message "Running command: $InstallCommand"
try {
    Invoke-Expression $InstallCommand
    Write-Message "MetaGPT and dependencies installed successfully." -Type SUCCESS
}
catch {
    Write-Message "Error installing dependencies: $($_.Exception.Message)" -Type ERROR
    Write-Message "Please check the output above for details. Ensure your network connection is stable and try running the command manually in the activated venv: $activateScript then `pip install -e .[dev]`" -Type ERROR
    exit 1
}

# --- 5. Node.js and pnpm Installation Guidance ---
Write-Message "5. Node.js and pnpm (Optional but Recommended)" -Type INFO
Write-Message "-----------------------------------------------------"
Write-Message "For full functionality, including certain diagramming features and mermaid support, MetaGPT uses Node.js and pnpm."
Write-Message "Please install them manually if you haven't already:"
Write-Message "  - Node.js (LTS recommended): https://nodejs.org/"
Write-Message "  - pnpm (after installing Node.js, via npm): npm install -g pnpm (Run this in a new PowerShell/CMD window after Node.js installation)"
Write-Message "    pnpm installation guide: https://pnpm.io/installation#using-npm"
Write-Message "-----------------------------------------------------"

# --- 6. Initialize MetaGPT Configuration ---
Write-Message "6. Initializing MetaGPT configuration..."
$MetaGPTExecutable = Join-Path -Path $VenvPath -ChildPath "Scripts\metagpt.exe"
$InitConfigCommand = "& `"$MetaGPTExecutable`" --init-config"
Write-Message "Running command: $InitConfigCommand"
try {
    Invoke-Expression $InitConfigCommand
    Write-Message "MetaGPT configuration initialized." -Type SUCCESS
}
catch {
    Write-Message "Error initializing MetaGPT configuration: $($_.Exception.Message)" -Type ERROR
    Write-Message "This can sometimes happen if there was an issue with the installation or PATH." -Type ERROR
    Write-Message "Try activating the environment manually (.\$VenvName\Scripts\Activate.ps1) and running 'metagpt --init-config'." -Type ERROR
    # It's not critical to exit here, user can do it manually.
}

# --- 7. Configuration File Editing Prompt ---
Write-Message "7. Configure MetaGPT" -Type INFO
Write-Message "-----------------------------------------------------"
$ConfigPath = Join-Path -Path $HOME -ChildPath ".metagpt\config2.yaml"
Write-Message "The MetaGPT configuration file is typically located at: $ConfigPath"
Write-Message "Please open this file with a text editor and add your LLM API keys (e.g., OPENAI_API_KEY)."
Write-Message "You may also want to configure other settings like your preferred LLM model."
Write-Message "Example for OpenAI:"
Write-Message "  llm:"
Write-Message "    api_type: openai"
Write-Message "    model: gpt-4-turbo-preview"
Write-Message "    base_url: https://api.openai.com/v1"
Write-Message "    api_key: YOUR_API_KEY_HERE"
Write-Message "-----------------------------------------------------"

Write-Message "Installation and basic setup complete!" -Type SUCCESS
Write-Message "To start using MetaGPT:"
Write-Message "1. Activate the virtual environment: `cd $RepoName` (if not already there) then `.\$VenvName\Scripts\Activate.ps1`"
Write-Message "2. Run MetaGPT: `metagpt ""Your requirement text""`"
Write-Message "Happy coding!"

# End of script
Set-Location .. # Go back to the parent directory from MetaGPT
Write-Message "Changed current directory back to $(Get-Location)."
