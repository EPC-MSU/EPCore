# Тут хранятся разные небольшие вспомогательные подпрограммы

Перед использованием установите в интерпретатор все зависиости из requirements.txt в корне проекта

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

Если в исходном файле опорные ВАХ-и не помечены в схеме как опорные (reference_ivc: None), то 
в выходном файле они также не будут считаться опорными.  
Чтобы форсированно добавить к существующим ВАХ метку reference при конвертации нужно запустить конвертер с 
параметром --reference