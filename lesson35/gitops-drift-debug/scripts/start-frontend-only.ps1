# Simple script to start just the frontend port-forward from Windows
# This uses WSL kubectl to access the kind cluster in WSL
# Run this in PowerShell and keep the window open

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Starting Frontend Dashboard Port-Forward" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check if port is already in use
$portCheck = netstat -ano | findstr ":3000"
if ($portCheck) {
    Write-Host "Warning: Port 3000 is already in use!" -ForegroundColor Yellow
    Write-Host "Stopping existing port-forwards..." -ForegroundColor Yellow
    Get-Process | Where-Object {$_.ProcessName -like "*kubectl*"} | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
}

Write-Host "Using WSL kubectl to connect to kind cluster..." -ForegroundColor Green
Write-Host ""
Write-Host "Dashboard will be available at: http://localhost:3000" -ForegroundColor Yellow
Write-Host ""
Write-Host "IMPORTANT: Keep this window open!" -ForegroundColor Red
Write-Host "Press Ctrl+C to stop" -ForegroundColor Cyan
Write-Host ""
Write-Host "Starting port-forward..." -ForegroundColor Green
Write-Host ""

# Use WSL kubectl directly (this works because the cluster is in WSL)
wsl kubectl port-forward -n production svc/frontend 3000:80
