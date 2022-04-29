# epcore
epcore – это общий набор ключевых модулей, на базе которых строится различное ПО, работающее с сигнатурными анализаторами EyePoint.

_Все новые модули нужно делать по образцу существующих в этом проекте. Нужно соблюдать сходство именований и архитектуры папок._

## Тесты в Windows

Выполните команду:

```bash
testall.bat
```

## Тесты в Linux

Выполните команду

```bash
bash testall.sh
```

## Прочие инструкции

###### Запуск теста для одного модуля
```bash
python -m unittest discover epcore/filemanager
```

###### Запуск примера работы с модулем
```bash
python -m epcore.filemanager
```

###### Добавление пакетной зависимости (например: numpy, simpleaudio, etc) 

В файле `setup.py` укажите требуемый пакет, например:
<pre>
    install_requires=[
        "numpy",  # for pin module
        "simpleaudio"  # for sound module
    ],
</pre>

###### Добавление бинарной зависимости
В файле `setup.py` укажите требуемый файл, например:
<pre>
    package_data={
        'epcore.sound': ['sound/foo.so']  # for sound module
    }
</pre>
