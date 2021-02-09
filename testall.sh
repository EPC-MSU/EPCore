rm -rf venv

set -e

python3.6 -m venv venv
./venv/bin/python -m pip install --upgrade pip
./venv/bin/python -m pip install -r requirements.txt

export PYTHONPATH=$(dirname "$0")

for f in epcore/*/
do
dir=${f%*/}
echo "Test $dir"
./venv/bin/python _test.py "$dir"
done;

./venv/bin/python -m pip install flake8
echo "Check flake8..."
./venv/bin/python -m flake8 .
echo "done"