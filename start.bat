@echo off
title Ejecutando Proyecto Django
cd /d "C:\Users\Sebastian Reyez\proyct"
call .venv\Scripts\activate
python manage.py runserver
pause