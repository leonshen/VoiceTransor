# -*- coding: utf-8 -*-
"""Best-effort CPU temperature and utilization readings (Windows-first)."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

import psutil


@dataclass
class ThermalConfig:
    enabled: bool = True
    high_c: float = 85.0
    critical_c: float = 95.0
    cooldown_ms_base: int = 200
    cooldown_ms_hot: int = 800
    poll_ms: int = 1000
    fallback_use_cpu_percent: bool = True
    cpu_hot_pct: int = 85


def get_cpu_temp_c() -> Optional[float]:
    """Return CPU/package temperature in Celsius if available; else None.

    Order of attempts:
      1) psutil.sensors_temperatures()
      2) OpenHardwareMonitor WMI (root\OpenHardwareMonitor)  <-- added
      3) Windows ACPI WMI (MSAcpi_ThermalZoneTemperature)
    """
    # 1) psutil sensors (works on many Linux distros; sometimes on Windows with proper drivers)
    try:
        temps = psutil.sensors_temperatures()
        if temps:
            # try common keys
            for key in ("coretemp", "k10temp", "acpitz", "cpu_thermal", "nvme", "pch_cannonlake"):
                if key in temps:
                    vals = [t.current for t in temps[key] if t.current is not None]
                    if vals:
                        v = max(vals)
                        if 0 < v < 120:
                            return float(v)
            # otherwise search any plausible value
            all_vals = []
            for arr in temps.values():
                all_vals.extend([t.current for t in arr if t.current is not None])
            if all_vals:
                v = max(all_vals)
                if 0 < v < 120:
                    return float(v)
    except Exception:
        pass

    # 2) OpenHardwareMonitor WMI (requires OHM to be running; often needs admin rights)
    try:
        import wmi  # type: ignore
        ow = wmi.WMI(namespace="root\\OpenHardwareMonitor")
        candidates = []
        for sensor in ow.Sensor():
            stype = getattr(sensor, "SensorType", None)
            name = (getattr(sensor, "Name", "") or "")
            value = getattr(sensor, "Value", None)
            if stype and str(stype).lower() == "temperature" and "cpu" in name.lower():
                if value is not None:
                    try:
                        v = float(value)
                        if 0 < v < 120:
                            candidates.append(v)
                    except Exception:
                        pass
        if candidates:
            return max(candidates)
    except Exception:
        pass

    # 3) Windows ACPI WMI (may report ambient/zone temps; not always CPU package)
    try:
        import wmi  # type: ignore
        w = wmi.WMI(namespace="root\\WMI")
        for sensor in w.MSAcpi_ThermalZoneTemperature():
            kelvin10 = getattr(sensor, "CurrentTemperature", None)
            if kelvin10:
                c = float(kelvin10) / 10.0 - 273.15  # tenths of Kelvin -> °C
                if 0 < c < 120:
                    return c
    except Exception:
        pass

    # 4) As a last resort, temperature not available
    return None

def get_cpu_percent() -> float:
    """Return current overall CPU utilization percentage."""
    try:
        return float(psutil.cpu_percent(interval=0.2))
    except Exception:
        return 0.0
