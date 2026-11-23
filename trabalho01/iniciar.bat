@echo off
setlocal

cd /d "%~dp0"
title Petala Livraria

if not exist "venv\Scripts\python.exe" (
    echo Criando o ambiente virtual...
    where py >nul 2>nul
    if %errorlevel% equ 0 (
        py -3 -m venv venv
    ) else (
        python -m venv venv
    )
    if errorlevel 1 (
        echo.
        echo Nao foi possivel criar o ambiente virtual.
        echo Instale o Python e tente novamente.
        pause
        exit /b 1
    )
)

echo Instalando ou atualizando as dependencias...
venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo Nao foi possivel instalar as dependencias.
    pause
    exit /b 1
)

echo Aplicando as migracoes do banco...
venv\Scripts\python.exe manage.py migrate
if errorlevel 1 (
    echo.
    echo Nao foi possivel aplicar as migracoes.
    pause
    exit /b 1
)

echo.
echo Iniciando a Petala Livraria em http://127.0.0.1:8000/
echo Pressione CTRL+C para encerrar o servidor.
echo.
venv\Scripts\python.exe manage.py runserver

pause
