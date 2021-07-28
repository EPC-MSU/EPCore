# EyePoint Kernel 
Здесь находятся модули EyePoint, универсальные для всех продуктов.

_Все новые модули нужно делать по образцу существующих в этом проекте. Нужно соблюдать сходство именований и архитектуры папок._

## Тесты в Linux
Чтобы запустить тесты, нужно из директории проекта запустить:
```bash
bash testall.sh
```
При этом Python версии 3.6 должен быть доступен для выполнения.

## Тесты в Windows

```bash
cmd
testall.bat
```
При этом Python версии 3.6 должен быть доступен для выполнения. Скрипт тестирования создаст venv в папке с проектом, поэтому у исполнителя должен быть доступ на запись.

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

В файле setup.py:
<pre>
    install_requires=[
        "numpy",  # for pin module
        "simpleaudio"  # for sound module
    ],
</pre>

###### Добавление бинарной зависимости
В файле setup.py, например:
<pre>
    package_data={
        'epcore.sound': ['sound/foo.so']  # for sound module
    }
</pre>
