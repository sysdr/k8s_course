@echo off
echo ==========================================
echo Starting Frontend Dashboard
echo ==========================================
echo.
echo This will start the port-forward to access the dashboard.
echo Keep this window open while using the dashboard!
echo.
echo Dashboard URL: http://localhost:3000
echo.
echo Press Ctrl+C to stop
echo.
echo Starting...
echo.

wsl kubectl port-forward -n production svc/frontend 3000:80

pause
