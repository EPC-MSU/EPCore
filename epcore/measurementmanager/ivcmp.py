import logging
import os
from ctypes import Array, c_double, c_size_t, c_ubyte, CDLL, POINTER, pointer, Structure
from platform import system
import numpy as np


VOLTAGE_AMPL = 12.
R_CS = 475.
CURRENT_AMPL = (VOLTAGE_AMPL / R_CS * 1000)
MAX_NUM_POINTS = 1000


def _fullpath_lib(name: str) -> str:
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), name)


def _load_specific_lib(path):
    try:
        lib = CDLL(path)
        logging.debug("Load library " + path + ": success")
        return lib
    except OSError as err:
        logging.debug("Load library " + path + ": failed, " + str(err))
        raise err


def _get_dll():
    if system() == "Linux":
        paths = (
            _fullpath_lib("libivcmp.so"),
            "libivcmp.so",
        )
    elif system() == "Windows":
        paths = (
            _fullpath_lib("ivcmp.dll"),
            "ivcmp.dll",
        )
    else:
        raise NotImplementedError("Unsupported platform {}".format(system()))

    errors = []
    for path in paths:
        try:
            lib = _load_specific_lib(path)
        except Exception as e:
            errors.append(str(e))
        else:
            return lib

    error_msg = "Unable to load library. Paths tried:\n"
    for i, path in enumerate(paths):
        error_msg = error_msg + str(path) + " - got error: " + errors[i] + "\n"

    raise RuntimeError(error_msg)


lib = _get_dll()


class _IterableStructure(Structure):
    def __iter__(self):
        return (getattr(self, n) for n, t in self._fields_)


def _normalize_arg(value, desired_ctype):
    from collections.abc import Sequence

    if isinstance(value, desired_ctype):
        return value

    if issubclass(desired_ctype, Array) and isinstance(value, Sequence):
        member_type = desired_ctype._type_

        if desired_ctype._length_ < len(value):
            raise ValueError()

        if issubclass(member_type, c_ubyte) and isinstance(value, bytes):
            return desired_ctype.from_buffer_copy(value)
        if issubclass(member_type, c_ubyte) and isinstance(value, bytearray):
            return value

        return desired_ctype(*value)

    return value


class IvCurve(_IterableStructure):
    """
    Класс сигнатуры (ВАХ).
    voltages - массив напряжений [В].
    сurrents - массив токов [мА].
    length - количество элементов в массивах voltages и currents (должно быть одинаковым).
    """

    _fields_ = (
        ("_voltages", c_double * MAX_NUM_POINTS),
        ("_currents", c_double * MAX_NUM_POINTS),
        ("length", c_size_t)
    )

    def __init__(self):
        self.length = 0

    @property
    def voltages(self):
        return self._voltages

    @voltages.setter
    def voltages(self, new_voltages_array):
        if len(new_voltages_array) > MAX_NUM_POINTS:
            raise ValueError("Voltages array length is too large: {} should be less or equal {}".format(
                len(new_voltages_array), MAX_NUM_POINTS))

        for i in range(len(new_voltages_array)):
            # Elementwise assignment for correct ctypes conversion
            self._voltages[i] = c_double(new_voltages_array[i])

    @property
    def currents(self):
        return self._currents

    @currents.setter
    def currents(self, new_currents_array):
        if len(new_currents_array) > MAX_NUM_POINTS:
            raise ValueError("Currents array length is too large: {} should be less or equal {}".format(
                len(new_currents_array), MAX_NUM_POINTS))

        for i in range(len(new_currents_array)):
            # Elementwise assignment for correct ctypes conversion
            self._currents[i] = c_double(new_currents_array[i])


def SetMinVarVC(min_var_v, min_var_c):
    """
    Функция установки порогов масштабирования при нормировке токов и напряжений.
    Установка этих параметров обязательна для корректной работы библиотеки.
    При сравнении кривых производится нормировка токов и напряжений.
    Шумы, которые есть в любой системе, могут оказывать влияние на результат сравнения.
    Если шумы не учитывать, то при сравнении визуально совпадающих кривых,
    библиотека может выдать ненулевую степень различия из-за неправильной нормировки.
    Чтобы этого не произошло, установите порог нормировки с помощью данной функции.
    Сохранённые значения будут использоваться для всех последующих сравнений кривых
    до тех пор, пока масштабы не будут обновлены путём вызова данной функции или функции SetMinVarVCFromCurves().

    Способы определения порогов масштабирования:
    - Ручной:
        - Произвести измерения шумов по току и напряжению.
        - Определить их стандартные отклонения.
        - Задать пороги, равные трём стандартным отклонениям.
    - Автоматический:
        - Измерить сигнатуры разрыва и короткого замыкания.
        - Воспользоваться процедурой автоматического определения с помощью функции SetMinVarVCFromCurves().
    - Ручной грубый:
        - Задать пороги сравнения, равные 3% от диапазонов измерения по току и напряжению.

    При любом способе определения пороги масштабирования зависят от диапазонов измерения.
    Поэтому значения необходимо обновлять при каждом изменении настроек измерителя.

    :param min_var_v: Характерный масштаб по напряжению. Единицы измерения: В.
    :param min_var_c: Характерный масштаб по току. Единицы измерения: мА.
    """

    lib_func = lib.SetMinVarVC
    lib_func.argtype = c_double, c_double
    lib_func(c_double(min_var_v),  c_double(min_var_c))


