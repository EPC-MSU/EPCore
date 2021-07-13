import logging
from sys import version_info
from ctypes import CDLL, Structure, Array, CFUNCTYPE, byref, create_string_buffer, addressof, cast
from ctypes import c_ubyte, c_byte, c_ushort, c_short, c_uint, c_int, c_ulonglong, c_longlong, c_float, \
     c_void_p, c_char_p, c_wchar_p, c_size_t
try:
    from typing import overload, Union, Sequence, Optional
except ImportError:
    def overload(method):
        return method


    class _GenericTypeMeta(type):
        def __getitem__(self, _):
            return None


    class Union(metaclass=_GenericTypeMeta):
        pass


    class Sequence(metaclass=_GenericTypeMeta):
        pass


    class Optional(metaclass=_GenericTypeMeta):
        pass


urpc_builder_version = "0.6.1"


_Ok = 0
_Error = -1
_NotImplemented = -2
_ValueError = -3
_NoDevice = -4
_DeviceUndefined = -1


class _IterableStructure(Structure):
    def __iter__(self):
        return (getattr(self, n) for n, t in self._fields_)


def _validate_call(result):
    if result == _ValueError:
        raise ValueError()
    elif result == _NotImplemented:
        raise NotImplementedError()
    elif result != _Ok:
        raise RuntimeError()


def _normalize_arg(value, desired_ctype):
    from collections import Sequence

    if isinstance(value, desired_ctype):
        return value
    elif issubclass(desired_ctype, Array) and isinstance(value, Sequence):
        member_type = desired_ctype._type_

        if desired_ctype._length_ < len(value):
            raise ValueError()

        if issubclass(member_type, c_ubyte) and isinstance(value, bytes):
            return desired_ctype.from_buffer_copy(value)
        elif issubclass(member_type, c_ubyte) and isinstance(value, bytearray):
            return desired_ctype.from_buffer(value)
        else:
            return desired_ctype(*value)
    else:
        return desired_ctype(value)


def _load_lib():
    from platform import system

    lib = None
    os_kind = system().lower()
    if os_kind == "windows":
        lib = CDLL("ivm.dll")
    elif os_kind == "darwin":
        lib = CDLL("libivm.dylib")
    elif os_kind == "freebsd" or "linux" in os_kind:
        lib = CDLL("libivm.so")
    else:
        raise RuntimeError("unexpected OS")

    return lib

_lib = _load_lib()


# Hack to prevent auto-conversion to native Python int
class _device_t(c_int):
    def from_param(self, *args):
        return self


_lib.ivm_open_device.restype = _device_t


_logger = logging.getLogger(__name__)


@CFUNCTYPE(None, c_int, c_wchar_p, c_void_p)
def _logging_callback(loglevel, message, user_data):
    if loglevel == 0x01:
        _logger.error(message)    
    elif loglevel == 0x02:
        _logger.warning(message)
    elif loglevel == 0x03:
        _logger.info(message)
    elif loglevel == 0x04:
        _logger.debug(message)

_lib.ivm_set_logging_callback(_logging_callback)


def reset_locks():
    _validate_call(_lib.ivm_reset_locks())


def fix_usbser_sys():
    _validate_call(_lib.ivm_fix_usbser_sys())


