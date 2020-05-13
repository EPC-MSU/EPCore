# Тут хранятся разные небольшие вспомогательные подпрограммы

## converter_p10

Программа для конвертации файлов из формата, используемого в EyePoint Px / Bx в формат UFIV (Universal Format for IV curves, используется в EPLab).

Пример запуска:

```
python converter_p10.py --source <файлы из EP P10>.json --destination <название нового файла>.json
python converter_p10.py --source tests/p10.json --destination test_file.json
```

Выходные файлы должны соответствовать схеме (описания)  формата UFIV.

Схема хранится в папке `../doc/elements.schema.json`.

Чтобы проверить, что выходной файл соответствует схеме, можно добавить ключ `--validate` и указать путь к схеме.

Пример:

```
python converter_p10.py --source tests/p10.json --destination test_file.json --validate ../doc/elements.schema.json
```

Проверить выходной файл на соответствие схеме можно также и с помощью внешних инструментов. Например, https://www.jsonschemavalidator.net.

