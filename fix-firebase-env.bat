@echo off
echo ========================================
echo Firebase Environment Variables Fix
echo ========================================
echo.

echo 1. Checking .env file location...
if exist "frontend\.env" (
    echo ✅ Found frontend\.env file
) else (
    echo ❌ Missing frontend\.env file
    echo Creating from example...
    copy "frontend\.env.example" "frontend\.env"
)

echo.
echo 2. Checking .env file content...
findstr "VITE_FIREBASE_API_KEY" frontend\.env >nul
if %errorlevel%==0 (
    echo ✅ Firebase API key found in .env
) else (
    echo ❌ Firebase API key missing from .env
)

echo.
echo 3. Clearing Node.js cache...
cd frontend
if exist "node_modules\.cache" (
    rmdir /s /q "node_modules\.cache"
    echo ✅ Cleared Vite cache
)

echo.
echo 4. Restarting development server...
echo Stopping any existing processes...
taskkill /f /im node.exe 2>nul

echo.
echo Starting fresh development server...
echo Run this command manually: npm run dev
echo.
echo ========================================
echo If the issue persists:
echo 1. Close all browser tabs
echo 2. Clear browser cache
echo 3. Run: npm run dev
echo ========================================
pause