@echo off
REM Push project to GitHub

echo.
echo ========================================
echo Push to GitHub - Quant Trading Dashboard
echo ========================================
echo.

REM Navigate to project folder
cd /d c:\Users\samar\Downloads\GEMSCAP\quant-trading-dashboard

echo Initializing git repository...
git init

echo.
echo Adding all files...
git add .

echo.
echo Creating initial commit...
git commit -m "Quant Trading Dashboard - Production Ready"

echo.
echo.
echo ========================================
echo IMPORTANT: Create GitHub Repository First
echo ========================================
echo.
echo 1. Go to https://github.com/new
echo 2. Create a new repository named: quant-trading-dashboard
echo 3. Keep it PUBLIC
echo 4. Do NOT initialize with README
echo 5. Click "Create repository"
echo.
echo Then come back and run this script again!
echo.
pause

echo.
echo Using GitHub username: SAMARESH_EC22B1063
set username=SAMARESH_EC22B1063

echo.
echo Adding remote repository...
git remote add origin https://github.com/%username%/SAMARESH_EC22B1063.git

echo.
echo Renaming branch to main...
git branch -M main

echo.
echo Pushing to GitHub...
git push -u origin main

echo.
echo ========================================
echo Success! Project pushed to GitHub!
echo ========================================
echo.
echo Your repository: https://github.com/%username%/quant-trading-dashboard
echo.
pause
