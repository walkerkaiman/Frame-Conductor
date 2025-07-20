@echo off
REM Conductor Repository Cleanup Script
REM This script removes unwanted files from git tracking and commits the cleanup

echo 🧹 Cleaning up Conductor repository...
echo ======================================

REM Remove node_modules from tracking
echo 📦 Removing node_modules from tracking...
git rm -r --cached node_modules/ 2>nul || echo node_modules already removed

REM Remove frontend build artifacts
echo 🏗️  Removing frontend build artifacts...
git rm -r --cached frontend/dist/ 2>nul || echo frontend/dist already removed
git rm -r --cached frontend/node_modules/ 2>nul || echo frontend/node_modules already removed

REM Remove Python build artifacts
echo 🐍 Removing Python build artifacts...
git rm -r --cached __pycache__/ 2>nul || echo __pycache__ already removed
git rm -r --cached utils/__pycache__/ 2>nul || echo utils/__pycache__ already removed
git rm --cached "*.pyc" 2>nul || echo *.pyc files already removed
git rm --cached "*.pyo" 2>nul || echo *.pyo files already removed

REM Remove PyInstaller artifacts
echo 📦 Removing PyInstaller artifacts...
git rm --cached "*.spec" 2>nul || echo *.spec files already removed
git rm -r --cached build/ 2>nul || echo build/ already removed
git rm -r --cached dist/ 2>nul || echo dist/ already removed

REM Remove Electron build artifacts
echo ⚡ Removing Electron build artifacts...
git rm --cached "*.exe" 2>nul || echo *.exe files already removed
git rm --cached "*.dmg" 2>nul || echo *.dmg files already removed
git rm --cached "*.deb" 2>nul || echo *.deb files already removed
git rm --cached "*.AppImage" 2>nul || echo *.AppImage files already removed

REM Remove config files that shouldn't be tracked
echo ⚙️  Removing local config files...
git rm --cached sacn_sender_config.json 2>nul || echo sacn_sender_config.json already removed

REM Add the .gitignore file
echo 📝 Adding .gitignore...
git add .gitignore

REM Show what will be committed
echo.
echo 📋 Files to be committed:
git status --porcelain

REM Ask for confirmation
echo.
set /p confirm="Do you want to commit these changes? (y/N): "
if /i "%confirm%"=="y" (
    echo 💾 Committing cleanup...
    git commit -m "Clean up repository: remove build artifacts and add .gitignore
    
    - Removed node_modules from tracking
    - Removed frontend build artifacts
    - Removed Python build artifacts
    - Removed PyInstaller artifacts
    - Removed Electron build artifacts
    - Removed local config files
    - Added comprehensive .gitignore"
    
    echo ✅ Repository cleaned up successfully!
    echo.
    echo 📊 Repository size reduced significantly.
    echo 🚀 Ready for clean commits going forward.
) else (
    echo ❌ Cleanup cancelled. Files removed from tracking but not committed.
    echo Run 'git add . && git commit' manually if you want to commit the changes.
)

pause 