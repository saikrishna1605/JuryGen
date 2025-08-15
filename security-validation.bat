@echo off
echo 🔐 SECURITY VALIDATION - Checking for sensitive files...
echo.

set "SECURITY_PASSED=true"

echo 📋 Checking for sensitive files that should NOT be committed:
echo.

if exist "backend\.env" (
    echo ❌ CRITICAL: backend\.env contains secrets and MUST be removed!
    set "SECURITY_PASSED=false"
) else (
    echo ✅ backend\.env - Not found (good)
)

if exist "frontend\.env" (
    echo ❌ CRITICAL: frontend\.env contains secrets and MUST be removed!
    set "SECURITY_PASSED=false"
) else (
    echo ✅ frontend\.env - Not found (good)
)

if exist "backend\service-account.json" (
    echo ❌ CRITICAL: service-account.json contains secrets and MUST be removed!
    set "SECURITY_PASSED=false"
) else (
    echo ✅ service-account.json - Not found (good)
)

echo.
echo 📝 Checking for template files that SHOULD exist:
echo.

if exist "backend\.env.example" (
    echo ✅ backend\.env.example - Found (good)
) else (
    echo ❌ WARNING: backend\.env.example missing - users need this template!
)

if exist "frontend\.env.example" (
    echo ✅ frontend\.env.example - Found (good)
) else (
    echo ❌ WARNING: frontend\.env.example missing - users need this template!
)

if exist "backend\service-account.json.example" (
    echo ✅ service-account.json.example - Found (good)
) else (
    echo ❌ WARNING: service-account.json.example missing - users need this template!
)

echo.
echo 🔍 Checking .gitignore coverage:
echo.

findstr /C:".env" .gitignore >nul
if %errorlevel%==0 (
    echo ✅ .env files are ignored by Git
) else (
    echo ❌ CRITICAL: .env files not properly ignored!
    set "SECURITY_PASSED=false"
)

findstr /C:"service-account.json" .gitignore >nul
if %errorlevel%==0 (
    echo ✅ service-account.json is ignored by Git
) else (
    echo ❌ CRITICAL: service-account.json not properly ignored!
    set "SECURITY_PASSED=false"
)

echo.
echo 🔍 Scanning for hardcoded secrets in files:
echo.

:: Check for potential API keys in documentation
findstr /R /C:"AIza[0-9A-Za-z_-]*" *.md >nul 2>&1
if %errorlevel%==0 (
    echo ❌ CRITICAL: Google API key found in documentation!
    findstr /R /C:"AIza[0-9A-Za-z_-]*" *.md
    set "SECURITY_PASSED=false"
) else (
    echo ✅ No Google API keys found in documentation
)

:: Check for Firebase project IDs
findstr /R /C:"kiro-hackathon" *.md *.bat >nul 2>&1
if %errorlevel%==0 (
    echo ❌ WARNING: Hardcoded project references found:
    findstr /R /C:"kiro-hackathon" *.md *.bat
    echo Please replace with placeholders like [YOUR-PROJECT-ID]
) else (
    echo ✅ No hardcoded project references found
)

echo.
echo 📊 SECURITY VALIDATION SUMMARY:
echo ================================

if "%SECURITY_PASSED%"=="true" (
    echo ✅ SECURITY CHECK PASSED - SAFE TO PUSH TO GITHUB!
    echo.
    echo 🛡️ All sensitive files are properly protected:
    echo   • No .env files with real secrets
    echo   • No service account JSON with real credentials  
    echo   • All sensitive patterns are in .gitignore
    echo   • Template files are available for users
    echo.
    echo 🚀 Ready for GitHub push!
) else (
    echo ❌ SECURITY CHECK FAILED - DO NOT PUSH TO GITHUB!
    echo.
    echo 🚨 Critical issues found that must be fixed first.
    echo Please resolve all CRITICAL issues above before pushing.
    echo.
    echo 🔧 To fix issues:
    echo   1. Delete any .env files with real secrets
    echo   2. Delete any service-account.json files with real credentials
    echo   3. Update .gitignore to ignore sensitive files
    echo   4. Replace hardcoded values with placeholders
    echo.
)

echo.
pause