@echo off
setlocal EnableDelayedExpansion
if exist venv  rd /S /Q venv
python -m venv venv
venv\Scripts\python -m pip install --upgrade pip
venv\Scripts\python -m pip install -r requirements.txt --upgrade
venv\Scripts\python -m pip install flake8
echo --- Run all tests ---
for /D %%f in (epcore\*) do (
echo Test %%f
venv\Scripts\python _test.py %%f
)

echo --- Check flake8 ---
venv\Scripts\python -m flake8 .

echo --- Done ---
pause