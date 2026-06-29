@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo === DoMySubs - העלאה ל-GitHub ===
echo.

set "GH=gh"
where gh >nul 2>&1
if errorlevel 1 (
    if exist "%ProgramFiles%\GitHub CLI\gh.exe" (
        set "GH=%ProgramFiles%\GitHub CLI\gh.exe"
    ) else (
        echo [שגיאה] GitHub CLI לא מותקן.
        echo התקן: winget install GitHub.cli
        echo ואז סגור ופתח מחדש את PowerShell.
        pause
        exit /b 1
    )
)

"%GH%" auth status >nul 2>&1
if errorlevel 1 (
    echo התחבר ל-GitHub...
    "%GH%" auth login
)

git status >nul 2>&1
if errorlevel 1 (
    echo [שגיאה] תיקייה זו אינה repo של git
    pause
    exit /b 1
)

set /p MSG="הודעת commit (Enter = עדכון): "
if "%MSG%"=="" set MSG=עדכון פרויקט

git add .
git status
git commit -m "%MSG%" 2>nul
if errorlevel 1 echo [מידע] אין שינויים חדשים ל-commit

git remote get-url origin >nul 2>&1
if errorlevel 1 (
    echo.
    echo יוצר repo חדש ב-GitHub...
    git branch -M main
    "%GH%" repo create DoMySubs --public --source=. --remote=origin --push
) else (
    git push
)

echo.
echo === הושלם ===
pause
