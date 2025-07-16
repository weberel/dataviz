# Dataviz - Biogas Sensor Visualization

A Python library for quick plotting and visualization of biogas sensor data, with support for live plotting and dashboard interfaces.

## Features

- **Quick plotting functions** with automatic subplot detection
- **Sensor data simulation** for testing without hardware
- **Live updating plots** for real-time data monitoring
- **Interactive dashboard** with multiple views
- **Serial port integration** for real sensor data
- **Flexible data input** (pandas DataFrames, numpy arrays, lists, dictionaries)

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

### Basic Plotting

```python
from quick_plot import quick_plot, plot_dataframe
import pandas as pd
import numpy as np

# Quick plot with arrays
data = np.random.randn(100)
fig = quick_plot(data, title="My Data")

# Plot DataFrame columns
df = pd.DataFrame({
    'temp': np.random.normal(25, 2, 100),
    'flow': np.random.exponential(2, 100)
})
fig = plot_dataframe(df, title="Sensor Data")
```

### Sensor Data Simulation

```python
from sensor_simulator import BiogasSensorSimulator

# Create simulator
simulator = BiogasSensorSimulator()

# Generate data
df = simulator.generate_dataframe(duration_minutes=30)

# Plot sensor data
from quick_plot import plot_sensor_data
fig = plot_sensor_data(df=df, title="Simulated Biogas Sensor")
```

### Live Plotting

```python
from live_plot import LivePlotter
from sensor_simulator import ThreadedSensorSimulator

# Create simulator
sim = ThreadedSensorSimulator()
sim.start()

# Create live plot
plotter = LivePlotter(data_source=sim)
plotter.setup_plot(variables=['temp', 'flow', 'pressure'])
plotter.start()  # Shows live updating plot
```

### Dashboard

```python
from dashboard import BiogasDashboard

# Create dashboard
dashboard = BiogasDashboard(use_simulator=True)

# Run dashboard (opens in browser at localhost:8050)
dashboard.run()
```

## Modules

### `quick_plot.py`
- `quick_plot()`: Universal plotting function with automatic subplot detection
- `plot_dataframe()`: Plot pandas DataFrame columns
- `plot_sensor_data()`: Specialized for biogas sensor data format

### `sensor_simulator.py`
- `BiogasSensorSimulator`: Simulates realistic biogas sensor data
- `ThreadedSensorSimulator`: Background data generation
- Supports JSON and CSV output formats matching real sensor

### `live_plot.py`
- `LivePlotter`: Live updating plots with multiple subplots
- `MultiVariableLivePlot`: Multiple variables in single plot
- Real-time data visualization

### `dashboard.py`
- `BiogasDashboard`: Interactive web dashboard
- `SerialDataReader`: Read data from serial ports
- Multiple plot views and data table

## Data Formats

The library supports biogas sensor data with these fields:

```python
{
    'datetime': '2024-01-01T12:00:00',
    'temp_degC': 25.5,
    'humidity_perc_rH': 65.0,
    'flow': 10.2,
    'concentration_ch4': 62.3,
    'pressure': 101.3,
    # ... additional thermistor readings
}
```

## Examples

Run the examples to see all features:

```bash
python examples.py
```

Or run specific examples:

```python
from examples import example_basic_plotting, example_live_plotting
example_basic_plotting()
example_live_plotting()
```

## Serial Port Usage

For real sensor data:

```python
# Dashboard with serial port
dashboard = BiogasDashboard(data_source='/dev/ttyUSB0', use_simulator=False)
dashboard.run()

# Direct serial reading
from dashboard import SerialDataReader
reader = SerialDataReader(port='/dev/ttyUSB0')
reader.start()
data = reader.get_latest_data()
```

## Customization

### Adjust simulator parameters:

```python
simulator = BiogasSensorSimulator(
    base_temp=30.0,
    base_flow=15.0,
    noise_level=0.1
)
```

### Create custom live plots:

```python
from live_plot import create_custom_live_plot

def my_data_source():
    return {'value1': random.random(), 'value2': random.random()}

plotter = create_custom_live_plot(
    data_function=my_data_source,
    variables=['value1', 'value2'],
    title="Custom Live Plot"
)
plotter.start()
```

### Customize quick plots:

```python
fig = quick_plot(
    data=df,
    x='time_column',
    y=['var1', 'var2'],
    color='pressure',
    title="Custom Plot",
    figsize=(12, 8)
)
```

## Architecture

```
dataviz/
├── quick_plot.py      # Basic plotting functions
├── sensor_simulator.py # Data simulation
├── live_plot.py       # Live plotting
├── dashboard.py       # Web dashboard
├── examples.py        # Usage examples
└── requirements.txt   # Dependencies
```

## Dependencies

- matplotlib (plotting)
- pandas (data handling)
- numpy (numerical operations)
- plotly + dash (interactive dashboard)
- pyserial (serial communication)
- seaborn (enhanced plotting)