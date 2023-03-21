rm -rf venv
set -e

python3 -m venv venv
./venv/bin/python -m pip install --upgrade pip
./venv/bin/python -m pip install -r requirements.txt
./venv/bin/python -m pip install flake8

echo "--- Run all tests ---"
export PYTHONPATH=$(dirname "$0")
for f in epcore/*/
do
dir=${f%*/}
echo "Test $dir"
./venv/bin/python _test.py "$dir"
done;

echo "--- Check flake8 ---"
./venv/bin/python -m flake8 .

echo "--- Done ---"