<#
.SYNOPSIS
    Opens the MetaGPT configuration file for editing.
.DESCRIPTION
    This script locates the MetaGPT configuration file (config2.yaml)
    and opens it in the default text editor. It also reminds the user
    to save their changes.
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

# --- 1. Locate Configuration File ---
Write-Message "Locating MetaGPT configuration file..."
$ConfigFileName = "config2.yaml"
$MetaGPTConfigDir = Join-Path -Path $HOME -ChildPath ".metagpt"
$ConfigFilePath = Join-Path -Path $MetaGPTConfigDir -ChildPath $ConfigFileName

Write-Message "Expected configuration file path: $ConfigFilePath"

if (-not (Test-Path $ConfigFilePath)) {
    Write-Message "MetaGPT configuration file ('$ConfigFilePath') not found." -Type ERROR
    Write-Message "Please ensure MetaGPT has been installed and initialized correctly." -Type ERROR
    Write-Message "You might need to run the installation script or 'metagpt --init-config' if you installed manually." -Type ERROR
    exit 1
} else {
    Write-Message "Configuration file found." -Type SUCCESS
}

# --- 2. Open Configuration File ---
Write-Message "Opening configuration file '$ConfigFilePath' in the default editor..."
try {
    Invoke-Item $ConfigFilePath
    Write-Message "The configuration file should now be open." -Type SUCCESS
}
catch {
    Write-Message "Error opening configuration file: $($_.Exception.Message)" -Type ERROR
    Write-Message "Please try opening the file manually: $ConfigFilePath" -Type ERROR
    exit 1
}

# --- 3. User Reminder ---
Write-Message "-----------------------------------------------------" -Type INFO
Write-Message "REMINDER: Please save the file '$ConfigFileName' in your editor after making any changes." -Type INFO
Write-Message "-----------------------------------------------------"

Write-Message "Script finished."