def SetMinVarVCFromCurves(open_circuit_iv_curve, short_circuit_iv_curve):
    """
    Функция автоматического определения и установки порогов масштабирования при нормировке токов и напряжений.
    Функция принимает две сигнатуры:
    - первая должна быть измерена при разомкнутых щупах (измеряется нулевой ток);
    - вторая должна быть измерена в случае, когда щупы замкнуты накоротко (измеряется напряжение КЗ).
    На основе полученных сигнатур функция определяет характерные масштабы шумов
    и задаёт пороги масштабирования при нормировке.
    Установленные значения будут использоваться для всех последующих сравнений кривых
    до тех пор, пока пороги не будут обновлены путём вызова данной функции или функции SetMinVarVC().
    Данная функция является альтернативой для функции SetMinVarVC().
    Если Вы не знаете уровень шумов, но у Вас есть сигнатуры короткого замыкания
    и разрыва, используйте эту функцию. Если у Вас нет сигнатур или
    Вы хотите произвести оценки самостоятельно, используйте функцию SetMinVarVC().

    :param open_circuit_iv_curve: Сигнатура, снятая при разомкнутых щупах (объект типа IvCurve).
    :param short_circuit_iv_curve: Сигнатура, снятая при разомкнутых щупах (объект типа IvCurve).
    """

    lib_func = lib.SetMinVarVCFromCurves
    lib_func.argtype = POINTER(c_double), POINTER(c_double), c_size_t, POINTER(c_double), POINTER(c_double), c_size_t
    lib_func.restype = c_double
    res = lib_func(open_circuit_iv_curve.voltages, open_circuit_iv_curve.currents, open_circuit_iv_curve.length,
                   short_circuit_iv_curve.voltages, short_circuit_iv_curve.currents, short_circuit_iv_curve.length)
    res = _normalize_arg(res, c_double)
    return res


def GetMinVarVC():
    """
    Функция для получения текущих значений порогов масштабирования при нормировке токов и напряжений.
    Подробнее о порогах см. описание функции SetMinVarVC.

    :return: Значения порогов масштабирования напряжения и тока.
    """

    min_var_v = c_double()
    min_var_c = c_double()

    lib_func = lib.GetMinVarVC
    lib_func.argtype = POINTER(c_double), POINTER(c_double)

    lib_func(pointer(min_var_v), pointer(min_var_c))
    return min_var_v.value, min_var_c.value


def SetRangesVC(range_v, range_c):
    lib_func = lib.SetRangesVC
    lib_func.argtype = c_double, c_double
    lib_func(c_double(range_v), c_double(range_c))


def CompareIvc(first_iv_curve, second_iv_curve) -> float:
    """
    Функция для сравнения двух сигнатур (ВАХ).
    Возвращает степень различия в диапазоне [0, 1] (0 - кривые совпадают, 1 - кривые совсем разные).
    Степень различия соответствует визуальному различию кривых.
    Совпадающими сигнатурами являются те, которые совпадают при наложении.
    Максимальным различием обладают сигнатуры разрыва и короткого замыкания
    (в одной из них меняется только напряжение, в другой меняется только ток).
    Если сигнатуры имеют некоторые общие черты, но не совпадают
    (например, сопротивления разных номиналов или сопротивление и сопротивление с ёмкостью),
    степень различия будет промежуточной.
    Передаваемые массивы токов и напряжений должны иметь одинаковую длину
    и содержать по одному периоду пробного сигнала (один цикл замкнутой кривой).

    :param first_iv_curve: Первая кривая для сравнения (объект типа IvCurve).
    :param second_iv_curve: Вторая кривая для сравнения (объект типа IvCurve).
    :return: Степень различия.
    """

    if first_iv_curve.length == 0 or second_iv_curve.length == 0:
        raise ValueError("IVCurve length attribute should be explicitly set. And it should not be zero.")

    lib_func = lib.CompareIVC
    lib_func.argtype = POINTER(c_double), POINTER(c_double), c_size_t, POINTER(c_double), POINTER(c_double), c_size_t
    lib_func.restype = c_double
    res = lib_func(first_iv_curve.voltages, first_iv_curve.currents, first_iv_curve.length,
                   second_iv_curve.voltages, second_iv_curve.currents, second_iv_curve.length)
    res = _normalize_arg(res, c_double)

    if res < 0:
        raise RuntimeError("Something went wrong during ivcmp.CompareIVC() call. More details in console output.")

    return res


if __name__ == "__main__":
    iv_curve_1 = IvCurve()
    iv_curve_1.length = MAX_NUM_POINTS
    iv_curve_2 = IvCurve()
    iv_curve_2.length = MAX_NUM_POINTS
    for i in range(MAX_NUM_POINTS):
        iv_curve_1.voltages[i] = 1.2 * VOLTAGE_AMPL * np.sin(2 * 3.14 * i / MAX_NUM_POINTS)
        iv_curve_1.currents[i] = 0.8 * CURRENT_AMPL * np.sin(2 * 3.14 * i / MAX_NUM_POINTS)
        iv_curve_2.voltages[i] = VOLTAGE_AMPL * np.sin(2 * 3.14 * i / MAX_NUM_POINTS)
        iv_curve_2.currents[i] = CURRENT_AMPL * np.sin(2 * 3.14 * i / MAX_NUM_POINTS)

    # Set curves scale and range
    SetMinVarVC(VOLTAGE_AMPL * 0.03, CURRENT_AMPL * 0.03)
    SetRangesVC(VOLTAGE_AMPL, CURRENT_AMPL)

    score = CompareIvc(iv_curve_1, iv_curve_2)
    print("Score: {:.2f}".format(score))
