# PowerShell script to fetch all backend source files from GitHub repo
# using gh api

$repo = "repos/YogendraChukka01/AdaptiveAgent"
$ref = "main"
$baseDir = "C:\Users\yogen\AdaptiveAgent"

# Function to download a file from GitHub contents API and save it
function Download-GitHubFile {
    param(
        [string]$Path,
        [string]$Repo = $repo,
        [string]$Ref = $ref,
        [string]$BaseDir = $baseDir
    )

    $localPath = Join-Path $BaseDir $Path
    $parentDir = Split-Path $localPath -Parent

    # Create parent directory if it doesn't exist
    if (-not (Test-Path $parentDir)) {
        New-Item -ItemType Directory -Path $parentDir -Force | Out-Null
    }

    # Download content via gh api - content comes back as array of lines, join them
    $content = gh api "$Repo/contents/$Path?ref=$Ref" --jq '.content'
    if ($null -eq $content -or $content -eq '') {
        Write-Warning "Failed to download: $Path (empty content)"
        return $false
    }

    $base64 = $content -join ''
    try {
        $decoded = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($base64))
        Set-Content -Path $localPath -Value $decoded -Encoding UTF8
        Write-Host "Downloaded: $Path"
        return $true
    } catch {
        Write-Warning "Failed to decode: $Path - $($_.Exception.Message)"
        return $false
    }
}

# Get the full tree
$tree = gh api "$repo/git/trees/$ref?recursive=1" --jq '.tree[].path'

# Filter for .py files under backend/app/
$pyFiles = $tree | Where-Object { $_ -like 'backend/app/*.py' }

Write-Host "Found $($pyFiles.Count) .py files under backend/app/"
Write-Host "============================================="

# Download each .py file
$successCount = 0
$failCount = 0
foreach ($file in $pyFiles) {
    if (Download-GitHubFile -Path $file) {
        $successCount++
    } else {
        $failCount++
    }
}

Write-Host "============================================="
Write-Host "Py files: $successCount downloaded, $failCount failed"

# Download additional files
$additionalFiles = @(
    "backend/pyproject.toml",
    "backend/.env.example",
    "backend/run.py",
    ".github/workflows/ci.yml"
)

foreach ($file in $additionalFiles) {
    if (Download-GitHubFile -Path $file) {
        $successCount++
    } else {
        $failCount++
    }
}

Write-Host "============================================="
Write-Host "Total: $successCount downloaded, $failCount failed"
