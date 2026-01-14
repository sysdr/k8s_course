# ✅ Windows Access Fix - Connection Refused

## Problem
Windows browser shows "ERR_CONNECTION_REFUSED" when accessing `localhost:3000` or `localhost:8000` even though services are running in WSL.

## Solution

### Option 1: Use WSL IP Address (Easiest)

Instead of `localhost`, use the WSL IP address directly:

- **Dashboard:** http://172.17.32.19:3000
- **API:** http://172.17.32.19:8000

### Option 2: Set Up Windows Port Forwarding (Recommended)

This allows you to use `localhost` from Windows.

#### Step 1: Open PowerShell as Administrator
1. Press `Win + X`
2. Select "Windows PowerShell (Admin)" or "Terminal (Admin)"

#### Step 2: Run the Setup Script
```powershell
cd C:\Users\YourUsername\path\to\break-it-friday-stateful\scripts
.\setup-windows-port-forward.ps1
```

#### Step 3: Or Run Commands Manually
```powershell
# Get WSL IP (run in WSL first: hostname -I)
$wslIp = "172.17.32.19"  # Replace with your WSL IP

# Set up port forwarding
netsh interface portproxy add v4tov4 listenport=3000 listenaddress=0.0.0.0 connectport=3000 connectaddress=$wslIp
netsh interface portproxy add v4tov4 listenport=8000 listenaddress=0.0.0.0 connectport=8000 connectaddress=$wslIp
```

#### Step 4: Verify
```powershell
netsh interface portproxy show all
```

### Option 3: Check Windows Firewall

If port forwarding doesn't work, check Windows Firewall:

1. Open Windows Defender Firewall
2. Click "Advanced settings"
3. Check if ports 3000 and 8000 are allowed
4. If not, create inbound rules for these ports

## Quick Check Commands

### Verify Services Are Running (in WSL)
```bash
cd break-it-friday-stateful/scripts
./check-access.sh
```

### Restart Services (in WSL)
```bash
cd break-it-friday-stateful/scripts
./start-simple.sh
```

### Get WSL IP Address
```bash
hostname -I | awk '{print $1}'
```

## Current Status

✅ **Services are running:**
- API: Port 8000 (accessible in WSL)
- Frontend: Port 3000 (accessible in WSL)

✅ **WSL IP:** 172.17.32.19

## Access URLs

**From Windows Browser:**
- Try: http://localhost:3000 (if port forwarding is set up)
- Or: http://172.17.32.19:3000 (direct WSL IP)

**From WSL:**
- http://localhost:3000 (always works)

## Troubleshooting

### If localhost still doesn't work:
1. Make sure you ran PowerShell as Administrator
2. Check port forwarding: `netsh interface portproxy show all`
3. Try the WSL IP directly: http://172.17.32.19:3000
4. Check Windows Firewall settings

### If WSL IP doesn't work:
1. Verify services are running: `./check-access.sh`
2. Check WSL IP hasn't changed: `hostname -I`
3. Restart services: `./start-simple.sh`

## Remove Port Forwarding (if needed)

```powershell
netsh interface portproxy delete v4tov4 listenport=3000 listenaddress=0.0.0.0
netsh interface portproxy delete v4tov4 listenport=8000 listenaddress=0.0.0.0
```

## Summary

**Quick Fix:** Use http://172.17.32.19:3000 instead of localhost

**Permanent Fix:** Set up Windows port forwarding using the PowerShell script