class IvmDeviceHandle:
    class GetMeasurementRequest(_IterableStructure):
        _fields_ = (
            ("_frame", c_ushort),
        )

        @property
        def frame(self) -> c_ushort:
            return self._frame


        @frame.setter
        def frame(self, value: Union[int, c_ushort]) -> None:
            self._frame = _normalize_arg(value, c_ushort)

    class GetMeasurementResponse(_IterableStructure):
        _fields_ = (
            ("_voltage", c_float*25),
            ("_current", c_float*25),
        )

        @property
        def voltage(self) -> c_float*25:
            return self._voltage


        @voltage.setter
        def voltage(self, value: Union[Sequence[float], c_float*25]) -> None:
            self._voltage = _normalize_arg(value, c_float*25)

        @property
        def current(self) -> c_float*25:
            return self._current


        @current.setter
        def current(self, value: Union[Sequence[float], c_float*25]) -> None:
            self._current = _normalize_arg(value, c_float*25)

    @overload
    def get_measurement(
            self,
            frame: Union[int, c_ushort],
            *,
            dst_buffer: Optional[GetMeasurementResponse]=None
    ) -> GetMeasurementResponse: pass

    @overload
    def get_measurement(
            self,
            src_buffer: GetMeasurementRequest,
            *,
            dst_buffer: Optional[GetMeasurementResponse]=None
    ) -> GetMeasurementResponse: pass

    def get_measurement(self, *args, **kwargs) -> GetMeasurementResponse:
        src_buffer = None
        if len(args) != 1 or not isinstance(args[0], self.GetMeasurementRequest):
            src_buffer = self.GetMeasurementRequest(
                frame=_normalize_arg(args[0], c_ushort)
            )
        else:
            src_buffer = args[0]
        dst_buffer = kwargs.get("dst_buffer", self.GetMeasurementResponse())
        _validate_call(_lib.ivm_get_measurement(self._handle, byref(src_buffer), byref(dst_buffer)))
        return dst_buffer

    class GetIdentityInformationResponse(_IterableStructure):
        _fields_ = (
            ("_manufacturer", c_ubyte*16),
            ("_product_name", c_ubyte*16),
            ("_controller_name", c_ubyte*16),
            ("_hardware_major", c_ubyte),
            ("_hardware_minor", c_ubyte),
            ("_hardware_bugfix", c_ushort),
            ("_bootloader_major", c_ubyte),
            ("_bootloader_minor", c_ubyte),
            ("_bootloader_bugfix", c_ushort),
            ("_firmware_major", c_ubyte),
            ("_firmware_minor", c_ubyte),
            ("_firmware_bugfix", c_ushort),
            ("_serial_number", c_uint),
            ("_reserved", c_ubyte*8),
        )

        @property
        def manufacturer(self) -> c_ubyte*16:
            return self._manufacturer


        @manufacturer.setter
        def manufacturer(self, value: Union[Sequence[int], c_ubyte*16]) -> None:
            self._manufacturer = _normalize_arg(value, c_ubyte*16)

        @property
        def product_name(self) -> c_ubyte*16:
            return self._product_name


        @product_name.setter
        def product_name(self, value: Union[Sequence[int], c_ubyte*16]) -> None:
            self._product_name = _normalize_arg(value, c_ubyte*16)

        @property
        def controller_name(self) -> c_ubyte*16:
            return self._controller_name


        @controller_name.setter
        def controller_name(self, value: Union[Sequence[int], c_ubyte*16]) -> None:
            self._controller_name = _normalize_arg(value, c_ubyte*16)

        @property
        def hardware_major(self) -> c_ubyte:
            return self._hardware_major


        @hardware_major.setter
        def hardware_major(self, value: Union[int, c_ubyte]) -> None:
            self._hardware_major = _normalize_arg(value, c_ubyte)

        @property
        def hardware_minor(self) -> c_ubyte:
            return self._hardware_minor


        @hardware_minor.setter
        def hardware_minor(self, value: Union[int, c_ubyte]) -> None:
            self._hardware_minor = _normalize_arg(value, c_ubyte)

        @property
        def hardware_bugfix(self) -> c_ushort:
            return self._hardware_bugfix


        @hardware_bugfix.setter
        def hardware_bugfix(self, value: Union[int, c_ushort]) -> None:
            self._hardware_bugfix = _normalize_arg(value, c_ushort)

        @property
        def bootloader_major(self) -> c_ubyte:
            return self._bootloader_major


        @bootloader_major.setter
        def bootloader_major(self, value: Union[int, c_ubyte]) -> None:
            self._bootloader_major = _normalize_arg(value, c_ubyte)

        @property
        def bootloader_minor(self) -> c_ubyte:
            return self._bootloader_minor


        @bootloader_minor.setter
        def bootloader_minor(self, value: Union[int, c_ubyte]) -> None:
            self._bootloader_minor = _normalize_arg(value, c_ubyte)

        @property
        def bootloader_bugfix(self) -> c_ushort:
            return self._bootloader_bugfix


        @bootloader_bugfix.setter
        def bootloader_bugfix(self, value: Union[int, c_ushort]) -> None:
            self._bootloader_bugfix = _normalize_arg(value, c_ushort)

        @property
        def firmware_major(self) -> c_ubyte:
            return self._firmware_major


        @firmware_major.setter
        def firmware_major(self, value: Union[int, c_ubyte]) -> None:
            self._firmware_major = _normalize_arg(value, c_ubyte)

        @property
        def firmware_minor(self) -> c_ubyte:
            return self._firmware_minor


        @firmware_minor.setter
        def firmware_minor(self, value: Union[int, c_ubyte]) -> None:
            self._firmware_minor = _normalize_arg(value, c_ubyte)

        @property
        def firmware_bugfix(self) -> c_ushort:
            return self._firmware_bugfix


        @firmware_bugfix.setter
        def firmware_bugfix(self, value: Union[int, c_ushort]) -> None:
            self._firmware_bugfix = _normalize_arg(value, c_ushort)

        @property
        def serial_number(self) -> c_uint:
            return self._serial_number


        @serial_number.setter
        def serial_number(self, value: Union[int, c_uint]) -> None:
            self._serial_number = _normalize_arg(value, c_uint)

        @property
        def reserved(self) -> c_ubyte*8:
            return self._reserved


        @reserved.setter
        def reserved(self, value: Union[Sequence[int], c_ubyte*8]) -> None:
            self._reserved = _normalize_arg(value, c_ubyte*8)

    def get_identity_information(self, **kwargs) -> GetIdentityInformationResponse:
        dst_buffer = kwargs.get("dst_buffer", self.GetIdentityInformationResponse())
        _validate_call(_lib.ivm_get_identity_information(self._handle, byref(dst_buffer)))
        return dst_buffer

    class CalibrateResponse(_IterableStructure):
        _fields_ = (
            ("_result", c_ubyte),
        )

        @property
        def result(self) -> c_ubyte:
            return self._result


        @result.setter
        def result(self, value: Union[int, c_ubyte]) -> None:
            self._result = _normalize_arg(value, c_ubyte)

    def calibrate(self, **kwargs) -> CalibrateResponse:
        dst_buffer = kwargs.get("dst_buffer", self.CalibrateResponse())
        _validate_call(_lib.ivm_calibrate(self._handle, byref(dst_buffer)))
        return dst_buffer

    class GetStatusResponse(_IterableStructure):
        _fields_ = (
            ("_status", c_uint),
            ("_temp", c_short),
            ("_reserved", c_ubyte*48),
        )

        @property
        def status(self) -> c_uint:
            return self._status


        @status.setter
        def status(self, value: Union[int, c_uint]) -> None:
            self._status = _normalize_arg(value, c_uint)

        @property
        def temp(self) -> c_short:
            return self._temp


        @temp.setter
        def temp(self, value: Union[int, c_short]) -> None:
            self._temp = _normalize_arg(value, c_short)

        @property
        def reserved(self) -> c_ubyte*48:
            return self._reserved


        @reserved.setter
        def reserved(self, value: Union[Sequence[int], c_ubyte*48]) -> None:
            self._reserved = _normalize_arg(value, c_ubyte*48)

    def get_status(self, **kwargs) -> GetStatusResponse:
        dst_buffer = kwargs.get("dst_buffer", self.GetStatusResponse())
        _validate_call(_lib.ivm_get_status(self._handle, byref(dst_buffer)))
        return dst_buffer

    def start_measurement(self) -> None:
        _validate_call(_lib.ivm_start_measurement(self._handle))

    class MeasurementReadyResponse(_IterableStructure):
        _fields_ = (
            ("_ready_status", c_ubyte),
            ("_reserved", c_ubyte*15),
        )

        @property
        def ready_status(self) -> c_ubyte:
            return self._ready_status


        @ready_status.setter
        def ready_status(self, value: Union[int, c_ubyte]) -> None:
            self._ready_status = _normalize_arg(value, c_ubyte)

        @property
        def reserved(self) -> c_ubyte*15:
            return self._reserved


        @reserved.setter
        def reserved(self, value: Union[Sequence[int], c_ubyte*15]) -> None:
            self._reserved = _normalize_arg(value, c_ubyte*15)

    def measurement_ready(self, **kwargs) -> MeasurementReadyResponse:
        dst_buffer = kwargs.get("dst_buffer", self.MeasurementReadyResponse())
        _validate_call(_lib.ivm_measurement_ready(self._handle, byref(dst_buffer)))
        return dst_buffer

    def reset(self) -> None:
        _validate_call(_lib.ivm_reset(self._handle))

    def update_firmware(self) -> None:
        _validate_call(_lib.ivm_update_firmware(self._handle))

    def reboot_to_bootloader(self) -> None:
        _validate_call(_lib.ivm_reboot_to_bootloader(self._handle))

    def save_robust_settings(self) -> None:
        _validate_call(_lib.ivm_save_robust_settings(self._handle))

    def read_robust_settings(self) -> None:
        _validate_call(_lib.ivm_read_robust_settings(self._handle))

    class AnalogDataRequest(_IterableStructure):
        _fields_ = (
            ("_frame", c_ushort),
        )

        @property
        def frame(self) -> c_ushort:
            return self._frame


        @frame.setter
        def frame(self, value: Union[int, c_ushort]) -> None:
            self._frame = _normalize_arg(value, c_ushort)

    class AnalogDataResponse(_IterableStructure):
        _fields_ = (
            ("_voltage_code", c_ushort*25),
            ("_current_code", c_ushort*25),
        )

        @property
        def voltage_code(self) -> c_ushort*25:
            return self._voltage_code


        @voltage_code.setter
        def voltage_code(self, value: Union[Sequence[int], c_ushort*25]) -> None:
            self._voltage_code = _normalize_arg(value, c_ushort*25)

        @property
        def current_code(self) -> c_ushort*25:
            return self._current_code


        @current_code.setter
        def current_code(self, value: Union[Sequence[int], c_ushort*25]) -> None:
            self._current_code = _normalize_arg(value, c_ushort*25)

    @overload
    def analog_data(
            self,
            frame: Union[int, c_ushort],
            *,
            dst_buffer: Optional[AnalogDataResponse]=None
    ) -> AnalogDataResponse: pass

    @overload
    def analog_data(
            self,
            src_buffer: AnalogDataRequest,
            *,
            dst_buffer: Optional[AnalogDataResponse]=None
    ) -> AnalogDataResponse: pass

    def analog_data(self, *args, **kwargs) -> AnalogDataResponse:
        src_buffer = None
        if len(args) != 1 or not isinstance(args[0], self.AnalogDataRequest):
            src_buffer = self.AnalogDataRequest(
                frame=_normalize_arg(args[0], c_ushort)
            )
        else:
            src_buffer = args[0]
        dst_buffer = kwargs.get("dst_buffer", self.AnalogDataResponse())
        _validate_call(_lib.ivm_analog_data(self._handle, byref(src_buffer), byref(dst_buffer)))
        return dst_buffer

    class MainLightRequest(_IterableStructure):
        _fields_ = (
            ("_state", c_ubyte),
        )

        class State(int):
            MAIN_LIGHT_STATE_ON = 1

            @property
            def main_light_state_on(self) -> int:
                return self & self.MAIN_LIGHT_STATE_ON                

        @property
        def state(self) -> State:
            return self.State(self._state)

        @state.setter
        def state(self, value: Union[int, c_ubyte]) -> None:
            self._state = _normalize_arg(value, c_ubyte)

    @overload
    def main_light(
            self,
            state: Union[int, c_ubyte]
    ) -> None: pass

    @overload
    def main_light(
            self,
            src_buffer: MainLightRequest
    ) -> None: pass

    def main_light(self, *args) -> None:
        src_buffer = None
        if len(args) != 1 or not isinstance(args[0], self.MainLightRequest):
            src_buffer = self.MainLightRequest(
                state=_normalize_arg(args[0], c_ubyte)
            )
        else:
            src_buffer = args[0]
        _validate_call(_lib.ivm_main_light(self._handle, byref(src_buffer)))

    class HeadLightRequest(_IterableStructure):
        _fields_ = (
            ("_state", c_ubyte),
        )

        class State(int):
            HEAD_LIGHT_STATE_ON = 1

            @property
            def head_light_state_on(self) -> int:
                return self & self.HEAD_LIGHT_STATE_ON                

        @property
        def state(self) -> State:
            return self.State(self._state)

        @state.setter
        def state(self, value: Union[int, c_ubyte]) -> None:
            self._state = _normalize_arg(value, c_ubyte)

    @overload
    def head_light(
            self,
            state: Union[int, c_ubyte]
    ) -> None: pass

    @overload
    def head_light(
            self,
            src_buffer: HeadLightRequest
    ) -> None: pass

    def head_light(self, *args) -> None:
        src_buffer = None
        if len(args) != 1 or not isinstance(args[0], self.HeadLightRequest):
            src_buffer = self.HeadLightRequest(
                state=_normalize_arg(args[0], c_ubyte)
            )
        else:
            src_buffer = args[0]
        _validate_call(_lib.ivm_head_light(self._handle, byref(src_buffer)))

    class MeasureSettingsRequest(_IterableStructure):
        _fields_ = (
            ("_desc_frequency", c_float),
            ("_probe_signal_frequency", c_float),
            ("_number_points", c_uint),
            ("_number_charge_points", c_uint),
            ("_max_voltage", c_float),
            ("_max_current", c_float),
            ("_measure_flags", c_uint),
            ("_reserved", c_ubyte*20),
        )

        @property
        def desc_frequency(self) -> c_float:
            return self._desc_frequency


        @desc_frequency.setter
        def desc_frequency(self, value: Union[float, c_float]) -> None:
            self._desc_frequency = _normalize_arg(value, c_float)

        @property
        def probe_signal_frequency(self) -> c_float:
            return self._probe_signal_frequency


        @probe_signal_frequency.setter
        def probe_signal_frequency(self, value: Union[float, c_float]) -> None:
            self._probe_signal_frequency = _normalize_arg(value, c_float)

        @property
        def number_points(self) -> c_uint:
            return self._number_points


        @number_points.setter
        def number_points(self, value: Union[int, c_uint]) -> None:
            self._number_points = _normalize_arg(value, c_uint)

        @property
        def number_charge_points(self) -> c_uint:
            return self._number_charge_points


        @number_charge_points.setter
        def number_charge_points(self, value: Union[int, c_uint]) -> None:
            self._number_charge_points = _normalize_arg(value, c_uint)

        @property
        def max_voltage(self) -> c_float:
            return self._max_voltage


        @max_voltage.setter
        def max_voltage(self, value: Union[float, c_float]) -> None:
            self._max_voltage = _normalize_arg(value, c_float)

        @property
        def max_current(self) -> c_float:
            return self._max_current


        @max_current.setter
        def max_current(self, value: Union[float, c_float]) -> None:
            self._max_current = _normalize_arg(value, c_float)

        class MeasureFlags(int):
            CURRENT_SENSE_MODE_ISOLATED = 0
            CURRENT_SENSE_MODE_250UA = 1
            CURRENT_SENSE_MODE_2M5A = 2
            CURRENT_SENSE_MODE_25MA = 3
            CURRENT_SENSE_MODE_BITS = 3

            @property
            def current_sense_mode_isolated(self) -> int:
                return self & self.CURRENT_SENSE_MODE_ISOLATED                

            @property
            def current_sense_mode_250_ua(self) -> int:
                return self & self.CURRENT_SENSE_MODE_250UA                

            @property
            def current_sense_mode_2_m5_a(self) -> int:
                return self & self.CURRENT_SENSE_MODE_2M5A                

            @property
            def current_sense_mode_25_ma(self) -> int:
                return self & self.CURRENT_SENSE_MODE_25MA                

            @property
            def current_sense_mode_bits(self) -> int:
                return self & self.CURRENT_SENSE_MODE_BITS                

        @property
        def measure_flags(self) -> MeasureFlags:
            return self.MeasureFlags(self._measure_flags)

        @measure_flags.setter
        def measure_flags(self, value: Union[int, c_uint]) -> None:
            self._measure_flags = _normalize_arg(value, c_uint)

        @property
        def reserved(self) -> c_ubyte*20:
            return self._reserved


        @reserved.setter
        def reserved(self, value: Union[Sequence[int], c_ubyte*20]) -> None:
            self._reserved = _normalize_arg(value, c_ubyte*20)

    MeasureSettingsResponse = MeasureSettingsRequest

    def get_measure_settings(self, **kwargs) -> MeasureSettingsResponse:
        dst_buffer = kwargs.get("dst_buffer", self.MeasureSettingsResponse())
        _validate_call(_lib.ivm_get_measure_settings(self._handle, byref(dst_buffer)))
        return dst_buffer

    @overload
    def set_measure_settings(
            self,
            desc_frequency: Union[float, c_float],
            probe_signal_frequency: Union[float, c_float],
            number_points: Union[int, c_uint],
            number_charge_points: Union[int, c_uint],
            max_voltage: Union[float, c_float],
            max_current: Union[float, c_float],
            measure_flags: Union[int, c_uint]
    ) -> None: pass

    @overload
    def set_measure_settings(
            self,
            src_buffer: MeasureSettingsRequest
    ) -> None: pass

    def set_measure_settings(self, *args) -> None:
        src_buffer = None
        if len(args) != 1 or not isinstance(args[0], self.MeasureSettingsRequest):
            src_buffer = self.MeasureSettingsRequest(
                desc_frequency=_normalize_arg(args[0], c_float),
                probe_signal_frequency=_normalize_arg(args[1], c_float),
                number_points=_normalize_arg(args[2], c_uint),
                number_charge_points=_normalize_arg(args[3], c_uint),
                max_voltage=_normalize_arg(args[4], c_float),
                max_current=_normalize_arg(args[5], c_float),
                measure_flags=_normalize_arg(args[6], c_uint)
            )
        else:
            src_buffer = args[0]
        _validate_call(_lib.ivm_set_measure_settings(self._handle, byref(src_buffer)))

    class CalibrationSettingsRequest(_IterableStructure):
        _fields_ = (
            ("_dac_mult", c_float),
            ("_dac_offset", c_float),
            ("_adc_mult", c_float),
            ("_adcv_offset", c_float),
            ("_current_sense1_mult", c_float),
            ("_current_sense1_offset", c_float),
            ("_current_sense2_mult", c_float),
            ("_current_sense2_offset", c_float),
            ("_current_sense3_mult", c_float),
            ("_current_sense3_offset", c_float),
            ("_reserved", c_ubyte*72),
        )

        @property
        def dac_mult(self) -> c_float:
            return self._dac_mult


        @dac_mult.setter
        def dac_mult(self, value: Union[float, c_float]) -> None:
            self._dac_mult = _normalize_arg(value, c_float)

        @property
        def dac_offset(self) -> c_float:
            return self._dac_offset


        @dac_offset.setter
        def dac_offset(self, value: Union[float, c_float]) -> None:
            self._dac_offset = _normalize_arg(value, c_float)

        @property
        def adc_mult(self) -> c_float:
            return self._adc_mult


        @adc_mult.setter
        def adc_mult(self, value: Union[float, c_float]) -> None:
            self._adc_mult = _normalize_arg(value, c_float)

        @property
        def adcv_offset(self) -> c_float:
            return self._adcv_offset


        @adcv_offset.setter
        def adcv_offset(self, value: Union[float, c_float]) -> None:
            self._adcv_offset = _normalize_arg(value, c_float)

        @property
        def current_sense1_mult(self) -> c_float:
            return self._current_sense1_mult


        @current_sense1_mult.setter
        def current_sense1_mult(self, value: Union[float, c_float]) -> None:
            self._current_sense1_mult = _normalize_arg(value, c_float)

        @property
        def current_sense1_offset(self) -> c_float:
            return self._current_sense1_offset


        @current_sense1_offset.setter
        def current_sense1_offset(self, value: Union[float, c_float]) -> None:
            self._current_sense1_offset = _normalize_arg(value, c_float)

        @property
        def current_sense2_mult(self) -> c_float:
            return self._current_sense2_mult


        @current_sense2_mult.setter
        def current_sense2_mult(self, value: Union[float, c_float]) -> None:
            self._current_sense2_mult = _normalize_arg(value, c_float)

        @property
        def current_sense2_offset(self) -> c_float:
            return self._current_sense2_offset


        @current_sense2_offset.setter
        def current_sense2_offset(self, value: Union[float, c_float]) -> None:
            self._current_sense2_offset = _normalize_arg(value, c_float)

        @property
        def current_sense3_mult(self) -> c_float:
            return self._current_sense3_mult


        @current_sense3_mult.setter
        def current_sense3_mult(self, value: Union[float, c_float]) -> None:
            self._current_sense3_mult = _normalize_arg(value, c_float)

        @property
        def current_sense3_offset(self) -> c_float:
            return self._current_sense3_offset


        @current_sense3_offset.setter
        def current_sense3_offset(self, value: Union[float, c_float]) -> None:
            self._current_sense3_offset = _normalize_arg(value, c_float)

        @property
        def reserved(self) -> c_ubyte*72:
            return self._reserved


        @reserved.setter
        def reserved(self, value: Union[Sequence[int], c_ubyte*72]) -> None:
            self._reserved = _normalize_arg(value, c_ubyte*72)

    CalibrationSettingsResponse = CalibrationSettingsRequest

    def get_calibration_settings(self, **kwargs) -> CalibrationSettingsResponse:
        dst_buffer = kwargs.get("dst_buffer", self.CalibrationSettingsResponse())
        _validate_call(_lib.ivm_get_calibration_settings(self._handle, byref(dst_buffer)))
        return dst_buffer

    @overload
    def set_calibration_settings(
            self,
            dac_mult: Union[float, c_float],
            dac_offset: Union[float, c_float],
            adc_mult: Union[float, c_float],
            adcv_offset: Union[float, c_float],
            current_sense1_mult: Union[float, c_float],
            current_sense1_offset: Union[float, c_float],
            current_sense2_mult: Union[float, c_float],
            current_sense2_offset: Union[float, c_float],
            current_sense3_mult: Union[float, c_float],
            current_sense3_offset: Union[float, c_float]
    ) -> None: pass

    @overload
    def set_calibration_settings(
            self,
            src_buffer: CalibrationSettingsRequest
    ) -> None: pass

    def set_calibration_settings(self, *args) -> None:
        src_buffer = None
        if len(args) != 1 or not isinstance(args[0], self.CalibrationSettingsRequest):
            src_buffer = self.CalibrationSettingsRequest(
                dac_mult=_normalize_arg(args[0], c_float),
                dac_offset=_normalize_arg(args[1], c_float),
                adc_mult=_normalize_arg(args[2], c_float),
                adcv_offset=_normalize_arg(args[3], c_float),
                current_sense1_mult=_normalize_arg(args[4], c_float),
                current_sense1_offset=_normalize_arg(args[5], c_float),
                current_sense2_mult=_normalize_arg(args[6], c_float),
                current_sense2_offset=_normalize_arg(args[7], c_float),
                current_sense3_mult=_normalize_arg(args[8], c_float),
                current_sense3_offset=_normalize_arg(args[9], c_float)
            )
        else:
            src_buffer = args[0]
        _validate_call(_lib.ivm_set_calibration_settings(self._handle, byref(src_buffer)))

    def __init__(self, uri, defer_open=False):
        if isinstance(uri, str):
            uri = uri.encode("utf-8")

        if not isinstance(uri, (bytes, bytearray)):
            raise ValueError()
        self._uri = uri
        self._handle = None
        if not defer_open:
            self.open()

    if version_info >= (3, 4):
        def __del__(self):
            if self._handle:
                self.close()

    @property
    def uri(self):
        return self._uri

    def open(self):
        if self._handle is not None:
            return False

        handle = _lib.ivm_open_device(self._uri)
        if handle.value == _DeviceUndefined:
            raise RuntimeError()

        self._handle = handle
        return True

    def close(self):
        if self._handle is None:
            return False

        try:
            result = _lib.ivm_close_device(byref(self._handle))
            if result != _Ok:
                raise RuntimeError()
        except:
            raise
        else:
            return True
        finally:
            self._handle = None

    def get_profile(self):
        buffer = c_char_p()

        @CFUNCTYPE(c_void_p, c_size_t)
        def allocate(size):
            # http://bugs.python.org/issue1574593
            return cast(create_string_buffer(size+1), c_void_p).value

        _validate_call(_lib.ivm_get_profile(self._handle, byref(buffer), allocate))

        return buffer.value.decode("utf-8")

    def set_profile(self, source):
        if isinstance(source, str):
            source = source.encode("utf-8")
        _validate_call(_lib.ivm_set_profile(self._handle, c_char_p(source), len(source)))
