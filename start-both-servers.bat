@echo off
echo Starting Legal Companion Servers...
echo =====================================

echo.
echo Starting Backend Server...
start "Backend Server" cmd /k "cd backend && python start_server_simple.py"

echo.
echo Waiting 3 seconds for backend to start...
timeout /t 3 /nobreak > nul

echo.
echo Starting Frontend Server...
start "Frontend Server" cmd /k "cd frontend && npm run dev"

echo.
echo =====================================
echo Both servers are starting!
echo.
echo Backend:  http://127.0.0.1:8000
echo Frontend: http://localhost:5173
echo API Docs: http://127.0.0.1:8000/docs
echo.
echo Press any key to exit this window...
pause > nul