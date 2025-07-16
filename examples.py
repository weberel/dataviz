#!/usr/bin/env python3
"""
Example usage of the dataviz plotting functions.
"""

import sys

# Check for required packages
try:
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    print("✓ Core packages (pandas, numpy, matplotlib) available")
except ImportError as e:
    print(f"✗ Missing required package: {e}")
    print("Please install with: pip install pandas numpy matplotlib")
    sys.exit(1)

try:
    from quick_plot import quick_plot, plot_dataframe, plot_sensor_data
    from sensor_simulator import BiogasSensorSimulator, example_simulate_and_save
    print("✓ Core dataviz modules imported successfully")
except ImportError as e:
    print(f"✗ Error importing dataviz modules: {e}")
    sys.exit(1)

# Optional imports
try:
    from live_plot import example_live_plot_basic, example_live_plot_normalized
    HAS_LIVE_PLOT = True
except ImportError:
    HAS_LIVE_PLOT = False
    print("⚠ Live plotting not available (matplotlib animation issues)")

# Dashboard import will be checked when needed
HAS_DASHBOARD = None  # Will be checked later


def example_basic_plotting():
    """Example of basic quick plotting with different data types."""
    print("=== Basic Quick Plot Example ===")
    
    # Simple dictionary data
    print("Plotting sensor-like data...")
    data = {
        'temperature': np.random.normal(25, 2, 50),
        'pressure': np.random.normal(101, 0.5, 50),
        'flow': np.random.exponential(2, 50)
    }
    fig = quick_plot(data, title="Sensor Data")
    plt.show()


def example_dataframe_plotting():
    """Example of DataFrame plotting."""
    print("=== DataFrame Plotting Example ===")
    
    # Create sample DataFrame
    dates = pd.date_range('2024-01-01', periods=100, freq='1min')
    df = pd.DataFrame({
        'datetime': dates,
        'temperature': 25 + 2 * np.sin(np.arange(100) * 0.1) + np.random.normal(0, 0.5, 100),
        'flow': 10 + 2 * np.sin(np.arange(100) * 0.05) + np.random.normal(0, 0.5, 100)
    })
    
    print("Plotting DataFrame with time series...")
    fig = plot_dataframe(df, x_column='datetime', title="Time Series Data")
    plt.show()


def example_sensor_data_simulation():
    """Example of sensor data simulation and plotting."""
    print("=== Sensor Data Simulation Example ===")
    
    # Create simulator
    simulator = BiogasSensorSimulator()
    
    print("Generating simulated biogas sensor data...")
    df = simulator.generate_dataframe(duration_minutes=10, interval_seconds=5)
    
    # Plot key sensor variables
    fig = plot_sensor_data(df=df, 
                          sensor_columns=['temp_degC', 'flow', 'concentration_ch4'],
                          title="Simulated Biogas Sensor")
    plt.show()


def example_custom_plotting():
    """Example of custom plotting scenarios."""
    print("=== Custom Plotting Example ===")
    
    # Create data with color mapping
    simulator = BiogasSensorSimulator()
    df = simulator.generate_dataframe(duration_minutes=15, interval_seconds=10)
    
    # Custom plot with color mapping
    print("Plotting flow vs temperature with pressure coloring...")
    fig = quick_plot(df, 
                    x='temp_degC', 
                    y='flow', 
                    color='d0_pressure',
                    title="Flow vs Temperature (colored by pressure)")
    plt.show()


def example_live_plotting():
    """Example of live plotting (requires manual interruption)."""
    print("=== Live Plotting Example ===")
    
    if not HAS_LIVE_PLOT:
        print("⚠ Live plotting not available.")
        return
    
    response = input("Run live plotting demo? (y/n): ")
    if response.lower() == 'y':
        print("Starting live plot (press Ctrl+C to stop)...")
        try:
            example_live_plot_basic()
        except KeyboardInterrupt:
            print("Stopped live plot")


def example_dashboard():
    """Example of running the dashboard."""
    print("=== Dashboard Example ===")
    
    # Check dashboard availability when needed
    try:
        from dashboard import run_dashboard
        dashboard_available = True
    except ImportError:
        dashboard_available = False
        print("⚠ Dashboard not available. Install with: pip install dash plotly")
        return
    
    response = input("Run dashboard? (y/n): ")
    if response.lower() == 'y':
        print("Starting dashboard at http://localhost:8050 (press Ctrl+C to stop)")
        try:
            run_dashboard()
        except KeyboardInterrupt:
            print("Dashboard stopped")


def run_all_examples():
    """Run all examples in sequence."""
    print("Dataviz Examples - Biogas Sensor Visualization")
    print("=" * 50)
    
    try:
        example_basic_plotting()
        example_sensor_data_simulation()
        example_custom_plotting()
        print("\n" + "=" * 50)
        print("Optional examples (require user input):")
        example_live_plotting()
        example_dashboard()
        
    except KeyboardInterrupt:
        print("\nExamples interrupted by user")
    except Exception as e:
        print(f"Error running examples: {e}")
    
    print("\nExamples completed!")


if __name__ == '__main__':
    run_all_examples()