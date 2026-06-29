#!/usr/bin/env python3

from bme68x import BME68X
import bme68xConstants as cnst
import bsecConstants as bsec
import time
from datetime import datetime, timezone
import logging


class AmbientMonitor:
    def __init__(self):
        self.logger = logging.getLogger("AmbientMonitor")
        self.elapsed_time = "N/A"
        self._start_time = None

        self._sensor = BME68X(cnst.BME68X_I2C_ADDR_HIGH, 0)
        self._sensor.set_sample_rate(bsec.BSEC_SAMPLE_RATE_LP)
        self._sensor.set_heatr_conf(1, 320, 100, 1)  # 320°C for 100 ms, 1 profile

    def _update_elapsed_time(self, current_time):
        if self._start_time is None:
            self._start_time = current_time

        etime = current_time - self._start_time
        total_seconds = int(etime.total_seconds())

        days, remainder = divmod(total_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)

        self.elapsed_time = "Elapsed time: "
        if days > 0:
            self.elapsed_time += f"{days} days, {hours:02d}:{minutes:02d}:{seconds:02d}"
        elif hours > 0:
            self.elapsed_time += f"{hours}:{minutes:02d}:{seconds:02d}"
        elif minutes > 0:
            self.elapsed_time += f"{minutes}:{seconds:02d}"
        else:
            self.elapsed_time += f"{int(etime.total_seconds())} sec."

    @staticmethod
    def _thom_discomfort_index(temperature, humidity):
        # Calculate the Thom Discomfort Index
        return temperature - 0.55 * (1 - humidity / 100) * (temperature - 14.5)

    def get_data(self):
        try:
            bsec_data = self._sensor.get_bsec_data()
        except Exception as e:
            self.logger.error("Error while reading sensor data:", e)
            return None
        if bsec_data == {}:
            return None

        timestamp = datetime.now(timezone.utc)
        self._update_elapsed_time(timestamp)
        return {
            'timestamp': timestamp,
            'temperature': bsec_data['temperature'] if 'temperature' in bsec_data else 0,
            'humidity': bsec_data['humidity'] if 'humidity' in bsec_data else 0,
            'pressure': bsec_data['raw_pressure'] / 100 if 'raw_pressure' in bsec_data else 0,  # Convert Pa to hPa
            'gas': bsec_data['raw_gas'] if 'raw_gas' in bsec_data else 0,  # Ohms
            'iaq': bsec_data['iaq'] if 'iaq' in bsec_data else 0,  # Indoor Air Quality
            'thom_discomfort_index': AmbientMonitor._thom_discomfort_index(
                bsec_data['temperature'] if 'temperature' in bsec_data else 0,
                bsec_data['humidity'] if 'humidity' in bsec_data else 0
            )
        }


if __name__ == "__main__":
    monitor = AmbientMonitor()
    while True:
        data = monitor.get_data()
        if data is not None:
            print(f"{monitor.elapsed_time}, "
                f"Temperature: {data['temperature']:.1f} °C, "
                f"Humidity: {data['humidity']:.1f} %, "
                f"Pressure: {data['pressure']:.1f} hPa, "
                f"Gas: {data['gas']} ohms, "
                f"IAQ: {data['iaq']:.1f}, "
                f"Thom Discomfort Index: {data['thom_discomfort_index']:.1f}",
                flush=True)
        time.sleep(3)
