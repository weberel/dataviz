import numpy as np
import pandas as pd
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Generator
import threading
import queue


class BiogasSensorSimulator:
    """Simulates biogas sensor data output matching the real sensor format."""
    
    def __init__(self, 
                 base_temp: float = 25.0,
                 base_pressure: float = 101.325,
                 base_flow: float = 10.0,
                 base_ch4_concentration: float = 60.0,
                 noise_level: float = 0.05):
        """
        Initialize sensor simulator.
        
        Parameters:
        -----------
        base_temp : float
            Base temperature in Celsius
        base_pressure : float
            Base pressure in kPa
        base_flow : float
            Base flow rate
        base_ch4_concentration : float
            Base CH4 concentration percentage
        noise_level : float
            Noise level as fraction of base values
        """
        self.base_temp = base_temp
        self.base_pressure = base_pressure
        self.base_flow = base_flow
        self.base_ch4_concentration = base_ch4_concentration
        self.noise_level = noise_level
        
        # State tracking
        self.state = 2  # 0=measurement, 1=error, 2=normal
        self.time_offset = 0
        
        # Thermistor simulation parameters
        self.ambient_temp = base_temp
        self.flow_thermistor_offset = 5.0  # Temperature offset above ambient
        self.comp_thermistor_offset = 15.0  # Temperature offset above ambient
        
    def _add_noise(self, value: float, noise_factor: float = 1.0) -> float:
        """Add realistic noise to a value."""
        noise = np.random.normal(0, self.noise_level * noise_factor * abs(value))
        return value + noise
    
    def _generate_sine_variation(self, period_minutes: float = 10.0, amplitude: float = 0.1) -> float:
        """Generate slow sinusoidal variations."""
        t = time.time() + self.time_offset
        return amplitude * np.sin(2 * np.pi * t / (period_minutes * 60))
    
    def generate_sensor_reading(self) -> Dict[str, Any]:
        """Generate a single sensor reading matching the JSON format."""
        # Add slow variations
        temp_variation = self._generate_sine_variation(period_minutes=15, amplitude=2.0)
        flow_variation = self._generate_sine_variation(period_minutes=5, amplitude=0.2)
        ch4_variation = self._generate_sine_variation(period_minutes=20, amplitude=5.0)
        
        # Calculate current values
        current_temp = self._add_noise(self.base_temp + temp_variation)
        current_pressure = self._add_noise(self.base_pressure, 0.01)
        current_flow = self._add_noise(self.base_flow * (1 + flow_variation))
        current_ch4 = np.clip(self._add_noise(self.base_ch4_concentration + ch4_variation), 0, 100)
        
        # Simulate thermistor readings
        flow_temp = current_temp + self.flow_thermistor_offset
        comp_temp = current_temp + self.comp_thermistor_offset
        
        # Calculate power based on temperature (simplified model)
        flow_power = self._add_noise(0.5 + 0.01 * flow_temp)
        comp_power = self._add_noise(1.2 + 0.015 * comp_temp)
        
        # Calculate compensation ratio
        comp_ratio = self._add_noise(comp_power / flow_power)
        
        return {
            "type": "BOMAD_flow",
            "state": self.state,
            "temp": round(current_temp, 2),
            "pressure": round(current_pressure, 2),
            "flow": round(current_flow, 2),
            "comp": round(comp_ratio, 3),
            "ch4_concentration": round(current_ch4, 1)
        }
    
    def generate_csv_row(self) -> Dict[str, Any]:
        """Generate a single CSV row matching the calibration data format."""
        reading = self.generate_sensor_reading()
        
        # Extended format for CSV
        row = {
            'datetime': datetime.now().isoformat(),
            'state': reading['state'],
            'temp_degC': reading['temp'],
            'humidity_perc_rH': self._add_noise(65.0, 0.1),
            'flow': reading['flow'],
            'concentration_ch4': reading['ch4_concentration'],
        }
        
        # Add device-specific readings for d0 and d1
        for device in ['d0', 'd1']:
            multiplier = 1.0 if device == 'd0' else 1.05  # Slight difference between devices
            
            row.update({
                f'{device}_state': reading['state'],
                f'{device}_temp_ambient': self._add_noise(reading['temp'] * multiplier),
                f'{device}_pressure': self._add_noise(reading['pressure'] * multiplier),
                f'{device}_temp_flow': self._add_noise((reading['temp'] + self.flow_thermistor_offset) * multiplier),
                f'{device}_power_flow': self._add_noise(0.5 * multiplier),
                f'{device}_vin_flow': self._add_noise(3.3),
                f'{device}_vout_flow': self._add_noise(1.65 * multiplier),
                f'{device}_temp_comp': self._add_noise((reading['temp'] + self.comp_thermistor_offset) * multiplier),
                f'{device}_power_comp': self._add_noise(1.2 * multiplier),
                f'{device}_vin_comp': self._add_noise(3.3),
                f'{device}_vout_comp': self._add_noise(2.1 * multiplier),
            })
        
        return row
    
    def generate_serial_output(self) -> str:
        """Generate comma-separated serial output matching firmware format."""
        row = self.generate_csv_row()
        
        # Format: state,temp_avg,pressure_avg,flow_avg,comp_avg,state,T_ambient,pressure*10,T_flow,P_flow,Vin_flow,Vout_flow,T_comp,P_comp,Vin_comp,Vout_comp
        values = [
            row['state'],
            row['temp_degC'],
            row['d0_pressure'],
            row['flow'],
            row['concentration_ch4'] / 100.0,  # As ratio
            row['d0_state'],
            row['d0_temp_ambient'],
            row['d0_pressure'] * 10,  # Pressure * 10 as per format
            row['d0_temp_flow'],
            row['d0_power_flow'],
            row['d0_vin_flow'],
            row['d0_vout_flow'],
            row['d0_temp_comp'],
            row['d0_power_comp'],
            row['d0_vin_comp'],
            row['d0_vout_comp']
        ]
        
        return ','.join(str(round(v, 2)) for v in values)
    
    def stream_data(self, interval: float = 1.0) -> Generator[Dict[str, Any], None, None]:
        """
        Stream sensor data at specified interval.
        
        Parameters:
        -----------
        interval : float
            Time between readings in seconds
        
        Yields:
        -------
        Dict containing sensor reading
        """
        while True:
            yield self.generate_sensor_reading()
            time.sleep(interval)
    
    def simulate_serial_port(self, interval: float = 1.0) -> Generator[str, None, None]:
        """
        Simulate serial port output.
        
        Parameters:
        -----------
        interval : float
            Time between readings in seconds
        
        Yields:
        -------
        Comma-separated sensor values
        """
        while True:
            yield self.generate_serial_output()
            time.sleep(interval)
    
    def generate_dataframe(self, duration_minutes: int = 60, interval_seconds: float = 1.0) -> pd.DataFrame:
        """
        Generate a DataFrame of sensor data over specified duration.
        
        Parameters:
        -----------
        duration_minutes : int
            Duration to simulate in minutes
        interval_seconds : float
            Interval between readings in seconds
        
        Returns:
        --------
        pandas DataFrame with sensor data
        """
        n_samples = int(duration_minutes * 60 / interval_seconds)
        data = []
        
        start_time = datetime.now()
        for i in range(n_samples):
            self.time_offset = i * interval_seconds
            row = self.generate_csv_row()
            # Override datetime to simulate passage of time
            row['datetime'] = (start_time + timedelta(seconds=i * interval_seconds)).isoformat()
            data.append(row)
        
        df = pd.DataFrame(data)
        df['datetime'] = pd.to_datetime(df['datetime'])
        df.set_index('datetime', inplace=True)
        
        return df
    
    def set_error_state(self):
        """Set sensor to error state."""
        self.state = 1
    
    def set_measurement_state(self):
        """Set sensor to measurement state."""
        self.state = 0
    
    def set_normal_state(self):
        """Set sensor to normal state."""
        self.state = 2
    
    def adjust_flow(self, new_flow: float):
        """Adjust base flow rate."""
        self.base_flow = new_flow
    
    def adjust_ch4_concentration(self, new_concentration: float):
        """Adjust CH4 concentration."""
        self.base_ch4_concentration = np.clip(new_concentration, 0, 100)


