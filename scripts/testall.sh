cd ..
rm -rf venv
set -e

echo "--- Install requirements ---"
python3 -m venv venv
./venv/bin/python -m pip install --upgrade pip
./venv/bin/python -m pip install -r requirements.txt
./venv/bin/python -m pip install flake8

echo "--- Run all tests ---"
./venv/bin/python -m unittest discover -v

echo "--- Check flake8 ---"
./venv/bin/python -m flake8 .

echo "--- Done ---"
