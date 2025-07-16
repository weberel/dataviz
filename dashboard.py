# Optional dashboard imports
try:
    import dash
    from dash import dcc, html, Input, Output, State, callback
    import plotly.graph_objs as go
    import plotly.express as px
    HAS_DASH = True
except ImportError:
    HAS_DASH = False
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import threading
import time
from collections import deque
# Optional serial import
try:
    import serial
    HAS_SERIAL = True
except ImportError:
    HAS_SERIAL = False
from sensor_simulator import BiogasSensorSimulator, ThreadedSensorSimulator
from typing import Dict, Any, Optional, List


class SerialDataReader:
    """Read data from serial port."""
    
    def __init__(self, port: str = '/dev/ttyUSB0', baudrate: int = 9600, 
                 timeout: float = 1.0, max_buffer_size: int = 1000):
        """
        Initialize serial data reader.
        
        Parameters:
        -----------
        port : str
            Serial port device
        baudrate : int
            Baud rate
        timeout : float
            Read timeout
        max_buffer_size : int
            Maximum buffer size
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.max_buffer_size = max_buffer_size
        
        self.serial_connection = None
        self.data_buffer = deque(maxlen=max_buffer_size)
        self.running = False
        self.thread = None
        
    def connect(self):
        """Connect to serial port."""
        if not HAS_SERIAL:
            print("Error: pyserial not installed. Install with: pip install pyserial")
            return False
        
        try:
            self.serial_connection = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout
            )
            return True
        except Exception as e:
            print(f"Error connecting to serial port: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from serial port."""
        self.stop()
        if self.serial_connection:
            self.serial_connection.close()
            self.serial_connection = None
    
    def parse_serial_line(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse a line from serial port."""
        try:
            # Try JSON format first
            if line.strip().startswith('{'):
                return json.loads(line.strip())
            
            # Try comma-separated format
            parts = line.strip().split(',')
            if len(parts) >= 5:
                return {
                    'timestamp': datetime.now(),
                    'state': int(float(parts[0])),
                    'temp': float(parts[1]),
                    'pressure': float(parts[2]),
                    'flow': float(parts[3]),
                    'comp': float(parts[4])
                }
        except Exception as e:
            print(f"Error parsing line: {line.strip()}, Error: {e}")
        
        return None
    
    def read_data(self):
        """Read data from serial port continuously."""
        while self.running and self.serial_connection:
            try:
                line = self.serial_connection.readline().decode('utf-8', errors='ignore')
                if line:
                    data = self.parse_serial_line(line)
                    if data:
                        self.data_buffer.append(data)
            except Exception as e:
                print(f"Error reading serial data: {e}")
                time.sleep(0.1)
    
    def start(self):
        """Start reading data in background thread."""
        if not self.connect():
            return False
        
        self.running = True
        self.thread = threading.Thread(target=self.read_data)
        self.thread.daemon = True
        self.thread.start()
        return True
    
    def stop(self):
        """Stop reading data."""
        self.running = False
        if self.thread:
            self.thread.join()
    
    def get_latest_data(self) -> Optional[Dict[str, Any]]:
        """Get latest data point."""
        if len(self.data_buffer) > 0:
            return self.data_buffer[-1]
        return None
    
    def get_data_buffer(self) -> List[Dict[str, Any]]:
        """Get all data in buffer."""
        return list(self.data_buffer)


class BiogasDashboard:
    """Interactive dashboard for biogas sensor data."""
    
    def __init__(self, 
                 data_source: Optional[str] = None,
                 use_simulator: bool = True,
                 max_points: int = 500):
        """
        Initialize dashboard.
        
        Parameters:
        -----------
        data_source : str (optional)
            Serial port for real sensor data
        use_simulator : bool
            Whether to use simulator if no real data
        max_points : int
            Maximum points to display
        """
        self.data_source = data_source
        self.use_simulator = use_simulator
        self.max_points = max_points
        
        # Data storage
        self.data_buffer = deque(maxlen=max_points)
        
        # Initialize data source
        if data_source:
            self.serial_reader = SerialDataReader(port=data_source)
        else:
            self.serial_reader = None
        
        if use_simulator:
            self.simulator = BiogasSensorSimulator()
            self.threaded_sim = ThreadedSensorSimulator(self.simulator)
        else:
            self.simulator = None
            self.threaded_sim = None
        
        # Create Dash app
        if not HAS_DASH:
            raise ImportError("Dash not installed. Install with: pip install dash plotly")
        
        self.app = dash.Dash(__name__)
        self.setup_layout()
        self.setup_callbacks()
    
    def setup_layout(self):
        """Setup dashboard layout."""
        self.app.layout = html.Div([
            html.H1("Biogas Sensor Dashboard", 
                   style={'text-align': 'center', 'color': '#2c3e50'}),
            
            # Control panel
            html.Div([
                html.Div([
                    html.Label("Data Source:"),
                    dcc.Dropdown(
                        id='data-source-dropdown',
                        options=[
                            {'label': 'Simulator', 'value': 'simulator'},
                            {'label': 'Serial Port', 'value': 'serial'}
                        ],
                        value='simulator' if self.use_simulator else 'serial',
                        style={'width': '200px'}
                    )
                ], style={'display': 'inline-block', 'margin': '10px'}),
                
                html.Div([
                    html.Label("Serial Port:"),
                    dcc.Input(
                        id='serial-port-input',
                        type='text',
                        value=self.data_source or '/dev/ttyUSB0',
                        style={'width': '150px'}
                    )
                ], style={'display': 'inline-block', 'margin': '10px'}),
                
                html.Div([
                    html.Button('Start', id='start-button', n_clicks=0,
                               style={'margin': '5px', 'background-color': '#27ae60', 'color': 'white'}),
                    html.Button('Stop', id='stop-button', n_clicks=0,
                               style={'margin': '5px', 'background-color': '#e74c3c', 'color': 'white'}),
                    html.Button('Clear', id='clear-button', n_clicks=0,
                               style={'margin': '5px', 'background-color': '#f39c12', 'color': 'white'})
                ], style={'display': 'inline-block', 'margin': '10px'})
            ], style={'background-color': '#ecf0f1', 'padding': '10px', 'border-radius': '5px'}),
            
            # Status display
            html.Div(id='status-display', style={'margin': '10px', 'padding': '10px', 
                                                'background-color': '#d5dbdb', 'border-radius': '5px'}),
            
            # Main plots
            html.Div([
                html.Div([
                    dcc.Graph(id='temperature-plot', style={'height': '300px'})
                ], style={'width': '48%', 'display': 'inline-block'}),
                
                html.Div([
                    dcc.Graph(id='flow-plot', style={'height': '300px'})
                ], style={'width': '48%', 'display': 'inline-block', 'margin-left': '2%'}),
            ]),
            
            html.Div([
                html.Div([
                    dcc.Graph(id='pressure-plot', style={'height': '300px'})
                ], style={'width': '48%', 'display': 'inline-block'}),
                
                html.Div([
                    dcc.Graph(id='composition-plot', style={'height': '300px'})
                ], style={'width': '48%', 'display': 'inline-block', 'margin-left': '2%'}),
            ]),
            
            # Multi-variable plot
            html.Div([
                dcc.Graph(id='multivar-plot', style={'height': '400px'})
            ], style={'margin': '10px'}),
            
            # Data table
            html.Div([
                html.H3("Recent Data"),
                html.Div(id='data-table')
            ], style={'margin': '10px'}),
            
            # Auto-refresh
            dcc.Interval(
                id='interval-component',
                interval=1000,  # 1 second
                n_intervals=0,
                disabled=True
            ),
            
            # Store for data
            dcc.Store(id='data-store', data=[])
        ])
    
    def setup_callbacks(self):
        """Setup dashboard callbacks."""
        
        @self.app.callback(
            [Output('interval-component', 'disabled'),
             Output('status-display', 'children')],
            [Input('start-button', 'n_clicks'),
             Input('stop-button', 'n_clicks'),
             Input('data-source-dropdown', 'value'),
             Input('serial-port-input', 'value')]
        )
        def control_data_collection(start_clicks, stop_clicks, data_source, serial_port):
            """Control data collection."""
            ctx = dash.callback_context
            if not ctx.triggered:
                return True, "Ready to start data collection"
            
            button_id = ctx.triggered[0]['prop_id'].split('.')[0]
            
            if button_id == 'start-button':
                if data_source == 'simulator':
                    if self.threaded_sim:
                        self.threaded_sim.start(interval=0.5)
                    status = "Simulator started"
                else:
                    if self.serial_reader:
                        self.serial_reader.port = serial_port
                        if self.serial_reader.start():
                            status = f"Connected to {serial_port}"
                        else:
                            status = f"Failed to connect to {serial_port}"
                    else:
                        status = "Serial reader not available"
                
                return False, status
            
            elif button_id == 'stop-button':
                if self.threaded_sim:
                    self.threaded_sim.stop()
                if self.serial_reader:
                    self.serial_reader.stop()
                
                return True, "Data collection stopped"
            
            return True, "Ready"
        
        @self.app.callback(
            Output('data-store', 'data'),
            [Input('interval-component', 'n_intervals'),
             Input('clear-button', 'n_clicks'),
             Input('data-source-dropdown', 'value')],
            [State('data-store', 'data')]
        )
        def update_data_store(n_intervals, clear_clicks, data_source, stored_data):
            """Update data store."""
            ctx = dash.callback_context
            if ctx.triggered and ctx.triggered[0]['prop_id'] == 'clear-button.n_clicks':
                self.data_buffer.clear()
                return []
            
            # Get new data
            new_data = None
            if data_source == 'simulator' and self.threaded_sim:
                new_data = self.threaded_sim.get_latest_data()
            elif data_source == 'serial' and self.serial_reader:
                new_data = self.serial_reader.get_latest_data()
            
            if new_data:
                # Add timestamp if not present
                if 'timestamp' not in new_data:
                    new_data['timestamp'] = datetime.now()
                
                # Convert timestamp to string for JSON serialization
                new_data['timestamp_str'] = new_data['timestamp'].isoformat()
                
                # Add to buffer
                self.data_buffer.append(new_data)
                
                # Return last N points
                return list(self.data_buffer)[-self.max_points:]
            
            return stored_data
        
        @self.app.callback(
            [Output('temperature-plot', 'figure'),
             Output('flow-plot', 'figure'),
             Output('pressure-plot', 'figure'),
             Output('composition-plot', 'figure'),
             Output('multivar-plot', 'figure'),
             Output('data-table', 'children')],
            [Input('data-store', 'data')]
        )
        def update_plots(data):
            """Update all plots."""
            if not data:
                # Return empty plots
                empty_fig = go.Figure()
                empty_fig.update_layout(title="No data available")
                return empty_fig, empty_fig, empty_fig, empty_fig, empty_fig, "No data"
            
            # Convert to DataFrame
            df = pd.DataFrame(data)
            df['timestamp'] = pd.to_datetime(df['timestamp_str'])
            
            # Temperature plot
            temp_fig = go.Figure()
            temp_fig.add_trace(go.Scatter(x=df['timestamp'], y=df['temp'], 
                                         mode='lines', name='Temperature'))
            temp_fig.update_layout(title='Temperature (°C)', xaxis_title='Time', yaxis_title='Temperature')
            
            # Flow plot
            flow_fig = go.Figure()
            flow_fig.add_trace(go.Scatter(x=df['timestamp'], y=df['flow'], 
                                         mode='lines', name='Flow Rate', line=dict(color='green')))
            flow_fig.update_layout(title='Flow Rate', xaxis_title='Time', yaxis_title='Flow')
            
            # Pressure plot
            pressure_fig = go.Figure()
            pressure_fig.add_trace(go.Scatter(x=df['timestamp'], y=df['pressure'], 
                                             mode='lines', name='Pressure', line=dict(color='red')))
            pressure_fig.update_layout(title='Pressure (kPa)', xaxis_title='Time', yaxis_title='Pressure')
            
            # Composition plot
            comp_fig = go.Figure()
            if 'comp' in df.columns:
                comp_fig.add_trace(go.Scatter(x=df['timestamp'], y=df['comp'], 
                                             mode='lines', name='Compensation', line=dict(color='orange')))
            if 'ch4_concentration' in df.columns:
                comp_fig.add_trace(go.Scatter(x=df['timestamp'], y=df['ch4_concentration'], 
                                             mode='lines', name='CH4 %', line=dict(color='purple')))
            comp_fig.update_layout(title='Composition', xaxis_title='Time', yaxis_title='Value')
            
            # Multi-variable plot (normalized)
            multivar_fig = go.Figure()
            for col in ['temp', 'flow', 'pressure', 'comp']:
                if col in df.columns:
                    # Normalize values
                    values = df[col]
                    norm_values = (values - values.min()) / (values.max() - values.min()) if values.max() > values.min() else values
                    multivar_fig.add_trace(go.Scatter(x=df['timestamp'], y=norm_values, 
                                                     mode='lines', name=col))
            multivar_fig.update_layout(title='All Variables (Normalized)', xaxis_title='Time', yaxis_title='Normalized Value')
            
            # Data table
            recent_data = df.tail(10)
            table_html = html.Table([
                html.Thead([
                    html.Tr([html.Th(col) for col in ['Time', 'Temp', 'Flow', 'Pressure', 'Comp']])
                ]),
                html.Tbody([
                    html.Tr([
                        html.Td(row['timestamp'].strftime('%H:%M:%S')),
                        html.Td(f"{row['temp']:.2f}"),
                        html.Td(f"{row['flow']:.2f}"),
                        html.Td(f"{row['pressure']:.2f}"),
                        html.Td(f"{row['comp']:.3f}")
                    ]) for _, row in recent_data.iterrows()
                ])
            ], style={'width': '100%', 'border': '1px solid #ddd'})
            
            return temp_fig, flow_fig, pressure_fig, comp_fig, multivar_fig, table_html
    
    def run(self, host='127.0.0.1', port=8050, debug=False):
        """Run the dashboard."""
        self.app.run_server(host=host, port=port, debug=debug)
    
    def cleanup(self):
        """Cleanup resources."""
        if self.threaded_sim:
            self.threaded_sim.stop()
        if self.serial_reader:
            self.serial_reader.disconnect()


# Example usage
def run_dashboard():
    """Run the biogas sensor dashboard."""
    dashboard = BiogasDashboard(use_simulator=True)
    
    try:
        print("Starting dashboard at http://localhost:8050")
        dashboard.run(debug=False)
    except KeyboardInterrupt:
        print("Stopping dashboard...")
    finally:
        dashboard.cleanup()


if __name__ == '__main__':
    run_dashboard()