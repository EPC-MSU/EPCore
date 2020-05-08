# EyePoint Kernel 
Здесь находятся модули EyePoint универсальные для всех продуктов

_Все новые модули нужно делать по образцу существующих в этом проекте. 
Соблюдать сходство именований и архитектуры папок_

## Тесты
Чтобы запустить тесты, нужно из директории проекта запустить:
```bash
bash testall.sh
```
При этом "python3.6" должен быть доступен для выполнения 
Либо на windows:
```bash
cmd
testall.bat
```
при этом "python" версии 3.6 должен быть доступен для выполнения.  

Скрипт тестирования создаст venv в папке с проектом, поэтому у исполнителя должен 
быть доступ на запись

### Прочие инструкции

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
