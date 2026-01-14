# PowerShell script to set up Windows port forwarding to WSL
# Run this in PowerShell as Administrator

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Windows Port Forwarding Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get WSL IP address
$wslIp = (wsl hostname -I).Split()[0]

if (-not $wslIp) {
    Write-Host "ERROR: Could not get WSL IP address" -ForegroundColor Red
    Write-Host "Make sure WSL is running" -ForegroundColor Yellow
    exit 1
}

Write-Host "WSL IP Address: $wslIp" -ForegroundColor Yellow
Write-Host ""

# Remove existing port forwards (if any)
Write-Host "Removing existing port forwards..." -ForegroundColor Yellow
netsh interface portproxy delete v4tov4 listenport=3000 listenaddress=0.0.0.0 2>$null
netsh interface portproxy delete v4tov4 listenport=8000 listenaddress=0.0.0.0 2>$null

# Add new port forwards
Write-Host "Setting up port forwarding..." -ForegroundColor Yellow
netsh interface portproxy add v4tov4 listenport=3000 listenaddress=0.0.0.0 connectport=3000 connectaddress=$wslIp
netsh interface portproxy add v4tov4 listenport=8000 listenaddress=0.0.0.0 connectport=8000 connectaddress=$wslIp

# Show current port forwards
Write-Host ""
Write-Host "Current port forwards:" -ForegroundColor Green
netsh interface portproxy show all

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "You can now access:" -ForegroundColor Yellow
Write-Host "  Dashboard: http://localhost:3000" -ForegroundColor Green
Write-Host "  API: http://localhost:8000" -ForegroundColor Green
Write-Host ""
