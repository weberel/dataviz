import requests
import json
import time
import threading
from datetime import datetime, timedelta
from collections import deque
from typing import Dict, Any, Optional, List, Union
import pandas as pd


class ThingsBoardClient:
    """Client for connecting to ThingsBoard API."""
    
    def __init__(self, 
                 host: str = "localhost",
                 port: int = 8080,
                 username: str = "tenant@thingsboard.org",
                 password: str = "tenant",
                 use_ssl: bool = False):
        """
        Initialize ThingsBoard client.
        
        Parameters:
        -----------
        host : str
            ThingsBoard server hostname
        port : int
            ThingsBoard server port
        username : str
            Username for authentication
        password : str
            Password for authentication
        use_ssl : bool
            Whether to use HTTPS
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_ssl = use_ssl
        
        # Build base URL
        protocol = "https" if use_ssl else "http"
        self.base_url = f"{protocol}://{host}:{port}"
        
        # Authentication
        self.token = None
        self.refresh_token = None
        self.token_expires = None
        
    def authenticate(self) -> bool:
        """Authenticate with ThingsBoard."""
        try:
            auth_url = f"{self.base_url}/api/auth/login"
            auth_data = {
                "username": self.username,
                "password": self.password
            }
            
            response = requests.post(auth_url, json=auth_data)
            response.raise_for_status()
            
            auth_result = response.json()
            self.token = auth_result.get("token")
            self.refresh_token = auth_result.get("refreshToken")
            
            # Token typically expires in 1 hour
            self.token_expires = datetime.now() + timedelta(hours=1)
            
            print(f"✓ Successfully authenticated with ThingsBoard at {self.base_url}")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"✗ Authentication failed: {e}")
            return False
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers with authentication token."""
        if not self.token:
            raise ValueError("Not authenticated. Call authenticate() first.")
        
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def _check_token_expiry(self):
        """Check if token needs refreshing."""
        if self.token_expires and datetime.now() > self.token_expires:
            print("Token expired, re-authenticating...")
            self.authenticate()
    
    def get_devices(self) -> List[Dict[str, Any]]:
        """Get list of devices."""
        self._check_token_expiry()
        
        try:
            url = f"{self.base_url}/api/tenant/devices"
            response = requests.get(url, headers=self._get_headers())
            response.raise_for_status()
            
            devices = response.json().get("data", [])
            return devices
            
        except requests.exceptions.RequestException as e:
            print(f"Error getting devices: {e}")
            return []
    
    def get_device_by_name(self, device_name: str) -> Optional[Dict[str, Any]]:
        """Get device by name."""
        devices = self.get_devices()
        for device in devices:
            if device.get("name") == device_name:
                return device
        return None
    
    def get_telemetry_keys(self, device_id: str) -> List[str]:
        """Get available telemetry keys for a device."""
        self._check_token_expiry()
        
        try:
            url = f"{self.base_url}/api/plugins/telemetry/DEVICE/{device_id}/keys/timeseries"
            response = requests.get(url, headers=self._get_headers())
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Error getting telemetry keys: {e}")
            return []
    
    def get_latest_telemetry(self, device_id: str, keys: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get latest telemetry values for a device."""
        self._check_token_expiry()
        
        try:
            url = f"{self.base_url}/api/plugins/telemetry/DEVICE/{device_id}/values/timeseries"
            
            params = {}
            if keys:
                params["keys"] = ",".join(keys)
            
            response = requests.get(url, headers=self._get_headers(), params=params)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Error getting latest telemetry: {e}")
            return {}
    
    def get_telemetry_history(self, 
                            device_id: str, 
                            keys: List[str],
                            start_time: Optional[datetime] = None,
                            end_time: Optional[datetime] = None,
                            limit: int = 100) -> Dict[str, List[Dict[str, Any]]]:
        """Get historical telemetry data."""
        self._check_token_expiry()
        
        if start_time is None:
            start_time = datetime.now() - timedelta(hours=1)
        if end_time is None:
            end_time = datetime.now()
        
        try:
            url = f"{self.base_url}/api/plugins/telemetry/DEVICE/{device_id}/values/timeseries"
            
            params = {
                "keys": ",".join(keys),
                "startTs": int(start_time.timestamp() * 1000),
                "endTs": int(end_time.timestamp() * 1000),
                "limit": limit
            }
            
            response = requests.get(url, headers=self._get_headers(), params=params)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Error getting telemetry history: {e}")
            return {}


class ThingsBoardSensorReader:
    """Read sensor data from ThingsBoard device."""
    
    def __init__(self, 
                 client: ThingsBoardClient,
                 device_name: str,
                 telemetry_keys: List[str],
                 max_buffer_size: int = 1000):
        """
        Initialize ThingsBoard sensor reader.
        
        Parameters:
        -----------
        client : ThingsBoardClient
            Authenticated ThingsBoard client
        device_name : str
            Name of the device in ThingsBoard
        telemetry_keys : list of str
            List of telemetry keys to read (e.g., ['temperature', 'humidity'])
        max_buffer_size : int
            Maximum buffer size for data storage
        """
        self.client = client
        self.device_name = device_name
        self.telemetry_keys = telemetry_keys
        self.max_buffer_size = max_buffer_size
        
        # Find device
        self.device = client.get_device_by_name(device_name)
        if not self.device:
            raise ValueError(f"Device '{device_name}' not found")
        
        self.device_id = self.device["id"]["id"]
        print(f"✓ Found device: {device_name} (ID: {self.device_id})")
        
        # Data storage
        self.data_buffer = deque(maxlen=max_buffer_size)
        self.running = False
        self.thread = None
        
        # Verify telemetry keys exist
        available_keys = client.get_telemetry_keys(self.device_id)
        missing_keys = [key for key in telemetry_keys if key not in available_keys]
        if missing_keys:
            print(f"⚠ Warning: These telemetry keys not found: {missing_keys}")
            print(f"Available keys: {available_keys}")
    
    def get_latest_reading(self) -> Optional[Dict[str, Any]]:
        """Get latest sensor reading."""
        try:
            telemetry = self.client.get_latest_telemetry(self.device_id, self.telemetry_keys)
            
            if not telemetry:
                return None
            
            # Convert ThingsBoard format to our format
            reading = {
                'timestamp': datetime.now(),
                'device_name': self.device_name,
                'device_id': self.device_id
            }
            
            for key, data_list in telemetry.items():
                if data_list and len(data_list) > 0:
                    # Get the latest value
                    latest_data = data_list[0]
                    reading[key] = latest_data.get('value')
                    
                    # Convert timestamp if available
                    if 'ts' in latest_data:
                        reading[f'{key}_timestamp'] = datetime.fromtimestamp(latest_data['ts'] / 1000)
            
            return reading
            
        except Exception as e:
            print(f"Error getting latest reading: {e}")
            return None
    
    def get_historical_data(self, 
                          hours_back: int = 1,
                          limit: int = 100) -> pd.DataFrame:
        """Get historical data as DataFrame."""
        try:
            start_time = datetime.now() - timedelta(hours=hours_back)
            end_time = datetime.now()
            
            telemetry = self.client.get_telemetry_history(
                self.device_id, 
                self.telemetry_keys,
                start_time=start_time,
                end_time=end_time,
                limit=limit
            )
            
            if not telemetry:
                return pd.DataFrame()
            
            # Convert to DataFrame
            data_rows = []
            
            # Get all timestamps from all keys
            all_timestamps = set()
            for key, data_list in telemetry.items():
                for data_point in data_list:
                    all_timestamps.add(data_point['ts'])
            
            # Create rows for each timestamp
            for ts in sorted(all_timestamps):
                row = {
                    'timestamp': datetime.fromtimestamp(ts / 1000),
                    'device_name': self.device_name
                }
                
                # Add values for each key at this timestamp
                for key, data_list in telemetry.items():
                    # Find value for this timestamp
                    value = None
                    for data_point in data_list:
                        if data_point['ts'] == ts:
                            value = data_point['value']
                            break
                    
                    row[key] = value
                
                data_rows.append(row)
            
            df = pd.DataFrame(data_rows)
            df.set_index('timestamp', inplace=True)
            df.sort_index(inplace=True)
            
            return df
            
        except Exception as e:
            print(f"Error getting historical data: {e}")
            return pd.DataFrame()
    
    def start_continuous_reading(self, interval: float = 5.0):
        """Start reading data continuously in background thread."""
        if self.running:
            print("Reader already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._read_loop, args=(interval,))
        self.thread.daemon = True
        self.thread.start()
        print(f"✓ Started continuous reading every {interval} seconds")
    
    def stop_continuous_reading(self):
        """Stop continuous reading."""
        if not self.running:
            return
        
        self.running = False
        if self.thread:
            self.thread.join()
        print("✓ Stopped continuous reading")
    
    def _read_loop(self, interval: float):
        """Continuous reading loop."""
        while self.running:
            try:
                reading = self.get_latest_reading()
                if reading:
                    self.data_buffer.append(reading)
                
                time.sleep(interval)
                
            except Exception as e:
                print(f"Error in reading loop: {e}")
                time.sleep(interval)
    
    def get_buffered_data(self) -> List[Dict[str, Any]]:
        """Get all buffered data."""
        return list(self.data_buffer)
    
    def get_latest_from_buffer(self) -> Optional[Dict[str, Any]]:
        """Get latest data from buffer."""
        if len(self.data_buffer) > 0:
            return self.data_buffer[-1]
        return None


# Example usage functions
def example_thingsboard_connection():
    """Example: Connect to ThingsBoard and list devices."""
    # Configure your ThingsBoard connection
    client = ThingsBoardClient(
        host="demo.thingsboard.io",  # or your ThingsBoard server
        port=443,
        username="tenant@thingsboard.org",
        password="tenant",
        use_ssl=True
    )
    
    # Authenticate
    if not client.authenticate():
        print("Failed to authenticate")
        return
    
    # List devices
    devices = client.get_devices()
    print(f"Found {len(devices)} devices:")
    
    for device in devices:
        print(f"  - {device['name']} (ID: {device['id']['id']})")
        
        # Get telemetry keys for this device
        keys = client.get_telemetry_keys(device['id']['id'])
        print(f"    Telemetry keys: {keys}")


def example_sensor_data_reading():
    """Example: Read data from a specific device."""
    # Configure your ThingsBoard connection
    client = ThingsBoardClient(
        host="demo.thingsboard.io",
        port=443,
        username="tenant@thingsboard.org", 
        password="tenant",
        use_ssl=True
    )
    
    if not client.authenticate():
        return
    
    # Create sensor reader for your device
    try:
        reader = ThingsBoardSensorReader(
            client=client,
            device_name="DHT22 Demo Device",  # Replace with your device name
            telemetry_keys=["temperature", "humidity"]  # Replace with your keys
        )
        
        # Get latest reading
        latest = reader.get_latest_reading()
        print(f"Latest reading: {latest}")
        
        # Get historical data
        df = reader.get_historical_data(hours_back=24)
        print(f"Historical data: {len(df)} records")
        print(df.head())
        
    except ValueError as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    print("ThingsBoard Integration Examples")
    print("=" * 40)
    
    print("\n1. Testing connection and listing devices...")
    example_thingsboard_connection()
    
    print("\n2. Reading sensor data...")
    example_sensor_data_reading()