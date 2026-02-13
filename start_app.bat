@echo off
chcp 65001 > nul
echo ===================================================
echo ❤️  Запускаем программу отправки PDF с любовью!  ❤️
echo ===================================================

echo.
echo [1/3] Проверяем Python...
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo Python не найден! Пожалуйста, установите Python 3.12 с python.org
    pause
    exit /b
)

echo.
echo [2/3] Устанавливаем необходимые библиотеки...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Ошибка при установке библиотек. Проверьте интернет соединение.
    pause
    exit /b
)

echo.
echo [3/3] Все готово! Запускаем сервер...
echo.
echo Сейчас появится ссылка с IP адресом.
echo Введите её в браузере телефона или отсканируйте QR-код.
echo Чтобы остановить сервер, нажмите Ctrl + C в этом окне.
echo.
python app.py

pause
