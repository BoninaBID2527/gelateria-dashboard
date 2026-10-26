@echo off
REM Rigenera i dati, controlla che i calcoli siano giusti e ricrea la dashboard.
python genera_dati.py
python -m unittest discover
python crea_dashboard.py
start dashboard.html
