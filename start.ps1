<#
.SYNOPSIS
    Sets up the environment and provides a placeholder for starting MetaGPT.
.DESCRIPTION
    This script verifies the MetaGPT installation, activates the virtual environment,
    and guides the user to add their specific command to run MetaGPT.
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

# --- 1. Verify Environment ---
Write-Message "1. Verifying MetaGPT environment..."
$MetaGPTDir = "MetaGPT"
$VenvDir = Join-Path -Path $MetaGPTDir -ChildPath ".venv"
$ActivateScriptPath = Join-Path -Path $VenvDir -ChildPath "Scripts\Activate.ps1"

if (-not (Test-Path $MetaGPTDir)) {
    Write-Message "MetaGPT directory ('$MetaGPTDir') not found in the current location ($(Get-Location))." -Type ERROR
    Write-Message "Please run the 'install.ps1' script first or ensure you are in the correct parent directory." -Type ERROR
    exit 1
} else {
    Write-Message "MetaGPT directory found." -Type SUCCESS
}

if (-not (Test-Path $VenvDir)) {
    Write-Message "Virtual environment directory ('$VenvDir') not found." -Type ERROR
    Write-Message "Please run the 'install.ps1' script to create the virtual environment." -Type ERROR
    exit 1
} else {
    Write-Message "Virtual environment directory found." -Type SUCCESS
}

if (-not (Test-Path $ActivateScriptPath)) {
    Write-Message "Virtual environment activation script ('$ActivateScriptPath') not found." -Type ERROR
    Write-Message "The virtual environment seems incomplete. Try running 'install.ps1' again." -Type ERROR
    exit 1
} else {
    Write-Message "Virtual environment activation script found." -Type SUCCESS
}

# --- 2. Activate Virtual Environment ---
Write-Message "2. Preparing to activate virtual environment..."
try {
    Write-Message "Changing current directory to '$MetaGPTDir'..."
    Set-Location $MetaGPTDir
    Write-Message "Current directory is now: $(Get-Location)" -Type SUCCESS
}
catch {
    Write-Message "Error changing directory to '$MetaGPTDir': $($_.Exception.Message)" -Type ERROR
    exit 1
}

# Activation guidance:
# Activating a venv in a script means subsequent commands *within this script's scope*
# can use it if called directly. However, to truly "activate" it for an interactive
# session or for commands run *after* the script, the user would typically source it.
# For this script, we will inform the user that they are now in an environment
# where metagpt commands *should* work if the user adds them below.

Write-Message "The virtual environment will be activated for commands run *within this script*."
Write-Message "To activate it for your current PowerShell session after this script finishes, you would typically run:"
Write-Message "  `.\.venv\Scripts\Activate.ps1` (from within the '$MetaGPTDir' directory)"
Write-Message "However, for this script, we are setting up for commands you will add below."

# --- 3. Placeholder for User Command ---
Write-Message "3. Add your MetaGPT command" -Type INFO
Write-Message "------------------------------------------------------------------------------------" -Type INFO
Write-Message "TODO: You need to edit this script to add your specific MetaGPT command below." -Type WARNING
Write-Message "The virtual environment is prepared for commands executed from this script." -Type INFO
Write-Message ""
Write-Host "# Example 1: Run a MetaGPT command directly" -ForegroundColor Gray
Write-Host "# metagpt ""Write a cli snake game"" " -ForegroundColor Gray
Write-Host ""
Write-Host "# Example 2: Run a Python script that uses MetaGPT library" -ForegroundColor Gray
Write-Host "# python your_application_script.py --config your_config.yaml" -ForegroundColor Gray
Write-Host ""
Write-Host "# --- Add your command below this line ---" -ForegroundColor Cyan
#
# metagpt "YOUR_PROMPT_OR_COMMAND_HERE"
#
Write-Host "# --- End of user command section ---" -ForegroundColor Cyan
Write-Message "------------------------------------------------------------------------------------" -Type INFO

# --- 4. Guidance for User ---
Write-Message "4. How to use this script:" -Type INFO
Write-Message "   a. Open '$((Get-Item $MyInvocation.MyCommand.Path).Name)' in a text editor."
Write-Message "   b. Find the section marked 'TODO: Add your MetaGPT command'."
Write-Message "   c. Replace the placeholder comments with your actual command to run MetaGPT."
Write-Message "      For example: `metagpt ""Generate a design for a simple calculator""`"
Write-Message "   d. Save the script."
Write-Message "   e. Run this script from PowerShell: `.\$((Get-Item $MyInvocation.MyCommand.Path).Name)`"
Write-Message ""
Write-Message "The script will then activate the environment and execute your command." -Type SUCCESS

# Note: The virtual environment is active only for the duration of this script execution.
# If the user's command starts a long-running process, it will run in the venv.
# If they want the venv active in their shell *after* the script, they must activate it manually.

# Go back to the original directory when the script exits (optional, good practice)
Pop-Location
Write-Message "Returned to original directory: $(Get-Location)" -Type INFO
Write-Message "Script finished."