class ThreadedSensorSimulator:
    """Threaded sensor simulator for background data generation."""
    
    def __init__(self, simulator: Optional[BiogasSensorSimulator] = None):
        self.simulator = simulator or BiogasSensorSimulator()
        self.data_queue = queue.Queue(maxsize=1000)
        self.running = False
        self.thread = None
        
    def start(self, interval: float = 1.0):
        """Start generating data in background thread."""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._generate_data, args=(interval,))
        self.thread.daemon = True
        self.thread.start()
    
    def stop(self):
        """Stop data generation."""
        self.running = False
        if self.thread:
            self.thread.join()
    
    def _generate_data(self, interval: float):
        """Generate data in background."""
        while self.running:
            try:
                data = self.simulator.generate_sensor_reading()
                data['timestamp'] = datetime.now()
                
                # Remove old data if queue is full
                if self.data_queue.full():
                    try:
                        self.data_queue.get_nowait()
                    except queue.Empty:
                        pass
                
                self.data_queue.put(data)
                time.sleep(interval)
            except Exception as e:
                print(f"Error in data generation: {e}")
    
    def get_latest_data(self) -> Optional[Dict[str, Any]]:
        """Get latest data point."""
        try:
            # Get all available data and return the latest
            latest = None
            while not self.data_queue.empty():
                latest = self.data_queue.get_nowait()
            return latest
        except queue.Empty:
            return None
    
    def get_all_data(self) -> List[Dict[str, Any]]:
        """Get all available data points."""
        data = []
        try:
            while not self.data_queue.empty():
                data.append(self.data_queue.get_nowait())
        except queue.Empty:
            pass
        return data


# Example usage functions
def example_simulate_and_save():
    """Example: Generate and save simulated sensor data."""
    simulator = BiogasSensorSimulator()
    
    # Generate 30 minutes of data
    df = simulator.generate_dataframe(duration_minutes=30, interval_seconds=1)
    
    # Save to CSV
    df.to_csv('simulated_sensor_data.csv')
    print(f"Generated {len(df)} data points")
    return df


def example_stream_json():
    """Example: Stream JSON data like the real sensor."""
    simulator = BiogasSensorSimulator()
    
    print("Streaming sensor data (press Ctrl+C to stop)...")
    try:
        for reading in simulator.stream_data(interval=1.0):
            print(json.dumps(reading))
    except KeyboardInterrupt:
        print("\nStopped streaming")


def example_serial_simulation():
    """Example: Simulate serial port output."""
    simulator = BiogasSensorSimulator()
    
    print("Simulating serial output (press Ctrl+C to stop)...")
    try:
        for line in simulator.simulate_serial_port(interval=0.5):
            print(line)
    except KeyboardInterrupt:
        print("\nStopped simulation")