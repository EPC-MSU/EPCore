## IVM

This is a python binding for IVM cross-platform library for EyePoint Signature Analyzers.

![IVM](https://raw.githubusercontent.com/EPC-MSU/EPLab/851dc110dd48f778766e33a604f93fdae4b685a9/media/manual_eyepoints.jpg)

### Installation

```
pip install ivm
```

### Minimal example

```python
from ivm import IvmDeviceHandle
from math import ceil
import time

# Useful constants
MEASUREMENT_COMPLETE = IvmDeviceHandle.CheckMeasurementStatusResponse.ReadyStatus.MEASUREMENT_COMPLETE
FRAME_SIZE = IvmDeviceHandle.GetMeasurementRequest.FrameNumber.FRAME_SIZE

# Set correct device URI here
# Format for Windows: com:\\.\COM1
# Format for Linux: /dev/ttyACM1
# Format for MacOS: com:///dev/tty.usbmodem000001234
device_uri = r'com:\\.\COM4'

try:
    device = IvmDeviceHandle(device_uri)
    print("Device opened")
    print("Read device information... ", end="")
    device_info = device.get_identity_information()
    print("Done")
except RuntimeError:
    print("Cannot open device {}.".format(device_uri))
    print("Please check URI and try again.")
    exit()

print("  -- Device information --")
print("  Product: {} {}".format(
    bytes(device_info.manufacturer).decode("utf-8"),
    bytes(device_info.product_name).decode("utf-8")
))
print("  Hardware version: {}.{}.{}".format(
    device_info.hardware_major,
    device_info.hardware_minor,
    device_info.hardware_bugfix
))
print("  Serial number: {}".format(device_info.serial_number))
print("  Firmware version: {}.{}.{}".format(
    device_info.firmware_major,
    device_info.firmware_minor,
    device_info.firmware_bugfix
))

# Launch single measurement in non-blocking mode
print("Measuring IV-curve... ", end="")
device.start_measurement()
# Wait for measurement to finish
while device.check_measurement_status().ready_status != MEASUREMENT_COMPLETE:
    time.sleep(0.05)
print("Done")

# Number of points in a single curve measurement
number_of_points = device.get_measurement_settings().number_points
print("Number of points in a single curve measurement: {}".format(number_of_points))

# Get all measurement results
currents = []
voltages = []
# Measurements are stored in frames of size FRAME_SIZE
number_of_frames = ceil(number_of_points/FRAME_SIZE)
for frame_index in range(number_of_frames):
    currents += list(device.get_measurement(frame_index).current)
    voltages += list(device.get_measurement(frame_index).voltage)

print("List of measured currents (in mA):")
print(*("{:.4f}".format(k) for k in currents), sep=", ")

print("List of measured voltages (in V):")
print(*("{:.4f}".format(k) for k in voltages), sep=", ")

# Close the device
device.close_device()
print("Device closed")
```

### More information
For documentation, software, examples of using the API and bindings for Python and C#, you can visit the Eyepoint website:
* English version: https://eyepoint.physlab.ru/en/
* Russian version: https://eyepoint.physlab.ru/ru/. 