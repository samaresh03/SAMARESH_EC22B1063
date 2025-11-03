# Push project to GitHub

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Push to GitHub - Quant Trading Dashboard" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Navigate to project folder
Set-Location "c:\Users\samar\Downloads\GEMSCAP\quant-trading-dashboard"

Write-Host "Initializing git repository..." -ForegroundColor Yellow
git init

Write-Host ""
Write-Host "Adding all files..." -ForegroundColor Yellow
git add .

Write-Host ""
Write-Host "Creating initial commit..." -ForegroundColor Yellow
git commit -m "Quant Trading Dashboard - Production Ready"

Write-Host ""
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "IMPORTANT: Create GitHub Repository First" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Go to https://github.com/new" -ForegroundColor White
Write-Host "2. Create a new repository named: quant-trading-dashboard" -ForegroundColor White
Write-Host "3. Keep it PUBLIC" -ForegroundColor White
Write-Host "4. Do NOT initialize with README" -ForegroundColor White
Write-Host "5. Click 'Create repository'" -ForegroundColor White
Write-Host ""
Write-Host "Then come back and continue!" -ForegroundColor Yellow
Write-Host ""
Read-Host "Press Enter to continue"

Write-Host ""
$username = "SAMARESH_EC22B1063"
Write-Host "Using GitHub username: $username" -ForegroundColor Green

Write-Host ""
Write-Host "Adding remote repository..." -ForegroundColor Yellow
git remote add origin "https://github.com/$username/SAMARESH_EC22B1063.git"

Write-Host ""
Write-Host "Renaming branch to main..." -ForegroundColor Yellow
git branch -M main

Write-Host ""
Write-Host "Pushing to GitHub..." -ForegroundColor Yellow
git push -u origin main

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Success! Project pushed to GitHub!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Your repository: https://github.com/$username/quant-trading-dashboard" -ForegroundColor Cyan
Write-Host ""
