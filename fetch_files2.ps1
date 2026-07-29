# PowerShell script to download all backend source files
# Reads tree from file, then downloads each .py file and additional files

$baseDir = "C:\Users\yogen\AdaptiveAgent"
$treeFile = Join-Path $baseDir "tree_paths.txt"

# Read tree paths from file
$tree = Get-Content $treeFile

# Filter for .py files under backend/app/
$pyFiles = $tree | Where-Object { $_ -like 'backend/app/*.py' }

Write-Host "Found $($pyFiles.Count) .py files under backend/app/"
Write-Host "============================================="

# Function to download a file from GitHub contents API and save it
function Download-GitHubFile {
    param([string]$Path)

    $localPath = Join-Path $baseDir $Path
    $parentDir = Split-Path $localPath -Parent

    # Create parent directory if it doesn't exist
    if (-not (Test-Path $parentDir)) {
        New-Item -ItemType Directory -Path $parentDir -Force | Out-Null
    }

    # Download content via gh api - content comes back as array of lines, join them
    $content = gh api "repos/YogendraChukka01/AdaptiveAgent/contents/$Path?ref=main" --jq '.content' 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Failed to download: $Path (exit code $LASTEXITCODE)"
        Write-Host "  Error: $content"
        return $false
    }

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
