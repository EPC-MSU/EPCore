rm -rf venv

set -e

python3.6 -m venv venv
./venv/bin/python -m pip install -r requirements.txt

export PYTHONPATH=/home/walker/Projects/epcore

for f in epcore/*
do
echo "Test $f"
./venv/bin/python _test.py "$f"
done;