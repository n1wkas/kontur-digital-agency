@echo off
chcp 65001 >nul
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Не найдено виртуальное окружение .venv.
    echo Создайте его командами:
    echo   python -m venv .venv
    echo   .venv\Scripts\python.exe -m pip install -r requirements.txt
    pause
    exit /b 1
)

echo Запускаю сайт: http://127.0.0.1:5000
echo Админка:      http://127.0.0.1:5000/admin
echo Остановить:   Ctrl+C в этом окне
echo.

start "" cmd /c "timeout /t 3 >nul & start "" http://127.0.0.1:5000"
".venv\Scripts\python.exe" run.py

pause
