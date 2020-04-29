#### EyePoint architecture example

###### Installation:
<pre>
python setup.py install
</pre>
From repository:
<pre>
python -m pip install -e hg+https://hg.ximc.ru/eyepoint/epcore@452b3cce7667#egg=epcore
</pre>

###### Run module example (epcore must be installed):
<pre>
python -m epcore.filemanager
</pre>

###### Run module tests:
<pre>
pytest epcore/filemanager/tests/*
</pre>

###### Add ur own submodule to epcore:

_do it like other existing submodules_

###### Add package dependency (like: numpy, simpleaudio, etc) 

In setup.py:
<pre>
    install_requires=[
        "numpy",  # for pin module
        "simpleaudio"  # for sound module
    ],
</pre>

Add package binary dependency:

_look at "sound" subpackage example_

In setup.py:
<pre>
    package_data={
        'epcore.sound': ['sound/foo.so']  # for sound module
    }
</pre>