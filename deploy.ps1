# HumanThinking Plugin - One-Click Deploy Script
# Usage: .\deploy.ps1

param(
    [string]$ServerIP = "192.168.10.132",
    [string]$ServerUser = "root",
    [string]$SSHKey = "$env:USERPROFILE\.ssh\humthink"
)

$ProjectDir = "e:\项目\Human Thinking Tools\humThink\HumanThinking"
$TempArchive = "$env:TEMP\humthink_deploy.tar.gz"

$PluginDir = "/root/.qwenpaw/plugins/HumanThinking"
$VenvDir = "/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/agents/tools/HumanThinking"

Write-Host "=== HumanThinking Plugin Deploy ===" -ForegroundColor Cyan

# Step 1: Package project
Write-Host "[1/5] Packaging project..." -ForegroundColor Yellow
Push-Location $ProjectDir
try {
    tar -czf $TempArchive `
        --exclude='.git' `
        --exclude='*.md' `
        --exclude='tests' `
        --exclude='.trae' `
        --exclude='tmp_*' `
        --exclude='__pycache__' `
        --exclude='*.pyc' `
        -C "$ProjectDir" .
    Write-Host "  Package created: $TempArchive" -ForegroundColor Green
} finally {
    Pop-Location
}

# Step 2: Upload
Write-Host "[2/5] Uploading to server..." -ForegroundColor Yellow
scp -i $SSHKey -o StrictHostKeyChecking=no $TempArchive ${ServerUser}@${ServerIP}:/tmp/humthink_deploy.tar.gz
Write-Host "  Upload complete" -ForegroundColor Green

# Step 3: Install on server
Write-Host "[3/5] Installing on server..." -ForegroundColor Yellow
$InstallCmd = @"
set -e
echo '=== Shutting down QwenPaw ==='
/root/.qwenpaw/bin/qwenpaw shutdown 2>/dev/null || true
sleep 3

echo '=== Extracting to plugin dir ==='
mkdir -p $PluginDir
tar -xzf /tmp/humthink_deploy.tar.gz -C $PluginDir

echo '=== Syncing to venv site-packages ==='
mkdir -p $VenvDir
rsync -a --delete $PluginDir/ $VenvDir/

echo '=== Clearing Python cache ==='
find $VenvDir -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
find $VenvDir -name '*.pyc' -delete 2>/dev/null || true

echo '=== Cleaning up ==='
rm -f /tmp/humthink_deploy.tar.gz

echo '=== Installation complete ==='
"@
ssh -i $SSHKey -o StrictHostKeyChecking=no ${ServerUser}@${ServerIP} "bash -c '$InstallCmd'"
Write-Host "  Install complete" -ForegroundColor Green

# Step 4: Start QwenPaw (first time)
Write-Host "[4/5] Starting QwenPaw (1st restart)..." -ForegroundColor Yellow
ssh -i $SSHKey -o StrictHostKeyChecking=no ${ServerUser}@${ServerIP} `
    "cd /root/.qwenpaw && nohup ./venv/bin/qwenpaw app --host 0.0.0.0 --port 8088 > /tmp/qw_deploy.log 2>&1 & echo 'PID='`$!"
Write-Host "  QwenPaw starting (waiting 15s)..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

# Step 5: Second restart (QwenPaw requires double restart to load plugins)
Write-Host "[5/5] Second restart for full plugin load..." -ForegroundColor Yellow
ssh -i $SSHKey -o StrictHostKeyChecking=no ${ServerUser}@${ServerIP} "/root/.qwenpaw/bin/qwenpaw shutdown"
Start-Sleep -Seconds 5
ssh -i $SSHKey -o StrictHostKeyChecking=no ${ServerUser}@${ServerIP} `
    "cd /root/.qwenpaw && nohup ./venv/bin/qwenpaw app --host 0.0.0.0 --port 8088 > /tmp/qw_deploy2.log 2>&1 & echo 'PID='`$!"

Write-Host ""
Write-Host "=== Deploy Complete ===" -ForegroundColor Green
Write-Host "Server: http://${ServerIP}:8088" -ForegroundColor Cyan
Write-Host ""
Write-Host "Wait 30s, then verify:" -ForegroundColor Yellow
Write-Host "  ssh ${ServerUser}@${ServerIP} 'grep -i \"started successfully\|rebuild\|auto_memory\" /root/.qwenpaw/qwenpaw.log | tail -5'" -ForegroundColor Gray

# Cleanup local temp
Remove-Item $TempArchive -ErrorAction SilentlyContinue