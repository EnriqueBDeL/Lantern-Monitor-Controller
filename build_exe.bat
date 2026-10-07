@echo off
cd /d "%~dp0"
echo === Creando entorno e instalando dependencias ===
py -3 -m venv .venv || goto :err
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip || goto :err
pip install -r requirements.txt pyinstaller || goto :err
echo === Generando el .exe ===
pyinstaller --noconfirm --clean Lantern.spec || goto :err
echo.
echo Listo: dist\Lantern.exe
pause
exit /b 0
:err
echo.
echo Ha fallado la compilacion. Revisa los mensajes de arriba.
pause
exit /b 1
