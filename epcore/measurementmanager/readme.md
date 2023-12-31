## Класс «Измерительная система» MeasurementSystem

Это список измерителей, которые есть в данной системе.

### Методы

* Получить список измерителей и список мультиплексоров.
* Массово установить базовые настройки всем измерителям.
* Получить настройки измерителей (если вдруг оказалось, что они разные, кинуть исключение).
* Получить комплект измерений со всех измерителей.
* Запустить измерение, если режим запуска ручной.
* Проброс специальных нестандартных настроек (например, в виртуальном измерителе можно настраивать модель измеряемого компонента).
* Задать активный выход всем мультиплексорам.

## Класс «План тестирования» MeasurementPlan

Класс плана тестирования наследуется от класса платы.

Все точки платы выстраиваются в единый список. Список «виртуальный» и нигде не хранится. Под списком понимается то, что для каждой точки, кроме первой и последней, всегда можно узнать следующую и предыдущую. Сами точки при этом хранятся в структуре платы и структура платы не нарушается.

### Методы

* Назначить и получить стандартный измеритель для плана тестирования.
* Назначить и получить мультиплексор для плана тестирования.
* Вернуть текущую точку и точку с заданным номером.
* Вернуть список точек, у которых не сохранены выходы мультиплексора.
* Добавить точку в конец (в последний компонент в списке компонентов платы).
* Перейти к следующей/предыдущей точке.
* Перейти к точке с определённым номером.
* Сделать измерение, которое было сделано последним, опорным/тестовым для данной точки.