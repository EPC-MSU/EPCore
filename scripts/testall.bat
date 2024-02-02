cd ..
setlocal EnableDelayedExpansion

echo --- Install requirements ---
if exist venv  rd /S /Q venv
python -m venv venv
venv\Scripts\python -m pip install --upgrade pip
venv\Scripts\python -m pip install -r requirements.txt
venv\Scripts\python -m pip install flake8

echo --- Run all tests ---
venv\Scripts\python -m unittest discover -v

echo --- Check flake8 ---
venv\Scripts\python -m flake8 .

echo --- Done ---
pause