from ctypes import Array, c_double, c_size_t, c_ubyte, POINTER, pointer, Structure
import numpy as np
from .ivc_comparator import get_dll

VOLTAGE_AMPL = 12.
R_CS = 475.
CURRENT_AMPL = (VOLTAGE_AMPL / R_CS * 1000)
MAX_NUM_POINTS = 1000
lib = get_dll()


class _IterableStructure(Structure):
    def __iter__(self):
        return (getattr(self, n) for n, t in self._fields_)


def _normalize_arg(value, desired_ctype):
    from collections.abc import Sequence

    if isinstance(value, desired_ctype):
        return value
    elif issubclass(desired_ctype, Array) and isinstance(value, Sequence):
        member_type = desired_ctype._type_

        if desired_ctype._length_ < len(value):
            raise ValueError()

        if issubclass(member_type, c_ubyte) and isinstance(value, bytes):
            return desired_ctype.from_buffer_copy(value)
        elif issubclass(member_type, c_ubyte) and isinstance(value, bytearray):
            return value
        else:
            return desired_ctype(*value)
    else:
        return value


class IvCurve(_IterableStructure):
    """
    Класс сигнатуры (ВАХ)
    voltages - массив напряжений [Вольты]
    сurrents - массив токов [мА]
    length - количество элементов в массивах voltages и currents (должно быть одинаковым).

    """
    _fields_ = (
        ("voltages", c_double*MAX_NUM_POINTS),
        ("currents", c_double*MAX_NUM_POINTS),
        ("length", c_size_t)
    )

    def __init__(self):
        self.length = MAX_NUM_POINTS


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
    до тех пор пока масштабы не будут обновлены путём вызова данной функции
    или функции SetMinVarVCFromCurves().

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

    @param min_var_v Характерный масштаб по напряжению. Единицы измерения: Вольты.
    @param min_var_c Характерный масштаб по току. Единицы измерения: мА.
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
    до тех пор пока пороги не будут обновлены путём вызова данной функции
    или функции SetMinVarVC().
    Данная функция является альтернативой для функции SetMinVarVC().
    Если Вы не знаете уровень шумов, но у Вас есть сигнатуры короткого замыкания
    и разрыва, используйте эту функцию. Если у Вас нет сигнатур или
    Вы хотите произвести оценки самостоятельно, используйте функцию SetMinVarVC().
    @param open_circuit_iv_curve сигнатура, снятая при разомкнутых щупах (объект типа IvCurve)
    @param short_circuit_iv_curve сигнатура, снятая при разомкнутых щупах (объект типа IvCurve)
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
    """
    min_var_v = c_double()
    min_var_c = c_double()

    lib_func = lib.GetMinVarVC
    lib_func.argtype = POINTER(c_double), POINTER(c_double)

    lib_func(pointer(min_var_v), pointer(min_var_c))
    return min_var_v.value, min_var_c.value


def CompareIvc(first_iv_curve, second_iv_curve):
    """
    Функция для сравнения двух сигнатур (ВАХ).
    Возвращает степень различия в диапазоне [0, 1]
    (0 - кривые совпадают, 1 - кривые совсем разные).
    Степень различия соответствует визуальному различию кривых.
    Совпадающими сигнатурами являются те, которые совпадают при наложении.
    Максимальным различием обладают сигнатуры разрыва и короткого замыкания
    (в одной из них меняется только напряжение, в другой меняется только ток).
    Если сигнатуры имеют некоторые общие черты, но не совпадают
    (например, сопротивления разных номиналов
    или сопротивление и сопротивление с ёмкостью), степень различия будет промежуточной.
    Передаваемые массивы токов и напряжений должны иметь одинаковую длину
    и содержать по одному периоду пробного сигнала
    (один цикл замкнутой кривой).
    @param first_iv_curve первая кривая для сравнения (объект типа IvCurve)
    @param second_iv_curve первая кривая для сравнения (объект типа IvCurve)
    """
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

    # Set cureves scale
    SetMinVarVC(VOLTAGE_AMPL * 0.03, CURRENT_AMPL * 0.03)

    score = CompareIvc(iv_curve_1, iv_curve_2)
    print("Score: {:.2f}".format(score))
