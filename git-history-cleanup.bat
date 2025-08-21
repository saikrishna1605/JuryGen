@echo off
echo 🧹 Git History Cleanup - Remove Sensitive Data
echo.
echo ⚠️  WARNING: This will rewrite Git history!
echo    Make sure all team members are aware before proceeding.
echo.
echo 🔍 This script will remove the following from Git history:
echo    - frontend/.env (contained real API keys)
echo    - backend/.env (contained potential secrets)
echo    - Any other .env files
echo.

set /p confirm="Are you sure you want to proceed? (y/N): "
if /i not "%confirm%"=="y" (
    echo ❌ Operation cancelled.
    pause
    exit /b 0
)

echo.
echo 🧹 Removing sensitive files from Git history...
echo.

echo 📝 Step 1: Remove frontend/.env from history...
git filter-branch --force --index-filter "git rm --cached --ignore-unmatch frontend/.env" --prune-empty --tag-name-filter cat -- --all

echo 📝 Step 2: Remove backend/.env from history...
git filter-branch --force --index-filter "git rm --cached --ignore-unmatch backend/.env" --prune-empty --tag-name-filter cat -- --all

echo 📝 Step 3: Remove any other .env files...
git filter-branch --force --index-filter "git rm --cached --ignore-unmatch *.env" --prune-empty --tag-name-filter cat -- --all

echo 📝 Step 4: Clean up backup refs...
git for-each-ref --format="delete %(refname)" refs/original | git update-ref --stdin

echo 📝 Step 5: Expire reflog and garbage collect...
git reflog expire --expire=now --all
git gc --prune=now --aggressive

echo.
echo ✅ Git history cleanup complete!
echo.
echo 🚀 Next steps:
echo 1. Force push to update remote repository:
echo    git push origin --force --all
echo.
echo 2. All team members must re-clone the repository:
echo    git clone https://github.com/saikrishna1605/JuryGen.git
echo.
echo ⚠️  IMPORTANT: Coordinate with your team before force pushing!
echo.
pause