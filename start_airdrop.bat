@echo off
chcp 65001 > nul
echo ===================================================
echo ☁️  Запускаем AirDrop PDF Receiver...  ☁️
echo ===================================================

echo.
echo [1/2] Проверяем библиотеки...
pip install -r requirements.txt > nul 2>&1
if %errorlevel% neq 0 (
    echo Установка библиотек...
    pip install -r requirements.txt
)

echo.
echo [2/2] Запускаем интерфейс...
python gui_app.py

pause
