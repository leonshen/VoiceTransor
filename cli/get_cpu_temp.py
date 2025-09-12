import wmi

w = wmi.WMI(namespace="root\\OpenHardwareMonitor")
for sensor in w.Sensor():
    if sensor.SensorType == u'Temperature' and "CPU" in sensor.Name:
        print(f"{sensor.Name}: {sensor.Value} °C")
